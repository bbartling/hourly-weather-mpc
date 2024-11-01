import matplotlib.pyplot as plt
import matplotlib.dates as mdates  # For formatting dates on the x-axis
from pathlib import Path
from time import sleep
import random
from datetime import timedelta, datetime
from energyplus_api_helpers.import_helper import EPlusAPIHelper

class RunConfig:
    def __init__(self):
        self.e = EPlusAPIHelper(Path('C:/EnergyPlusV24-1-0'))
        self.idf_name = Path.cwd() / '5ZoneAirCooled.idf'  # IDF in current directory
        self.api = self.e.get_api_instance()
        self.got_handles = False
        self.oa_temp_handle = -1
        self.zone_temp_handles = {}
        self.zone_temperatures = {}
        self.count = 0
        self.outdoor_data = []
        self.start_simulation_datetime = datetime(2024, 7, 7, 0, 0)  # Simulation start date
        self.zone_names = {
            'south': 'SPACE1-1', 'west': 'SPACE2-1', 'east': 'SPACE3-1',
            'north': 'SPACE4-1', 'center': 'SPACE5-1'
        }

runner = RunConfig()

# Plot setup for multiple zones and outdoor temperature
fig, ax = plt.subplots(len(runner.zone_names) + 1, 1, figsize=(10, 12))

# Outdoor Air Temperature Plot (without date formatting)
outdoor_line, = ax[0].plot([], [], label="Outdoor Air Temp", color='orange')
ax[0].set_title('Outdoor Air Temperature')
ax[0].set_ylabel('Temperature [°C]')
ax[0].legend(loc='lower right')

# Zone Temperature Plots (without date formatting)
zone_lines = {}
for i, (zone_name, _) in enumerate(runner.zone_names.items(), start=1):
    line, = ax[i].plot([], [], label=f"{zone_name.capitalize()} Zone Temp", color='blue')
    ax[i].set_title(f'{zone_name.capitalize()} Zone Air Temperature')
    ax[i].set_ylabel('Temperature [°C]')
    ax[i].legend(loc='lower right')
    zone_lines[zone_name] = line

# Apply date formatting only to the bottom plot
ax[-1].xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
ax[-1].xaxis.set_major_locator(mdates.HourLocator(interval=1))
ax[-1].xaxis.set_minor_locator(mdates.MinuteLocator(interval=15))
ax[-1].set_xlabel("Time")
ax[-1].tick_params(axis='x', rotation=45)  # Rotate labels for readability

# Update the plot with new data
def update_plot():
    outdoor_x = [data['x'] for data in runner.outdoor_data]
    outdoor_y = [data['y'] for data in runner.outdoor_data]
    outdoor_line.set_xdata(outdoor_x)
    outdoor_line.set_ydata(outdoor_y)
    ax[0].relim()
    ax[0].autoscale_view()

    for i, zone_name in enumerate(runner.zone_names):
        zone_data = runner.zone_temperatures.get(zone_name, [])
        zone_x = [data['x'] for data in zone_data]
        zone_y = [data['y'] for data in zone_data]
        zone_lines[zone_name].set_xdata(zone_x)
        zone_lines[zone_name].set_ydata(zone_y)
        ax[i + 1].relim()
        ax[i + 1].autoscale_view()

    plt.pause(0.01)  # Pause to update plot in real-time

# Callback function to handle the EnergyPlus simulation
def callback_function(s):
    if not runner.got_handles:
        if not runner.api.exchange.api_data_fully_ready(s):
            return
        runner.oa_temp_handle = runner.api.exchange.get_variable_handle(
            s, "Site Outdoor Air DryBulb Temperature", "Environment"
        )
        for zone_nickname, zone_name in runner.zone_names.items():
            runner.zone_temp_handles[zone_nickname] = runner.api.exchange.get_variable_handle(
                s, "Zone Mean Air Temperature", zone_name
            )
        if -1 in [runner.oa_temp_handle] + list(runner.zone_temp_handles.values()):
            runner.api.runtime.issue_severe("Invalid Handle in API usage, need to fix!")
        runner.got_handles = True

    if runner.api.exchange.warmup_flag(s):
        return

    runner.count += 1
    current_time_hours = runner.api.exchange.current_sim_time(s)
    current_sim_time = runner.start_simulation_datetime + timedelta(hours=current_time_hours)

    # Print current simulation time details
    print(f"current_time_hours: {current_time_hours}")
    print(f"current_sim_time: {current_sim_time}")
    print(f"Timestep: {runner.count}")

    # Generate a random outdoor air temperature between 10°C and 35°C
    eplus_outdoor_temp = random.uniform(-10.0, 3.0)
    eplus_outdoor_temp = 15.0
    runner.api.exchange.set_actuator_value(s, runner.oa_temp_handle, eplus_outdoor_temp)

    # Collect outdoor temperature data
    oa_temp = runner.api.exchange.get_variable_value(s, runner.oa_temp_handle)
    runner.outdoor_data.append({'x': current_sim_time, 'y': oa_temp})

    # Collect zone temperature data for each zone
    for zone_nickname, handle in runner.zone_temp_handles.items():
        zone_temp = runner.api.exchange.get_variable_value(s, handle)
        if zone_nickname not in runner.zone_temperatures:
            runner.zone_temperatures[zone_nickname] = []
        runner.zone_temperatures[zone_nickname].append({'x': current_sim_time, 'y': zone_temp})

    update_plot()
    print(f"-----------------------------------------")

# Function to run the EnergyPlus simulation
def run_simulation():
    state = runner.api.state_manager.new_state()
    runner.api.exchange.request_variable(state, "Site Outdoor Air DryBulb Temperature", "Environment")
    for zone_name in runner.zone_names.values():
        runner.api.exchange.request_variable(state, "Zone Mean Air Temperature", zone_name)

    # Register callback function to handle simulation data
    runner.api.runtime.callback_begin_zone_timestep_after_init_heat_balance(state, callback_function)
    
    # Run EnergyPlus simulation with the specified IDF file
    runner.api.runtime.run_energyplus(
        state, [
            '-d',
            runner.e.get_temp_run_dir(),
            '-w',
            runner.e.weather_file_path(),
            str(runner.idf_name)
        ]
    )

if __name__ == "__main__":
    run_simulation()
    plt.show()  # Show the plot at the end of the simulation
