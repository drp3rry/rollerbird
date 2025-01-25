import asyncio
import time
from collections import deque
import yaml

async def calculate_metrics(cadence_queue, metrics_queue, shutdown_event, config):
    """Calculate speed, distance, and averages."""
    # Config values
    WHEEL_CIRCUMFERENCE = config["wheel_circumference"]  # in meters
    GEAR_RATIO = config["chainring"] / config["cog"]  # adjust based on your gear setup

    # Metrics state
    state = {
        "live_speed": 0,
        "live_RPM": 0,
        "total_distance": 0,
        "average_speed": 0,
        # "last_speeds": deque(maxlen=30),  # Store the last 30 seconds of speeds
        "live_speeds": deque(maxlen=config["terminal_width"]),
        "last_revolutions" : None,
        "last_time": None,
        "active_time": 0,
        "intervals": deque(maxlen=config["terminal_width"])
    }

    interval_start_time = None
    interval_distance = 0

    while not shutdown_event.is_set():
        try:
            data = await asyncio.wait_for(cadence_queue.get(), timeout=1)
            cadence = data["cadence"]
            revolutions = data["revolutions"]
            current_time = time.time()

            if state["last_time"] is None:
                state["last_time"] = current_time
                interval_start_time = current_time
                state["last_revolutions"] = revolutions
                continue

            time_diff = current_time - state["last_time"]
            revolutions_diff = revolutions - state["last_revolutions"]
            distance_increment = revolutions_diff * GEAR_RATIO * WHEEL_CIRCUMFERENCE / 1000  # km
            state["total_distance"] += distance_increment
            interval_distance += distance_increment

            state["live_speed"] = (cadence / 60) * GEAR_RATIO * WHEEL_CIRCUMFERENCE * 3.6  # km/h

            if cadence > 0:
                state["active_time"] += time_diff

            state["live_speeds"].append(state["live_speed"] if cadence > 0 else 0)


            state["average_speed"] = state["total_distance"] / (state["active_time"] / 3600) if state["active_time"] > 0 else 0

            # interval_speed = (
            #     sum(list(state["live_speeds"])[-30:]) / min(30, len(state["live_speeds"]))
            # ) if state["live_speeds"] else 0
            # 
            interval_speed = 0

            interval_time = current_time - interval_start_time
            if interval_time >= 30:  # every 30 seconds
                interval_speed = (interval_distance / (interval_time / 3600)) if interval_time > 0 else 0
                state["intervals"].append({
                    "avg_speed": interval_speed,
                    "distance": interval_distance,
                })
                interval_start_time = current_time
                interval_distance = 0

            if current_time - interval_start_time >= 30:  # every 30 seconds
                state["intervals"].append({
                    "avg_speed": interval_speed,
                    "distance": interval_distance
                })
                interval_start_time = current_time
                interval_distance = 0

            state["last_time"] = current_time
            state["last_revolutions"] = revolutions

            # push metrics to the metrics_queue
            await metrics_queue.put({
                "live_RPM": cadence,
                "live_speed": state["live_speed"],
                "interval_speed": interval_speed,
                "average_speed": state["average_speed"],
                "total_distance": state["total_distance"],
                "intervals": list(state["intervals"]),
                "live_speeds": list(state["live_speeds"]),
                "active_time": state["active_time"]
            })

        except asyncio.TimeoutError:
            # no cadence data received in the last second
            pass
