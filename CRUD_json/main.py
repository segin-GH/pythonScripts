import json

# Storing data in a list of dictionaries

data = {

    "MSTR": {
        "isConnected": False,
        "DEV1": "PDB"
    },

    "SLV1": {
        "isConnected": False,
        "DEV1": "CAS1",
        "DEV2": "CAS2"
    },

    "SLV2": {
        "isConnected": False,
        "DEV1": "CAS3",
        "DEV2": "CAS4"
    }
}

# Writing the data to a JSON file with indentation
with open("data.json", "w") as f:
    json.dump(data, f, indent=2)
