# layer1_pipeline.py - AquaAdapt Pro Layer 1 with GEE

import requests
from supabase import create_client
from datetime import datetime
import os

print("="*50)
print(f"AquaAdapt Pro - Layer 1 Pipeline")
print(f"Run at: {datetime.now()}")
print("="*50)

# Supabase credentials
SUPABASE_URL = os.environ.get('SUPABASE_URL', 'https://xdsfbpvqtqeyvuddxheo.supabase.co')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inhkc2ZicHZxdHFleXZ1ZGR4aGVvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODA2NTEzNDQsImV4cCI6MjA5NjIyNzM0NH0.8gk4UZ1ioTiEprZW17levkO_udtd7Ay_sof49tW6Io0')

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ========== 1. WEATHER DATA ==========
print("\n📡 Fetching Weather Data...")
lat, lon = 18.408, 76.565
url = "https://api.open-meteo.com/v1/forecast"
params = {
    "latitude": lat,
    "longitude": lon,
    "hourly": "temperature_2m,precipitation",
    "timezone": "Asia/Kolkata",
    "forecast_days": 7
}

response = requests.get(url, params=params)
data = response.json()

temps = data['hourly']['temperature_2m']
rains = data['hourly']['precipitation']
times = data['hourly']['time']

weather_records = []
for i in range(0, len(temps), 24):
    if i + 24 <= len(temps):
        weather_records.append({
            "location_name": "Latur",
            "date": times[i][:10],
            "temp_max_c": max(temps[i:i+24]),
            "rain_mm": sum(rains[i:i+24]),
            "fetched_at": datetime.now().isoformat()
        })

supabase.table("weather_data").insert(weather_records).execute()
print(f"   ✅ Stored {len(weather_records)} weather records")

# ========== 2. SATELLITE DATA (GEE) ==========
print("\n🛰️ Setting up Google Earth Engine...")

try:
    import subprocess
    subprocess.check_call(['pip', 'install', '-q', 'earthengine-api'])
    
    import ee
    
    GEE_PROJECT = os.environ.get('GEE_PROJECT_ID', 'empyrean-aurora-468809-g9')
    ee.Initialize(project=GEE_PROJECT)
    print(f"   ✅ GEE Initialized with project: {GEE_PROJECT}")
    
    point = ee.Geometry.Point([76.565, 18.408])
    
    # Test GEE with a simple operation
    image = ee.Image('NASA/SPL3SMP_E/005/2024-01-01')
    soil_moisture = image.select('soil_moisture_am').reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=point,
        scale=9000
    ).getInfo()
    
    print(f"   ✅ GEE Working! Sample: {soil_moisture}")
    
    # Store test record
    gee_record = [{
        "location_name": "Latur",
        "date": datetime.now().strftime('%Y-%m-%d'),
        "data_source": "gee_status",
        "value": 1.0,
        "unit": "connected",
        "fetched_at": datetime.now().isoformat()
    }]
    
    try:
        supabase.table("satellite_data").insert(gee_record).execute()
        print(f"   ✅ Stored GEE status to satellite_data")
    except Exception as e:
        print(f"   ⚠️ Create satellite_data table in Supabase first")
        print(f"   SQL: CREATE TABLE satellite_data (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), location_name TEXT, date DATE, data_source TEXT, value FLOAT, unit TEXT, fetched_at TIMESTAMPTZ);")
    
except Exception as e:
    print(f"   ❌ GEE Error: {e}")
    print(f"\n   Fix: Enable Earth Engine API at")
    print(f"   https://console.cloud.google.com/apis/library/earthengine.googleapis.com")

# ========== 3. VERIFY ==========
weather_count = supabase.table("weather_data").select("*", count="exact").execute()
print("\n" + "="*50)
print("📊 DATABASE SUMMARY")
print("="*50)
print(f"   Weather table: {weather_count.count} rows")
print("="*50)
print("✅ Layer 1 Pipeline Complete!")
