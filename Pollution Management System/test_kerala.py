import requests
import json

# Test with Kerala coordinates
kerala_lat = 10.04673
kerala_lng = 76.32964

print(f"\n🌍 Testing Kerala coordinates: Lat={kerala_lat}, Lng={kerala_lng}\n")

try:
    url = f"http://127.0.0.1:5000/aqi/current?lat={kerala_lat}&lng={kerala_lng}"
    print(f"📡 URL: {url}\n")
    
    r = requests.get(url, timeout=10)
    data = r.json()
    
    print("✅ Response received!\n")
    print(f"Primary Source: {data.get('primary_source')}")
    print(f"\n📊 WAQI:")
    if data.get('waqi'):
        print(f"  Station: {data['waqi'].get('station_name')}")
        print(f"  AQI: {data['waqi'].get('aqi')}")
    else:
        print(f"  ❌ No nearby station (rejected or unavailable)")
    
    print(f"\n📊 OpenAQ:")
    if data.get('openaq'):
        print(f"  Station: {data['openaq'].get('station_name')}")
        print(f"  AQI: {data['openaq'].get('aqi')}")
    else:
        print(f"  ❌ No data available")
    
except Exception as e:
    print(f"❌ Error: {e}")
