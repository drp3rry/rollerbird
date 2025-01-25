import os
from datetime import datetime
import csv
import asyncio

def generate_csv_file_name():
    """generate a unique file name for logging workouts."""
    directory = "workouts"
    if not os.path.exists(directory):
        os.makedirs(directory)

    base_name = f"workout_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv"
    file_path = os.path.join(directory, base_name)
    return file_path


def batch_write_to_csv(file_path, data, fieldnames):
    """write a batch of data to the csv file."""
    if not data:
        return  # no new data to write

    with open(file_path, mode="a", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if os.stat(file_path).st_size == 0:  # write header if file is empty
            writer.writeheader()
        writer.writerows(data)

    print(f"[INFO] Batch written to {file_path}")


async def logger(metrics_queue, shutdown_event):
    """consume data from metrics_queue and write to a csv file."""
    csv_file_path = generate_csv_file_name()
    fieldnames = ["time", "cadence", "speed", "distance", "average_speed"]
    log_batch = []  # temporary buffer for storing data
    batch_interval = 30  # write every 30 seconds
    last_written_time = datetime.now()

    while not shutdown_event.is_set():
        try:
            # get the latest data from the queue
            metrics = await asyncio.wait_for(metrics_queue.get(), timeout=1)

            # add timestamped metrics to the log batch
            log_batch.append({
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "cadence": metrics["live_RPM"],
                "speed": metrics["live_speed"],
                "distance": metrics["total_distance"],
                "average_speed": metrics["average_speed"],
            })

            # check if the batch interval has elapsed
            now = datetime.now()
            if (now - last_written_time).total_seconds() >= batch_interval:
                batch_write_to_csv(csv_file_path, log_batch, fieldnames)
                log_batch = []  # reset the batch
                last_written_time = now

        except asyncio.TimeoutError:
            pass