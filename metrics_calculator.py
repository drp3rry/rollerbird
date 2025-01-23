# metrics_calculator.py

# Globals for total calculations
total_distance = 0  # in meters
total_time = 0  # in seconds
speed_buffer = []  # Buffer to track 30-second speeds
MAX_BUFFER_SIZE = 30  # Assuming 1 update per second


# metrics_calculator.py

def process_cadence_data(cadence, revolutions):
    """Process cadence and revolutions to update metrics."""
    global total_distance, total_time, speed_buffer

    elapsed_time = 1  # Assume 1 second intervals for simplicity

    # Update metrics using the calculator functions
    results = update_metrics(
        cadence=cadence,
        elapsed_time=elapsed_time,
        wheel_circumference=2.1,  # Replace with config value
        gear_ratio=3.33  # Replace with config value
    )

    # Print results for debugging
    print(f"Metrics Updated: {results}")



# Calculate speed
def calculate_speed(cadence, wheel_circumference, gear_ratio):
    """Calculate the speed in meters per second."""
    return cadence * wheel_circumference * gear_ratio / 60  # Cadence is in RPM

# Calculate total distance
def calculate_distance(revolutions, wheel_circumference):
    """Calculate the distance in meters."""
    return revolutions * wheel_circumference

# Calculate total average speed
def calculate_total_average_speed(total_distance, total_time):
    """Calculate the total average speed (m/s)."""
    return total_distance / total_time if total_time > 0 else 0

# Calculate 30-second average speed
def calculate_30s_average_speed(speed_buffer):
    """Calculate the 30-second average speed."""
    return sum(speed_buffer) / len(speed_buffer) if speed_buffer else 0

# Update metrics
def update_metrics(cadence, elapsed_time, wheel_circumference, gear_ratio):
    """Update all relevant metrics based on cadence and elapsed time."""
    global total_distance, total_time, speed_buffer

    # Calculate current speed
    current_speed = calculate_speed(cadence, wheel_circumference, gear_ratio)

    # Update total distance and time
    total_distance += current_speed * elapsed_time
    total_time += elapsed_time

    # Manage speed buffer
    speed_buffer.append(current_speed)
    if len(speed_buffer) > MAX_BUFFER_SIZE:
        speed_buffer.pop(0)

    # Calculate averages
    total_avg_speed = calculate_total_average_speed(total_distance, total_time)
    avg_30s_speed = calculate_30s_average_speed(speed_buffer)

    return {
        "current_speed": current_speed,
        "total_distance": total_distance,
        "total_avg_speed": total_avg_speed,
        "avg_30s_speed": avg_30s_speed,
    }
