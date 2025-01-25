import os
import asyncio
import time
import csv
import yaml
from math import ceil
from datetime import datetime
from bleak import BleakClient, BleakScanner

# # Load configuration
# def load_config(config_file="config.yaml"):
#     try:
#         with open(config_file, "r") as file:
#             return yaml.safe_load(file)
#     except FileNotFoundError:
#         print("[ERROR] Config file not found.")
#         raise
#     except yaml.YAMLError as e:
#         print(f"[ERROR] Failed to parse config: {e}")
#         raise

# config = load_config()
# CADENCE_UUID = config["cadence_uuid"]

# Globals to track data
prev_crank_event_time = None
prev_crank_revolutions = 0

# bluetooth handler
# Find Sensor
async def find_sensor(config):
    """Scan for devices for up to 60 seconds, waiting for the sensor to turn on."""
    print("[INFO] Scanning for devices...")

    retry_duration = config["scan_retry_duration"]  # Total retry duration in seconds
    scan_interval = config["scan_interval"]    # Duration of each scan attempt in seconds
    start_time = time.time()

    while time.time() - start_time < retry_duration:
        try:
            print(f"[INFO] Scanning for devices (up to {scan_interval} seconds)...")
            devices = await BleakScanner.discover(timeout=scan_interval)
            for device in devices:
                if "CAD" in (device.name or ""):  # Replace "CAD" with part of your sensor's name
                    print(f"[INFO] Sensor found: {device.name} ({device.address})")
                    return device.address
            print("[INFO] No matching sensor found. Retrying...")
        except Exception as e:
            print(f"[ERROR] Exception during scanning: {e}")

    print("[ERROR] Failed to find a matching sensor within 60 seconds.")
    return None

# Connect to BLE Sensor
async def connect_to_sensor(queue, shutdown_event, state, config):
    """Attempt to connect to the sensor and start tracking."""
    print("[INFO] Attempting to find sensor...")
    address = await find_sensor(config)

    if not address:
        print("[ERROR] No sensor found. Please ensure the sensor is active and try again.")
        return

    print(f"[INFO] Connecting to sensor at {address}...")
    try:
        async with BleakClient(address) as client:
            print("[INFO] Connected to sensor. Starting tracking...")
            await client.start_notify(config["cadence_uuid"], lambda _, data: asyncio.create_task(handle_data(data, queue, state)))
            print("[INFO] Notifications started. Listening for data...")

            # Wait for shutdown signal
            await shutdown_event.wait()
    except asyncio.CancelledError:
        print("[INFO] Sensor connection task canceled.")
    except Exception as e:
        print(f"[ERROR] Exception during BLE connection or data streaming: {e}")


# Handle incoming data
# Handle incoming data
async def handle_data(data, queue, state):
    """Process the incoming BLE data and push results to a queue."""
    # Parse data
    cumulative_crank_revolutions = int.from_bytes(data[1:3], byteorder="little")
    last_crank_event_time = int.from_bytes(data[3:5], byteorder="little")

    # Initialize state if not already present
    if "prev_crank_event_time" not in state:
        state["prev_crank_event_time"] = None
        state["prev_crank_revolutions"] = 0
        state["last_cadence"] = 0  # Store the last valid cadence
        state["last_movement_time"] = time.time()

    prev_crank_event_time = state["prev_crank_event_time"]
    prev_crank_revolutions = state["prev_crank_revolutions"]

    current_time = time.time()


    # Check for the first event (no previous data to compare with)
    if prev_crank_event_time is None:
        # Initialize the state and skip cadence calculation
        state["prev_crank_event_time"] = last_crank_event_time
        state["prev_crank_revolutions"] = cumulative_crank_revolutions
        state["last_movement_time"] = current_time
        await queue.put({"cadence": 0, "revolutions": cumulative_crank_revolutions})  # No cadence yet
        return

    # Ignore duplicate events (no time difference)
    if prev_crank_event_time == last_crank_event_time:
        state["last_movement_time"] = current_time
        await queue.put({"cadence": state["last_cadence"], "revolutions": cumulative_crank_revolutions})
        return

    # Calculate crank time difference
    crank_time_diff = (last_crank_event_time - prev_crank_event_time) / 1024  # seconds
    print(f"[DEBUG] Crank Time Diff: {crank_time_diff:.6f}, Prev Time: {prev_crank_event_time}, Last Time: {last_crank_event_time}")

    # Handle rollover
    if crank_time_diff < 0:
        crank_time_diff += 65536 / 1024

    # Calculate cadence if time difference is valid
    if crank_time_diff > 0:
        cadence = (cumulative_crank_revolutions - prev_crank_revolutions) / crank_time_diff * 60
    else:
        cadence = state["last_cadence"]  # Retain previous cadence if invalid time difference

    # Update state
    state["prev_crank_event_time"] = last_crank_event_time
    state["prev_crank_revolutions"] = cumulative_crank_revolutions
    state["last_cadence"] = cadence

    # Check if cadence should drop to zero
    if current_time - state["last_movement_time"] > 10:  # 10-second threshold
        print(f"[DEBUG] Cadence reset: {current_time - state['last_movement_time']:.2f}s since last movement")
        state["last_cadence"] = 0

    # Push the data into the queue
    await queue.put({"cadence": cadence, "revolutions": cumulative_crank_revolutions})

    # # Optional: Print data for debugging
    # print(f"[DATA] Cadence: {cadence:.2f} RPM, Revolutions: {cumulative_crank_revolutions}")


async def print_queue_updates(queue):
    while True:
        data = await queue.get()
        print(f"[DATA] Cadence: {data['cadence']:.2f} RPM, Revolutions: {data['revolutions']}")
        queue.task_done()

# Example display function
async def display_data():
    """Dummy display function to simulate tracking."""
    for _ in range(10):  # Simulate displaying data 10 times
        print("[INFO] Displaying data...")
        await asyncio.sleep(1)

# Placeholder for cadence processing in metrics calculator
def process_cadence_data(cadence):
    """Placeholder function to send cadence data to metrics calculator."""
    pass
