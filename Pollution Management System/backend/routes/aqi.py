from flask import Blueprint, jsonify, request
from db import get_db_connection
import time

aqi_bp = Blueprint("aqi", __name__)

# Simple in-memory cache with TTL (5 minutes)
_aqi_cache = {}
_CACHE_TTL = 300  # 5 minutes in seconds

def get_cached(key):
    """Get value from cache if not expired"""
    if key in _aqi_cache:
        value, timestamp = _aqi_cache[key]
        if time.time() - timestamp < _CACHE_TTL:
            return value
        del _aqi_cache[key]
    return None

def set_cached(key, value):
    """Store value in cache with current timestamp"""
    _aqi_cache[key] = (value, time.time())

def get_aqi_category(aqi):
    if aqi <= 50:
        return {
            "category": "Good",
            "color": "Green",
            "health_message": "Air quality is good. Enjoy outdoor activities."
        }
    elif aqi <= 100:
        return {
            "category": "Satisfactory",
            "color": "Light Green",
            "health_message": "Minor breathing discomfort to sensitive people."
        }
    elif aqi <= 200:
        return {
            "category": "Moderate",
            "color": "Yellow",
            "health_message": "Breathing discomfort to people with lung disease."
        }
    elif aqi <= 300:
        return {
            "category": "Poor",
            "color": "Orange",
            "health_message": "Breathing discomfort to most people on prolonged exposure."
        }
    elif aqi <= 400:
        return {
            "category": "Very Poor",
            "color": "Red",
            "health_message": "Respiratory illness on prolonged exposure."
        }
    else:
        return {
            "category": "Severe",
            "color": "Dark Red",
            "health_message": "Serious health impacts. Avoid outdoor activities."
        }

@aqi_bp.route("/aqi", methods=["GET"])

def get_aqi():
    location_id = request.args.get("location_id")

    if not location_id:
        return jsonify({"message": "location_id is required"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
        SELECT l.name, a.pm25, a.pm10, a.aqi, a.recorded_at
        FROM aqi_readings a
        JOIN locations l ON a.location_id = l.location_id
        WHERE a.location_id = %s
        ORDER BY a.recorded_at DESC
        LIMIT 1
        """
        cursor.execute(query, (location_id,))
        data = cursor.fetchone()

        cursor.close()
        conn.close()

        if not data:
            return jsonify({"message": "No AQI data found"}), 404

        severity = get_aqi_category(data["aqi"])
        data.update(severity)
        
        return jsonify(data), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@aqi_bp.route("/aqi/all", methods=["GET"])
def get_all_aqi():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
        SELECT 
            l.name AS location_name,
            l.latitude,
            l.longitude,
            a.aqi,
            a.pm25,
            a.pm10,
            a.recorded_at
        FROM aqi_readings a
        LEFT JOIN locations l ON a.location_id = l.location_id
        WHERE a.recorded_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
        ORDER BY a.recorded_at DESC
        """

        cursor.execute(query)
        rows = cursor.fetchall()

        result = []
        seen_locations = set()
        
        for r in rows:
            # Only include the most recent reading per location
            if r["location_name"] not in seen_locations:
                severity = get_aqi_category(r["aqi"])
                r.update(severity)
                result.append(r)
                seen_locations.add(r["location_name"])

        cursor.close()
        conn.close()

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def calculate_aqi_pm25(pm25):
    if pm25 <= 30:
        return 50
    elif pm25 <= 60:
        return 100
    elif pm25 <= 90:
        return 200
    elif pm25 <= 120:
        return 300
    else:
        return 400


@aqi_bp.route("/aqi/current", methods=["GET"])
def current_location_aqi():
    lat = request.args.get("lat")
    lng = request.args.get("lng")

    if not lat or not lng:
        return jsonify({"message": "lat and lng are required"}), 400

    try:
        lat = float(lat)
        lng = float(lng)
    except ValueError:
        return jsonify({"message": "Invalid coordinates"}), 400

    # Round coordinates for cache key (to 2 decimal places ~1km precision)
    cache_key = f"aqi_{round(lat, 2)}_{round(lng, 2)}"
    cached_result = get_cached(cache_key)
    if cached_result:
        print(f"✅ Cache hit for {cache_key}")
        return jsonify(cached_result), 200

    import requests
    import math
    from urllib.parse import quote
    from datetime import datetime, timezone

    # Helper function to calculate distance using Haversine formula
    def haversine_distance(lat1, lon1, lat2, lon2):
        R = 6371  # Earth's radius in kilometers
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c

    def parse_iso_datetime(value):
        if not value:
            return None
        try:
            # Handle Z suffix
            value = value.replace("Z", "+00:00")
            dt = datetime.fromisoformat(value)
            # If no timezone info, assume UTC
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except Exception:
            return None

    def age_hours(dt_value):
        if not dt_value:
            return None
        try:
            # Ensure both are timezone-aware
            now = datetime.now(timezone.utc)
            if dt_value.tzinfo is None:
                dt_value = dt_value.replace(tzinfo=timezone.utc)
            return round((now - dt_value).total_seconds() / 3600, 2)
        except Exception:
            return None

    def cpcb_subindex(conc, breakpoints):
        if conc is None:
            return None
        for c_low, c_high, i_low, i_high in breakpoints:
            if c_low <= conc <= c_high:
                return round((i_high - i_low) / (c_high - c_low) * (conc - c_low) + i_low)
        if conc > breakpoints[-1][1]:
            return 500
        return None

    def calculate_aqi_cpcb(pm25_value, pm10_value):
        pm25_bp = [
            (0, 30, 0, 50),
            (31, 60, 51, 100),
            (61, 90, 101, 200),
            (91, 120, 201, 300),
            (121, 250, 301, 400),
            (251, 999, 401, 500)
        ]
        pm10_bp = [
            (0, 50, 0, 50),
            (51, 100, 51, 100),
            (101, 250, 101, 200),
            (251, 350, 201, 300),
            (351, 430, 301, 400),
            (431, 999, 401, 500)
        ]

        subindices = []
        pm25_index = cpcb_subindex(pm25_value, pm25_bp)
        pm10_index = cpcb_subindex(pm10_value, pm10_bp)
        if pm25_index is not None:
            subindices.append(pm25_index)
        if pm10_index is not None:
            subindices.append(pm10_index)

        if not subindices:
            return None
        return max(subindices)

    # Allow data up to 5 years old (43800 hours) - will be marked as stale in UI
    MAX_DATA_AGE_HOURS = 43800

    def reverse_geocode_city(lat_val, lng_val):
        try:
            res = requests.get(
                "https://nominatim.openstreetmap.org/reverse",
                params={
                    "format": "json",
                    "lat": lat_val,
                    "lon": lng_val,
                    "zoom": 10,
                    "addressdetails": 1
                },
                headers={"User-Agent": "Pollution-Management-System/1.0"},
                timeout=3
            )
            if res.status_code == 200:
                addr = res.json().get("address", {})
                city = addr.get("city") or addr.get("town") or addr.get("village") or addr.get("county")
                state = addr.get("state")
                return city, state
        except Exception as e:
            print(f"Reverse geocode error: {e}")
        return None, None

    waqi_result = None
    waqi_stale_candidate = None
    openaq_result = None
    openaq_stale_candidate = None

    try:
        # 1️⃣ Try WAQI (World Air Quality Index) API first - More reliable
        # Note: This requires an API key - get free key from https://aqicn.org/api/
        WAQI_API_KEY = "752f88867cdc07ae8736875beb47539dbdc3c544"
        waqi_url = f"https://api.waqi.info/feed/geo:{lat};{lng}/?token={WAQI_API_KEY}"
        waqi_response = requests.get(waqi_url, timeout=5)
        if waqi_response.status_code == 200:
            waqi_data = waqi_response.json()
            if waqi_data.get("status") == "ok":
                aqi_value = waqi_data["data"]["aqi"]
                pm25 = waqi_data["data"].get("iaqi", {}).get("pm25", {}).get("v")
                pm10 = waqi_data["data"].get("iaqi", {}).get("pm10", {}).get("v")
                station_name = waqi_data["data"].get("city", {}).get("name")
                waqi_time = waqi_data["data"].get("time", {}).get("s")
                waqi_dt = parse_iso_datetime(waqi_time)
                waqi_age = age_hours(waqi_dt)
                aqi_cpcb = calculate_aqi_cpcb(pm25, pm10)
                aqi_display = aqi_cpcb if aqi_cpcb is not None else aqi_value

                if waqi_age is not None and waqi_age > MAX_DATA_AGE_HOURS:
                    print(f"❌ WAQI data too old ({waqi_age}h), marking as stale")
                    if aqi_display is not None:
                        waqi_stale_candidate = {
                            "aqi": aqi_display,
                            "aqi_raw": aqi_value,
                            "aqi_cpcb": aqi_cpcb,
                            "pm25": pm25,
                            "pm10": pm10,
                            "category": get_aqi_category(aqi_display)["category"],
                            "health_message": get_aqi_category(aqi_display)["health_message"],
                            "station_name": station_name,
                            "timestamp_utc": waqi_time,
                            "age_hours": waqi_age,
                            "is_stale": True,
                            "source": "WAQI"
                        }
                else:
                    # Validate station is actually near the requested location
                    station_geo = waqi_data["data"].get("city", {}).get("geo", [])
                    station_lat = station_geo[0] if len(station_geo) > 0 else 0
                    station_lng = station_geo[1] if len(station_geo) > 1 else 0

                    if station_lat and station_lng:
                        distance = haversine_distance(lat, lng, station_lat, station_lng)
                        print(f"WAQI Station Distance: {distance:.2f}km - {station_name}")

                        # Only use this station if it's within 100km (otherwise WAQI returned wrong station)
                        if distance < 100:
                            severity = get_aqi_category(aqi_display)
                            waqi_result = {
                                "aqi": aqi_display,
                                "aqi_raw": aqi_value,
                                "aqi_cpcb": aqi_cpcb,
                                "pm25": pm25,
                                "pm10": pm10,
                                "category": severity["category"],
                                "health_message": severity["health_message"],
                                "station_name": station_name,
                                "station_distance_km": round(distance, 1),
                                "timestamp_utc": waqi_time,
                                "age_hours": waqi_age,
                                "source": "WAQI"
                            }
                            print(f"✅ WAQI station validated: {station_name}")
                        else:
                            print(f"❌ WAQI returned distant station ({distance:.0f}km away), rejecting")
                    else:
                        # No coordinates in response, accept anyway (old API format)
                        severity = get_aqi_category(aqi_display)
                        waqi_result = {
                            "aqi": aqi_display,
                            "aqi_raw": aqi_value,
                            "aqi_cpcb": aqi_cpcb,
                            "pm25": pm25,
                            "pm10": pm10,
                            "category": severity["category"],
                            "health_message": severity["health_message"],
                            "station_name": station_name,
                            "timestamp_utc": waqi_time,
                            "age_hours": waqi_age,
                            "source": "WAQI"
                        }

        # Fallback: if WAQI geo lookup fails or returns a distant station, try city-based lookup
        if not waqi_result:
            city, state = reverse_geocode_city(lat, lng)
            if city:
                candidates = []
                if state:
                    candidates.append(f"{city}, {state}")
                candidates.append(city)

                for candidate in candidates:
                    city_query = quote(candidate)
                    city_url = f"https://api.waqi.info/feed/{city_query}/?token={WAQI_API_KEY}"
                    city_res = requests.get(city_url, timeout=3)
                    if city_res.status_code != 200:
                        continue

                    city_data = city_res.json()
                    if city_data.get("status") != "ok":
                        continue

                    aqi_value = city_data["data"].get("aqi")
                    pm25 = city_data["data"].get("iaqi", {}).get("pm25", {}).get("v")
                    pm10 = city_data["data"].get("iaqi", {}).get("pm10", {}).get("v")
                    station_name = city_data["data"].get("city", {}).get("name") or candidate
                    waqi_time = city_data["data"].get("time", {}).get("s")
                    waqi_dt = parse_iso_datetime(waqi_time)
                    waqi_age = age_hours(waqi_dt)

                    if waqi_age is not None and waqi_age > MAX_DATA_AGE_HOURS:
                        print(f"❌ WAQI city data too old ({waqi_age}h), marking as stale")
                        if waqi_stale_candidate is None:
                            # Calculate CPCB AQI for stale data
                            city_aqi_cpcb = calculate_aqi_cpcb(pm25, pm10)
                            city_aqi_display = city_aqi_cpcb if city_aqi_cpcb is not None else aqi_value
                            if city_aqi_display is not None:
                                waqi_stale_candidate = {
                                    "aqi": city_aqi_display,
                                    "aqi_raw": aqi_value,
                                    "aqi_cpcb": city_aqi_cpcb,
                                    "pm25": pm25,
                                    "pm10": pm10,
                                    "category": get_aqi_category(city_aqi_display)["category"],
                                    "health_message": get_aqi_category(city_aqi_display)["health_message"],
                                    "station_name": station_name,
                                    "timestamp_utc": waqi_time,
                                    "age_hours": waqi_age,
                                    "is_stale": True,
                                    "source": "WAQI"
                                }
                        continue

                    aqi_cpcb = calculate_aqi_cpcb(pm25, pm10)
                    aqi_display = aqi_cpcb if aqi_cpcb is not None else aqi_value
                    if aqi_display is None:
                        continue

                    severity = get_aqi_category(aqi_display)
                    waqi_result = {
                        "aqi": aqi_display,
                        "aqi_raw": aqi_value,
                        "aqi_cpcb": aqi_cpcb,
                        "pm25": pm25,
                        "pm10": pm10,
                        "category": severity["category"],
                        "health_message": severity["health_message"],
                        "station_name": station_name,
                        "timestamp_utc": waqi_time,
                        "age_hours": waqi_age,
                        "source": "WAQI"
                    }
                    print(f"✅ WAQI city fallback used: {station_name}")
                    break

                if not waqi_result and waqi_stale_candidate:
                    waqi_result = waqi_stale_candidate

        # 2️⃣ Try OpenAQ API V3 (requires free API key)
        # Get your free key at: https://explore.openaq.org/register
        # V2 API is retired - V3 requires API key in X-API-Key header
        OPENAQ_API_KEY = "4b9b3eba3cb638c58565c3f9767b3b68deffa9286ffbda634e27dae6793c8767" # Add your OpenAQ API key here (free at https://explore.openaq.org/register)
        
        if OPENAQ_API_KEY:
            openaq_url = "https://api.openaq.org/v3/locations"
            openaq_params = {
                "coordinates": f"{lat},{lng}",
                "radius": 25000,  # 25km radius in meters (OpenAQ v3 max)
                "limit": 3,  # Only check 3 nearest locations for speed
                "parameters_id": 2  # PM2.5
            }
            openaq_headers = {
                "User-Agent": "Pollution-Management-System/1.0",
                "X-API-Key": OPENAQ_API_KEY
            }

            openaq_res = requests.get(openaq_url, params=openaq_params, headers=openaq_headers, timeout=5)
            print(f"OpenAQ V3 Response Status: {openaq_res.status_code}")

            if openaq_res.status_code == 200:
                openaq_data = openaq_res.json()
                locations = openaq_data.get("results", [])
                print(f"OpenAQ V3 Results Found: {len(locations)}")

                # Sort by actual distance to ensure nearest station is used
                def location_distance_km(loc):
                    coords = loc.get("coordinates", {})
                    loc_lat = coords.get("latitude")
                    loc_lng = coords.get("longitude")
                    if loc_lat is None or loc_lng is None:
                        return float("inf")
                    return haversine_distance(lat, lng, loc_lat, loc_lng)

                locations = sorted(locations, key=location_distance_km)

                # Build sensor->parameter mapping from location's sensors array
                # This avoids making individual API calls for each sensor
                def build_sensor_map(loc):
                    sensor_map = {}
                    for sensor in loc.get("sensors", []):
                        sensor_id = sensor.get("id")
                        param = sensor.get("parameter", {})
                        param_name = param.get("name") if isinstance(param, dict) else None
                        if sensor_id and param_name:
                            sensor_map[sensor_id] = param_name
                    return sensor_map

                # Try to get latest measurement for each location
                for location in locations:
                    location_id = location.get("id")
                    location_name = location.get("name", "OpenAQ Station")
                    sensor_map = build_sensor_map(location)
                    
                    # Fetch latest measurements for this location
                    measurements_url = f"https://api.openaq.org/v3/locations/{location_id}/latest"
                    try:
                        meas_res = requests.get(measurements_url, headers=openaq_headers, timeout=3)
                        print(f"OpenAQ latest status for {location_name}: {meas_res.status_code}")
                        
                        if meas_res.status_code == 200:
                            meas_data = meas_res.json()
                            results = meas_data.get("results", [])
                            print(f"OpenAQ measurements found: {len(results)}")
                            
                            # Resolve PM2.5/PM10 using sensor map (no API calls needed)
                            pm25_value = None
                            pm10_value = None
                            best_time = None
                            best_age = None
                            stale_pm25 = None
                            stale_pm10 = None
                            stale_time = None
                            stale_age = None

                            for result in results:
                                value = result.get("value")
                                if value is None or value <= 0 or value >= 500:
                                    continue

                                sensor_id = result.get("sensorsId")
                                parameter = sensor_map.get(sensor_id)  # Use local map, no API call

                                if parameter not in ("pm25", "pm10", None):
                                    continue

                                ts = result.get("datetime", {}).get("utc")
                                dt_value = parse_iso_datetime(ts)
                                age = age_hours(dt_value)
                                if age is not None and age > MAX_DATA_AGE_HOURS:
                                    if stale_age is None or age < stale_age:
                                        stale_age = age
                                        stale_time = dt_value
                                        if parameter == "pm10":
                                            stale_pm10 = value
                                        else:
                                            stale_pm25 = value
                                    continue

                                if best_time is None or (dt_value and dt_value > best_time):
                                    best_time = dt_value
                                    best_age = age

                                if parameter == "pm10":
                                    pm10_value = value
                                else:
                                    pm25_value = value

                            if pm25_value is not None or pm10_value is not None:
                                aqi = calculate_aqi_cpcb(pm25_value, pm10_value)
                                if aqi is None:
                                    continue
                                severity = get_aqi_category(aqi)
                                station_distance = location_distance_km(location)

                                print(f"OpenAQ V3 Data Found: Station={location_name}, PM2.5={pm25_value}, PM10={pm10_value}, AQI={aqi}")

                                openaq_result = {
                                    "aqi": aqi,
                                    "aqi_cpcb": aqi,
                                    "pm25": pm25_value,
                                    "pm10": pm10_value,
                                    "category": severity["category"],
                                    "health_message": severity["health_message"],
                                    "station_name": location_name,
                                    "station_distance_km": round(station_distance, 1) if station_distance != float("inf") else None,
                                    "timestamp_utc": best_time.isoformat() if best_time else None,
                                    "age_hours": best_age,
                                    "source": "OpenAQ"
                                }
                                break
                            elif stale_pm25 is not None or stale_pm10 is not None:
                                aqi_stale = calculate_aqi_cpcb(stale_pm25, stale_pm10)
                                if aqi_stale is None:
                                    continue
                                if openaq_stale_candidate is None:
                                    severity = get_aqi_category(aqi_stale)
                                    station_distance = location_distance_km(location)
                                    openaq_stale_candidate = {
                                        "aqi": aqi_stale,
                                        "aqi_cpcb": aqi_stale,
                                        "pm25": stale_pm25,
                                        "pm10": stale_pm10,
                                        "category": severity["category"],
                                        "health_message": severity["health_message"],
                                        "station_name": location_name,
                                        "station_distance_km": round(station_distance, 1) if station_distance != float("inf") else None,
                                        "timestamp_utc": stale_time.isoformat() if stale_time else None,
                                        "age_hours": stale_age,
                                        "is_stale": True,
                                        "source": "OpenAQ"
                                    }
                    except Exception as e:
                        print(f"OpenAQ measurement fetch error: {e}")
                        continue
                
                if not openaq_result:
                    print(f"OpenAQ V3: No valid PM2.5 data found in {len(locations)} locations")
                    if openaq_stale_candidate:
                        print("OpenAQ V3: Using stale data fallback")
                        openaq_result = openaq_stale_candidate
            elif openaq_res.status_code == 401:
                print("OpenAQ V3: Unauthorized - API key required or invalid")
        else:
            print("OpenAQ V3: Skipped - No API key configured. Get free key at https://explore.openaq.org/register")

    except Exception as e:
        print(f"External API Error: {str(e)}")
        print(f"WAQI Result: {'Available' if waqi_result else 'None'}")
        print(f"OpenAQ Result: {'Available' if openaq_result else 'None'}")
        # Continue to fallback

    # Final stale data fallback - use stale data if no fresh data available
    if not waqi_result and waqi_stale_candidate:
        print("Using WAQI stale data as final fallback")
        waqi_result = waqi_stale_candidate
    if not openaq_result and openaq_stale_candidate:
        print("Using OpenAQ stale data as final fallback")
        openaq_result = openaq_stale_candidate

    if waqi_result or openaq_result:
        primary = waqi_result or openaq_result
        station_name = primary.get("station_name")
        source_label = primary.get("source")
        source_text = f"{source_label} - {station_name}" if station_name else source_label

        result = {
            "aqi": primary.get("aqi"),
            "pm25": primary.get("pm25"),
            "pm10": primary.get("pm10"),
            "category": primary.get("category"),
            "health_message": primary.get("health_message"),
            "source": source_text,
            "station_name": station_name,
            "primary_source": primary.get("source"),
            "waqi": waqi_result,
            "openaq": openaq_result
        }
        # Cache the result
        set_cached(cache_key, result)
        return jsonify(result), 200

    # 2️⃣ Fallback to nearest database location
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Get all locations with recent AQI readings
        query = """
        SELECT 
            l.location_id,
            l.name,
            l.latitude,
            l.longitude,
            a.aqi,
            a.pm25,
            a.pm10,
            a.recorded_at
        FROM locations l
        JOIN aqi_readings a ON l.location_id = a.location_id
        WHERE l.latitude IS NOT NULL 
        AND l.longitude IS NOT NULL
        AND a.recorded_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
        ORDER BY a.recorded_at DESC
        """
        
        cursor.execute(query)
        locations = cursor.fetchall()
        
        cursor.close()
        conn.close()

        if not locations:
            return jsonify({
                "aqi": None,
                "category": "Data Unavailable",
                "health_message": "No AQI data available for your area",
                "source": "System",
                "primary_source": "database",
                "waqi": None,
                "openaq": None
            }), 200

        # Find the nearest location
        nearest_location = None
        min_distance = float('inf')

        for location in locations:
            distance = haversine_distance(
                lat, lng,
                float(location['latitude']),
                float(location['longitude'])
            )
            
            if distance < min_distance:
                min_distance = distance
                nearest_location = location

        if nearest_location:
            severity = get_aqi_category(nearest_location['aqi'])
            
            return jsonify({
                "aqi": nearest_location['aqi'],
                "pm25": float(nearest_location['pm25']) if nearest_location['pm25'] else None,
                "pm10": float(nearest_location['pm10']) if nearest_location['pm10'] else None,
                "category": severity["category"],
                "health_message": severity["health_message"],
                "source": f"⚠️ TEST DATA - Nearest Station: {nearest_location['name']} ({min_distance:.1f} km away)",
                "location_name": nearest_location['name'],
                "distance_km": round(min_distance, 1),
                "is_test_data": True,
                "primary_source": "database",
                "waqi": None,
                "openaq": None
            }), 200

        return jsonify({
            "aqi": None,
            "category": "Data Unavailable",
            "health_message": "No nearby AQI data available",
            "source": "System",
            "primary_source": "database",
            "waqi": None,
            "openaq": None
        }), 200

    except Exception as e:
        print(f"Database Error: {str(e)}")
        return jsonify({
            "aqi": None,
            "category": "Error",
            "health_message": "Failed to fetch AQI data",
            "source": "System",
            "error": str(e),
            "primary_source": "database",
            "waqi": None,
            "openaq": None
        }), 500

def fetch_city_aqi(city):
    import requests

    url = "https://api.openaq.org/v2/latest"
    params = {
        "country": "IN",        # 🔑 IMPORTANT
        "city": city,
        "parameter": "pm25",
        "limit": 1
    }
    headers = {
        "User-Agent": "Pollution-Management-System/1.0"
    }

    res = requests.get(url, params=params, headers=headers, timeout=5)
    data = res.json()

    results = data.get("results", [])
    if not results:
        return None

    measurements = results[0].get("measurements", [])
    if not measurements:
        return None

    return measurements[0]["value"]


# Test endpoint to populate sample AQI data
@aqi_bp.route("/aqi/populate-test-data", methods=["POST"])
def populate_test_data():
    """Populate sample AQI data for all locations for testing purposes"""
    import random
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Get all locations
        cursor.execute("SELECT location_id, name FROM locations")
        locations = cursor.fetchall()

        if not locations:
            return jsonify({"message": "No locations found in database"}), 404

        inserted_count = 0
        for location in locations:
            # Generate random but realistic PM2.5 values
            pm25 = random.randint(15, 150)
            pm10 = pm25 * random.uniform(1.5, 2.0)
            aqi = calculate_aqi_pm25(pm25)

            insert_query = """
            INSERT INTO aqi_readings (location_id, pm25, pm10, aqi)
            VALUES (%s, %s, %s, %s)
            """
            cursor.execute(insert_query, (location['location_id'], pm25, pm10, aqi))
            inserted_count += 1

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            "message": "Test AQI data populated successfully",
            "locations_updated": inserted_count
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
