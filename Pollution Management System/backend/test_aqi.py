"""
Quick test script to populate sample AQI data and test the current location endpoint
"""
import requests
import json

BASE_URL = "http://127.0.0.1:5000"

print("=" * 60)
print("TESTING AQI IMPLEMENTATION")
print("=" * 60)

# Step 1: Populate test data
print("\n1. Populating test AQI data for all locations...")
try:
    response = requests.post(f"{BASE_URL}/aqi/populate-test-data")
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Success: {data['message']}")
        print(f"  Locations updated: {data['locations_updated']}")
    else:
        print(f"✗ Failed: {response.text}")
except Exception as e:
    print(f"✗ Error: {str(e)}")

# Step 2: Test current location AQI (using Delhi coordinates as example)
print("\n2. Testing current location AQI (Delhi coordinates)...")
test_coords = {
    "lat": 28.6139,
    "lng": 77.2090
}

try:
    response = requests.get(f"{BASE_URL}/aqi/current", params=test_coords)
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Success!")
        print(f"  AQI: {data.get('aqi')}")
        print(f"  Category: {data.get('category')}")
        print(f"  Health Message: {data.get('health_message')}")
        print(f"  Source: {data.get('source')}")
        if 'distance_km' in data:
            print(f"  Distance: {data.get('distance_km')} km")
    else:
        print(f"✗ Failed: {response.text}")
except Exception as e:
    print(f"✗ Error: {str(e)}")

# Step 3: Test with a different location (Mumbai)
print("\n3. Testing with Mumbai coordinates...")
test_coords2 = {
    "lat": 19.0760,
    "lng": 72.8777
}

try:
    response = requests.get(f"{BASE_URL}/aqi/current", params=test_coords2)
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Success!")
        print(f"  AQI: {data.get('aqi')}")
        print(f"  Category: {data.get('category')}")
        print(f"  Source: {data.get('source')}")
        if 'distance_km' in data:
            print(f"  Distance: {data.get('distance_km')} km")
    else:
        print(f"✗ Failed: {response.text}")
except Exception as e:
    print(f"✗ Error: {str(e)}")

# Step 4: Get all AQI readings
print("\n4. Testing /aqi/all endpoint...")
try:
    response = requests.get(f"{BASE_URL}/aqi/all")
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Success! Found {len(data)} locations with AQI data")
        for location in data[:3]:  # Show first 3
            print(f"  - {location['location_name']}: AQI {location['aqi']} ({location['category']})")
    else:
        print(f"✗ Failed: {response.text}")
except Exception as e:
    print(f"✗ Error: {str(e)}")

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
