import time
from datetime import datetime

def convert_to_epoch(time_str):
    dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
    return int(dt.timestamp())

# time_str = "2022-12-25 12:30:00"
# epoch_time = convert_to_epoch(time_str)
# print("The Unix timestamp for", time_str, "is:", epoch_time)

current_time = int(round(time.time()))
print("The current time in Unix timestamp format is:", current_time)
