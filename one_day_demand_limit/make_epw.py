import random
from datetime import datetime

# Create valid EPW weather file data for one day (e.g., July 7th)
def create_epw_file(filename="weather.epw", base_temp=30, fluctuation=5):
    with open(filename, 'w') as file:
        # EPW Header (example header information, adjust as needed)
        file.write("LOCATION,MN_MINNEAPOLIS-ST-PAUL-IAP,USA-MN,USA,TMYx,726580,45.00,-93.00,-6.0,265\n")
        file.write("DESIGN CONDITIONS,0\n")
        file.write("TYPICAL/EXTREME PERIODS,0\n")
        file.write("GROUND TEMPERATURES,0\n")
        file.write("HOLIDAYS/DAYLIGHT SAVINGS,No,0,0,0\n")
        file.write("COMMENTS 1,Created with random data for testing\n")
        file.write("COMMENTS 2,Generated by custom script\n")
        file.write("DATA PERIODS,1,1,Data,Sunday, 1/ 1, 12/31\n")

        # Generate data lines for each hour in a single day
        for hour in range(24):
            # Generate random temperature, keeping other fields constant for simplicity
            dry_bulb_temp = base_temp + random.uniform(-fluctuation, fluctuation)
            dew_point_temp = dry_bulb_temp - 3  # example adjustment
            relative_humidity = 50 + random.uniform(-10, 10)  # 50% RH with slight variation
            wind_speed = 3.5 + random.uniform(-1, 1)  # Wind speed with minor fluctuation
            wind_direction = 180  # Fixed wind direction

            # Format the line following EPW specifications (YYYY,MM,DD,HH,MM,WMO, ...)
            line = f"2024,7,7,{hour+1},60,726580,{dry_bulb_temp:.1f},{dew_point_temp:.1f},{relative_humidity:.0f},9999," \
                   f"9999,9999,9999,9999,{wind_speed:.1f},{wind_direction},0,0,0,0,0,0,0,0,0,0\n"
            file.write(line)

# Call function to create the EPW file
create_epw_file()
