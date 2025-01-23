import os
import asyncio
import time
import csv
import yaml
from math import ceil
from datetime import datetime
from bleak import BleakClient, BleakScanner

# Load configuration
def load_config(config_file="config.yaml"):
    with open(config_file, "r") as file:
        return yaml.safe_load(file)

config = load_config()
CADENCE_UUID = config["cadence_uuid"]
WHEEL_CIRCUMFERENCE = config["wheel_circumference"]
GEAR_RATIO = config["gear_ratio"]

# bluetooth handler
# Find Sensor
async def find_sensor():
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
async def connect_to_sensor():
    """Attempt to connect to the sensor and start tracking."""
    print("[INFO] Attempting to find sensor...")
    address = await find_sensor()
    if not address:
        print("[ERROR] No sensor found. Please ensure the sensor is active and try again.")
        return

    print(f"[INFO] Connecting to sensor at {address}...")
    try:
        async with BleakClient(address) as client:
            print("[INFO] Connected to sensor. Starting tracking...")
            await client.start_notify(CADENCE_UUID, handle_data)
            print("[INFO] Notifications started. Tracking data.")
            await display_data()  # Start tracking and displaying data
    except Exception as e:
        print(f"[ERROR] Exception during BLE connection or data streaming: {e}")

# Handle incoming data
def handle_data(sender, data):
    """Process the incoming BLE data."""
    print(f"[DATA] Received data from {sender}: {data}")
    # Add logic to process cadence, speed, etc.

# Example display function
async def display_data():
    """Dummy display function to simulate tracking."""
    for _ in range(10):  # Simulate displaying data 10 times
        print("[INFO] Displaying data...")
        await asyncio.sleep(1)
