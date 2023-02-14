import json

# Storing data in a list of dictionaries
data = [
    {
        "name": "JOHN",
        "age": "40"
    },

    {
        "name": "JSON",
        "age":"20"
    }
]

# Writing the data to a JSON file with indentation
with open("data.json", "w") as f:
    json.dump(data, f, indent=2)
