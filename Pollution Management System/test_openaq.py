import requests
import json

apiKey = '4b9b3eba3cb638c58565c3f9767b3b68deffa9286ffbda634e27dae6793c8767'
headers = {'X-API-Key': apiKey}

# Get locations
print("=== Getting locations ===")
loc_res = requests.get('https://api.openaq.org/v3/locations?coordinates=28.6139,77.2090&radius=25000&limit=1', headers=headers)
locs = loc_res.json()['results']
print(f"Location: {locs[0]['name']}, ID: {locs[0]['id']}")

# Get latest measurements
print("\n=== Getting latest measurements ===")
meas_res = requests.get(f"https://api.openaq.org/v3/locations/{locs[0]['id']}/latest", headers=headers)
print(f"Status: {meas_res.status_code}")
print("Response:")
print(json.dumps(meas_res.json(), indent=2))
