import time
from datetime import datetime

# def convert_to_epoch(time_str):
#     dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
#     return int(dt.timestamp())

# # time_str = "2022-12-25 12:30:00"
# # epoch_time = convert_to_epoch(time_str)
# # print("The Unix timestamp for", time_str, "is:", epoch_time)

# current_time = int(round(time.time()))
# print("The current time in Unix timestamp format is:", current_time)

# current_epoch_time = int(time.time())
# print(current_epoch_time)


import time
import datetime

current_epoch_time = int(time.time())

# Convert epoch time to datetime object
dt_object = datetime.datetime.fromtimestamp(current_epoch_time)

# Convert epoch time to seconds
epoch_seconds = current_epoch_time % 60

print("Datetime object:", dt_object)
print("Epoch seconds:", epoch_seconds)
