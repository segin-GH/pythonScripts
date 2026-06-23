import requests
import json

url = "https://archive.dozee.cloud/api/insights/lifecycle/query?datespan=UpdatedAt:2025-09-25T18:30:00Z...2025-09-26T18:30:00Z&filter=DeviceId:9d5f24f4-b5b5-41dd-80bd-d7e1cfdc4c45"

payload = {}
headers = {
    "Cookie": "AWSALB=e+xmHNwmZk/E/IMDM4MvYDm4xFcEkHys+4Dfuh0xndL7MMLJ3wtPcXzUG1yvQ8aJ3BmTcNcqKBd/BSpTWLROuEOCVxeyXZF8gIrdx4bjOXvUqQ+eK42+1i4xMSha; AWSALBCORS=e+xmHNwmZk/E/IMDM4MvYDm4xFcEkHys+4Dfuh0xndL7MMLJ3wtPcXzUG1yvQ8aJ3BmTcNcqKBd/BSpTWLROuEOCVxeyXZF8gIrdx4bjOXvUqQ+eK42+1i4xMSha",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3ODI3ODg3MzksImlhdCI6MTc1MTI1MjczOSwiaXNzIjoic2Vuc2xhYnMuaW8iLCJzdWIiOiJ7XCJBdXRoUm9sZVwiOlwiU0VOU1wiLFwiQ2F0ZWdvcnlcIjpcIk9QRVJBVE9SXCIsXCJNZWRpdW1cIjpcIkVtYWlsXCIsXCJNZWRpdW1WYWx1ZVwiOlwiYW1pdC5yZWRkeUBkb3plZS5pb1wifSJ9.UvUyvq0dNLtRFajlUYZhezoZJTp5-iX5cCJhVModzM0",
}

response = requests.request("GET", url, headers=headers, data=payload, timeout=30)

with open("device_lifecycle_response.json", "w") as f:

    f.write(json.dumps(response.json(), indent=4))


print(response.text)
