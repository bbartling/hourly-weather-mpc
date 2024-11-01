import matplotlib.pyplot as plt
import matplotlib.dates as mdates  # For formatting dates on the x-axis
from pathlib import Path
from time import sleep
import random
from datetime import timedelta, datetime
from energyplus_api_helpers.import_helper import EPlusAPIHelper

e = EPlusAPIHelper(Path('C:/EnergyPlusV24-1-0'))
api = e.get_api_instance()

got_handles = False
oa_temp_actuator = -1
oa_temp_handle = -1
zone_temp_handle = -1
start_simulation_datetime = datetime(2024, 1, 1, 0, 0)  # Simulation start date and time
outdoor_data = []
zone_temp_data = []

# Plot setup
fig, ax = plt.subplots(2, 1, figsize=(10, 8))

# Outdoor Air Temperature Plot (Top Plot)
outdoor_line, = ax[0].plot([], [], label="Outdoor Air Temp", color='orange')
ax[0].set_title('Outdoor Air Temperature')
ax[0].set_ylabel('Temperature [°C]')
ax[0].legend(loc='lower right')

# Zone Temperature Plot (Bottom Plot with Date/Time)
zone_line, = ax[1].plot([], [], label="Zone Temperature", color='blue')
ax[1].set_title('Zone Air Temperature')
ax[1].set_xlabel('Time')  # We will display actual time on this plot
ax[1].set_ylabel('Temperature [°C]')
ax[1].legend(loc='lower right')

# Apply the date-time formatting only to the bottom plot
ax[1].xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
ax[1].xaxis.set_major_locator(mdates.HourLocator(interval=1))  # Show every hour on x-axis
ax[1].xaxis.set_minor_locator(mdates.MinuteLocator(interval=15))  # Minor ticks at 15-minute intervals
ax[1].tick_params(axis='x', rotation=45)  # Rotate labels for readability

# Update the plot with new data
def update_plot():
    outdoor_x = [data['x'] for data in outdoor_data]
    outdoor_y = [data['y'] for data in outdoor_data]
    zone_x = [data['x'] for data in zone_temp_data]
    zone_y = [data['y'] for data in zone_temp_data]

    # Update top plot (Outdoor Air Temperature)
    outdoor_line.set_xdata(outdoor_x)
    outdoor_line.set_ydata(outdoor_y)
    ax[0].relim()
    ax[0].autoscale_view()

    # Update bottom plot (Zone Temperature)
    zone_line.set_xdata(zone_x)
    zone_line.set_ydata(zone_y)
    ax[1].relim()
    ax[1].autoscale_view()

    plt.pause(0.01)  # Pause to update plot in real-time

# Callback function to handle the EnergyPlus simulation
def callback_function(s):
    global got_handles, oa_temp_actuator, oa_temp_handle, zone_temp_handle

    if not got_handles:
        if not api.exchange.api_data_fully_ready(s):
            return
        oa_temp_actuator = api.exchange.get_actuator_handle(s, "Weather Data", "Outdoor Dry Bulb", "Environment")
        oa_temp_handle = api.exchange.get_variable_handle(s, "Site Outdoor Air DryBulb Temperature", "Environment")
        zone_temp_handle = api.exchange.get_variable_handle(s, "Zone Mean Air Temperature", 'Zone One')

        if -1 in [oa_temp_actuator, oa_temp_handle, zone_temp_handle]:
            print("***Invalid handles, check spelling and sensor/actuator availability")
            return
        got_handles = True

    if api.exchange.warmup_flag(s):
        return

    # Get the current simulation time in hours
    current_time_hours = api.exchange.current_sim_time(s)
    print(f"current_time_hours: {current_time_hours}")
    
    # Convert fractional hours to a datetime object
    current_sim_time = start_simulation_datetime + timedelta(hours=current_time_hours)
    print(f"current_sim_time: {current_sim_time}")

    # Print the simulation time and timestep
    print(f"Timestep: {len(outdoor_data) + 1}")

    # Generate a random outdoor air temperature between a range (e.g., 10°C to 35°C)
    eplus_outdoor_temp = random.uniform(10.0, 35.0)

    # Set actuator value for outdoor temperature
    api.exchange.set_actuator_value(s, oa_temp_actuator, eplus_outdoor_temp)

    # Collect outdoor and zone temperature data
    oa_temp = api.exchange.get_variable_value(s, oa_temp_handle)
    outdoor_data.append({'x': current_sim_time, 'y': oa_temp})

    zone_temp = api.exchange.get_variable_value(s, zone_temp_handle)
    zone_temp_data.append({'x': current_sim_time, 'y': zone_temp})

    # Update the plot
    update_plot()

    print(f"-----------------------------------------")

# Function to run the EnergyPlus simulation
def run_simulation():
    global api, outdoor_data, zone_temp_data
    outdoor_data = []
    zone_temp_data = []

    state = api.state_manager.new_state()
    api.exchange.request_variable(state, "Site Outdoor Air DryBulb Temperature", "Environment")
    api.exchange.request_variable(state, "Zone Mean Air Temperature", 'Zone One')

    # Register callback function to handle simulation data
    api.runtime.callback_begin_zone_timestep_after_init_heat_balance(state, callback_function)
    
    # Run EnergyPlus simulation
    api.runtime.run_energyplus(
        state, [
            '-d',
            e.get_temp_run_dir(),
            '-w',
            e.weather_file_path(),
            e.path_to_test_file(Path("C:/Users/bbartling/Desktop/EplusStuff/one_day_random_oat/1ZoneUncontrolled_.idf"))
        ]
    )

if __name__ == "__main__":
    run_simulation()
    plt.show()  # Show the plot at the end of the simulation
