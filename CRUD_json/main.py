import json

# Storing data in a list of dictionaries

# data = {
#     "MSTR": {
#         "isConnected": False,
#         "DEV1": "PDB"
#     },

#     "SLV1": {
#         "isConnected": False,
#         "DEV1": "CAS1",
#         "DEV2": "CAS2"
#     },

#     "SLV2": {
#         "isConnected": False,
#         "DEV1": "CAS3",
#         "DEV2": "CAS4"
#     }
# }

# # Writing the data to a JSON file with indentation
# with open("data.json", "w") as f:
#     json.dump(data, f, indent=2)


# with open('data.json', 'r') as f:
#     data = json.load(f)

# mstr = data["MSTR"]
# slv1 = data["SLV1"]
# slv2 = data["SLV2"]

# Printing the values
# print(mstr)
# print(slv1)
# print(slv2)

with open('setting.json','r') as f:
    data = json.load(f)


data["MSTR"]["isConnected"] = True
data["MSTR"]["timeStamp"] = 1676383622

data["SLV3"] = {
    "isConnected":True,
    "DEV1": "ACS",
    "DEV2": "FP"
}
data["totalDevices"] = 5

with open(".config.json", 'w') as f:
    json.dump(data, f, indent=2) 
