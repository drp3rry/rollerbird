import asyncio
import sys


# handles all terminal UI
def draw_plot(live_speed_history, speed_history, config):
    """draws the speed plot on the terminal."""
    terminal_width = config["terminal_width"]
    max_speed = config["max_speed"]
    y_interval = config["speed_interval"]  # each Y-axis line represents speed_interval km/h
    terminal_height = max_speed // y_interval

    # create a blank grid
    grid = [[" " for _ in range(terminal_width)] for _ in range(terminal_height)]

    # plot live speed stars over the bars
    for i, speed in enumerate(live_speed_history[-terminal_width:]):  # limit to terminal width
        x = i  # x-axis index
        y = terminal_height - 1 - min(terminal_height - 1, int(speed // y_interval))
        grid[y][x] = "\033[91m*\033[0m"  # red star for live speed

    # plot semi-transparent bars for average speed
    for i, avg_speed in enumerate(speed_history[-terminal_width:]):  # limit to terminal width
        x = i  # x-axis index
        bar_top = terminal_height - 1 - min(terminal_height - 1, int(avg_speed // y_interval))
        for y in range(terminal_height - 1, bar_top - 1, -1):  # fill bar down to the x-axis
            grid[y][x] = "\033[90m█\033[0m"  # semi-transparent bar

    # y-axis labels (speed)
    y_axis_labels = [f"{y_interval * i:2.0f}" for i in range(terminal_height)]

    # draw the y-axis title
    y_axis_title = "Speed (km/h)"
    print(f"{y_axis_title:<6}")

    # draw the plot with y-axis labels
    for row in range(terminal_height):
        speed_label = y_axis_labels[terminal_height - 1 - row]
        print(f"{speed_label:>4} |{''.join(grid[row])}")

    # x-axis line and labels
    x_axis = "     +" + "-" * (terminal_width - 5)  # x-axis line
    print(x_axis)  # draw the x-axis line

    # x-axis title (time)
    x_axis_title = "Time (red: 1s, white: 30s)"
    centered_title = f"{x_axis_title:^{terminal_width}}"
    print(centered_title)

def format_time(seconds):
    """Format time in seconds to HH:MM:SS."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"

def draw_metrics(metrics):
    """Display live metrics above the graph."""
    BRIGHT_RED = "\033[91m"
    RESET = "\033[0m"

    formatted_time = format_time(metrics.get("active_time", 0))  # format time as needed
    live_cadence = metrics.get("live_RPM", 0)
    live_speed = metrics.get("live_speed", 0)
    interval_speed = metrics.get("interval_speed", 0)
    avg_speed = metrics.get("average_speed", 0)
    distance = metrics.get("total_distance", 0)

    # Clear the terminal and print the metrics
    # sys.stdout.write("\033[H\033[J")  # Clear terminal screen
    print(f"Active Time:          {BRIGHT_RED}{formatted_time}{RESET}")
    print(f"Cadence:       {BRIGHT_RED}{live_cadence:6.1f} RPM{RESET}")
    print(f"Speed:         {BRIGHT_RED}{live_speed:6.1f} km/h{RESET}")
    print(f"30s Avg Speed: {BRIGHT_RED}{interval_speed:6.1f} km/h{RESET}")
    print(f"Total Avg Speed:{BRIGHT_RED}{avg_speed:6.1f} km/h{RESET}")
    print(f"Distance:      {BRIGHT_RED}{distance:7.2f} km{RESET}")
    print(" ")  # Blank line for spacing



async def terminal_display(metrics_queue, config, shutdown_event):
    """Periodically updates the terminal display with metrics and graph."""
    while not shutdown_event.is_set():
        try:
            # Get the latest metrics from the queue
            metrics = await asyncio.wait_for(metrics_queue.get(), timeout=1)

            # Clear the terminal ONCE
            sys.stdout.write("\033[H\033[J")  # Clear terminal and reset cursor position

            # Draw the metrics
            draw_metrics(metrics)

            # Draw the speed graph
            live_speed_history = metrics["live_speeds"]
            speed_history = [interval["avg_speed"] for interval in metrics["intervals"]]
            draw_plot(live_speed_history, speed_history, config)

        except asyncio.TimeoutError:
            pass
