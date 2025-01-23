# main entry point
from bluetooth_handler import connect_to_sensor, read_sensor_data
from data_logger import save_workout_log
from metrics_calculator import calculate_speed
from terminal_display import plot_data
from game_logic import generate_gate_sequence

def main():
    pass  # handle the workflow: connect, process data, gamify, display

if __name__ == "__main__":
    main()
