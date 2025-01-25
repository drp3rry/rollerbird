# main entry point
# from bluetooth_handler import connect_to_sensor, read_sensor_data
# from data_logger import save_workout_log
# from metrics_calculator import calculate_speed
# from terminal_display import plot_data
# from game_logic import generate_gate_sequence

import asyncio, yaml
from bluetooth_handler import connect_to_sensor, print_queue_updates
from metrics_calculator import calculate_metrics
from terminal_display import terminal_display

# Load configuration
def load_config(config_file="config.yaml"):
    try:
        with open(config_file, "r") as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        print("[ERROR] Config file not found.")
        raise
    except yaml.YAMLError as e:
        print(f"[ERROR] Failed to parse config: {e}")
        raise

async def display_metrics(metrics_queue, shutdown_event):
    """Display metrics from the metrics queue."""
    while not shutdown_event.is_set():
        try:
            metrics = await asyncio.wait_for(metrics_queue.get(), timeout=1)
            print(
                f"[METRICS] Live RPM: {metrics['live_RPM']:.2f} RPM, "
                f"Live Speed: {metrics['live_speed']:.2f} km/h, "
                f"Interval Speed: {metrics['interval_speed']:.2f} km/h, "
                f"Average Speed: {metrics['average_speed']:.2f} km/h, "
                f"Total Distance: {metrics['total_distance']:.2f} km"
            )
        except asyncio.TimeoutError:
            pass



async def main():
    config = load_config()
    bluetooth_queue = asyncio.Queue()
    metrics_queue = asyncio.Queue()
    shutdown_event = asyncio.Event()
    state = {}

    # Start the sensor connection and data printer
    sensor_task = asyncio.create_task(connect_to_sensor(bluetooth_queue, shutdown_event, state, config))
    metrics_task = asyncio.create_task(calculate_metrics(bluetooth_queue, metrics_queue, shutdown_event, config))
    display_task = asyncio.create_task(terminal_display(metrics_queue, config, shutdown_event))
    logging_task = asyncio.create_task(logger(metrics_queue, shutdown_event))
    # display_task = asyncio.create_task(display_metrics(metrics_queue, shutdown_event))
    # printer_task = asyncio.create_task(print_queue_updates(bluetooth_queue))

    try:
        await asyncio.gather(sensor_task, metrics_task, display_task)
    except KeyboardInterrupt:
        print("[INFO] Shutting down...")
        shutdown_event.set()
    finally:
        sensor_task.cancel()
        metrics_task.cancel()
        display_task.cancel()
        logging_task.cancel()
        # printer_task.cancel()

if __name__ == "__main__":
    asyncio.run(main())

