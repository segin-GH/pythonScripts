#! /usr/bin/python3


import sys
from datetime import datetime
import pytz

def convert_to_ist(timestamp):
    # Define the timezone for UTC and IST
    utc_zone = pytz.utc
    ist_zone = pytz.timezone('Asia/Kolkata')

    # Parse the timestamp string to a datetime object assuming the timestamp is in UTC
    utc_time = datetime.strptime(timestamp, '%d/%m/%y,%H:%M:%S+00')

    # Set the timezone for the datetime object to UTC
    utc_time = utc_zone.localize(utc_time)

    # Convert time to IST
    ist_time = utc_time.astimezone(ist_zone)

    # Return the converted time
    return ist_time.strftime('%d/%m/%Y, %H:%M:%S IST')

if __name__ == "__main__":
    # Check if a timestamp argument is provided
    if len(sys.argv) == 2:
        timestamp = sys.argv[1]
        try:
            ist_time = convert_to_ist(timestamp)
            print(f"Converted Time (IST): {ist_time}")
        except ValueError as e:
            print(f"Error converting timestamp: {e}")
    else:
        print("Usage: python script.py '<timestamp>'")
        print("Timestamp format should be: 'DD/MM/YY,HH:MM:SS+00'")

