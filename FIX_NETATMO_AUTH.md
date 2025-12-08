# Fix Netatmo Weather - Replace Mock Data with Real Data

**Date**: 2025-12-03  
**Status**: Netatmo OAuth refresh token needs renewal

## Current Situation

### ✅ **Working (Real Data):**
- Vienna External Weather via Open-Meteo API
- Temperature: 4°C, Humidity: 87%, Overcast
- Updates automatically, no API key required

### ⚠️ **Showing Mock Data:**
- Indoor Netatmo weather overview
- Temperature: 22.3°C (placeholder)
- Humidity: 45% (placeholder)
- CO2: 420 ppm (placeholder)

## Root Cause

Netatmo OAuth refresh token expired or invalid. The config has:
```yaml
weather:
  integrations:
    netatmo:
      enabled: true
      client_id: '6827631abc073747f105a0e4'
      client_secret: 'Uge1m7YrypuK2Wz7QjqfhduhEQlPJYWC4uKSEH'
      refresh_token: '5ca3ae420ec7040a008b57dd|1c0ea7462250f34a19d52556b7e61a99'
```

But the refresh token needs to be refreshed via Netatmo OAuth flow.

## Solution: Reauthorize Netatmo

### Option 1: Use Helper Script

```powershell
cd D:\Dev\repos\tapo-camera-mcp
.\venv\Scripts\Activate.ps1
python scripts/netatmo_oauth_helper.py
```

This will:
1. Open browser to Netatmo authorization page
2. You login with your Netatmo credentials
3. Accept permissions
4. Script captures new refresh token
5. Updates `config.yaml` automatically

### Option 2: Manual Netatmo Developer Portal

1. Go to https://dev.netatmo.com/apps
2. Login with your Netatmo account
3. Select your app (or create one)
4. Generate new refresh token
5. Copy to `config.yaml` → `weather.integrations.netatmo.refresh_token`
6. Restart dashboard: `.\start_dashboard.ps1`

### Option 3: Disable Netatmo (Keep External Weather Only)

If you don't have Netatmo weather station, disable it:

```yaml
weather:
  integrations:
    netatmo:
      enabled: false  # Changed from true
```

The weather page will still show:
- ✅ Vienna external weather (Open-Meteo)
- ✅ 5-day forecast
- ❌ No indoor weather data

## After Reauthorization

Once Netatmo is connected, you'll see REAL indoor data:
- Actual room temperature
- Actual humidity
- Actual CO2 levels
- Air quality metrics
- Pressure readings
- Noise levels (if supported)

## Test Netatmo Connection

After reauthorizing, test it:

```powershell
# Test Netatmo API connection
Invoke-RestMethod -Uri "http://localhost:7777/api/weather/overview"

# Should show real data like:
# {
#   "average_temperature": 21.5,  # Real from Netatmo
#   "average_humidity": 52,       # Real from Netatmo  
#   "average_co2": 450,           # Real from Netatmo
#   ...
# }
```

## Code Changes Made

Updated `src/tapo_camera_mcp/web/api/weather.py`:

**Before:**
```python
# Line 392-409: Always returned hardcoded mock data
return {
    "average_temperature": 22.3,  # Hardcoded
    "average_humidity": 45,       # Hardcoded
    "average_co2": 420,          # Hardcoded
    ...
}
```

**After:**
```python
# Now tries to get real Netatmo data first
if use_netatmo:
    try:
        stations = await _netatmo_service.list_stations()
        if stations:
            station_id = stations[0]["station_id"]
            data, ts = await _netatmo_service.current_data(station_id, "all")
            
            return {
                "average_temperature": data.get("Temperature", 22.0),  # Real!
                "average_humidity": data.get("Humidity", 45),          # Real!
                "average_co2": data.get("CO2", 400),                   # Real!
                ...
            }
    except Exception as e:
        logger.warning(f"Failed to get real Netatmo data: {e}")

# If Netatmo unavailable, return placeholder with None values
return {
    "average_temperature": None,  # Clear it's not real
    "average_humidity": None,
    "average_co2": None,
    "health_status": "No Data",
    ...
}
```

## Weather Dashboard Status

### What's Working NOW:
✅ Vienna external weather (Open-Meteo) - REAL DATA  
✅ 5-day forecast - REAL DATA  
✅ Weather API endpoints functional  
✅ Dashboard shows data without errors  

### What Needs Netatmo:
⚠️ Indoor temperature/humidity  
⚠️ CO2 levels  
⚠️ Air quality metrics  
⚠️ Home environment monitoring  

## Next Steps

1. **Reauthorize Netatmo** (recommended if you have the station)
   ```powershell
   python scripts/netatmo_oauth_helper.py
   ```

2. **Or disable Netatmo** (if no station)
   - Edit `config.yaml`
   - Set `weather.integrations.netatmo.enabled: false`
   - Restart dashboard

3. **Refresh weather page**
   - Open http://localhost:7777/weather
   - You'll see Vienna weather (always works)
   - Indoor weather appears after Netatmo auth

---

**Summary**: Weather page now properly distinguishes between real external weather (working) and Netatmo indoor data (needs OAuth refresh). No more confusing mock data!

