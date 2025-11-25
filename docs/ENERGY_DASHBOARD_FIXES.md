# Energy Dashboard Fixes - November 26, 2025

## Overview
Fixed three critical issues with the energy management dashboard that were preventing proper functionality.

## Issues Fixed

### 1. Tapo P115 Devices Not Displaying on Energy Page

**Problem**: Configured Tapo P115 smart plugs were not appearing on the energy management dashboard, even though they were working and discovered by the backend.

**Root Cause**: The `tapo_plug_manager` was not being initialized on web server startup, so devices weren't discovered until the first API call.

**Solution**: Added device initialization in the web server startup event handler.

**Files Changed**:
- `src/tapo_camera_mcp/web/server.py`
  - Added `tapo_plug_manager` initialization in `startup_event()`
  - Devices are now discovered when the server starts

**Code Changes**:
```python
# Initialize Tapo P115 plug manager to discover devices
try:
    from ..tools.energy.tapo_plug_tools import tapo_plug_manager
    logger.info("Initializing Tapo P115 plug manager on web server startup...")
    devices = await tapo_plug_manager.get_all_devices()
    logger.info(f"Tapo P115 plug manager initialized successfully - found {len(devices)} devices")
except Exception as e:
    logger.warning(f"Failed to initialize Tapo P115 plug manager: {e}")
```

---

### 2. Device Toggle On/Off Not Working

**Problem**: Clicking "Turn On" or "Turn Off" buttons on devices resulted in error: "error toggling device query turn on: field required".

**Root Cause**: FastAPI was not properly parsing the request body. The endpoint was using a dictionary parameter which FastAPI was trying to interpret as a query parameter instead of a request body.

**Solution**: Implemented a Pydantic model (`ToggleRequest`) for proper request body validation.

**Files Changed**:
- `src/tapo_camera_mcp/web/api/sensors.py`
  - Created `ToggleRequest` Pydantic model
  - Updated endpoint to use Pydantic model instead of raw dictionary
  - Added proper error handling and logging

**Code Changes**:
```python
class ToggleRequest(BaseModel):
    """Request model for toggling device power state."""
    turn_on: bool

@router.post("/tapo-p115/{device_id}/toggle")
async def toggle_tapo_p115(
    device_id: str,
    toggle_request: ToggleRequest,
) -> dict[str, Any]:
    turn_on = toggle_request.turn_on
    # ... rest of implementation
```

**Frontend Changes**:
- `src/tapo_camera_mcp/web/templates/energy.html`
  - Improved error handling in `toggleDevice()` function
  - Added detailed logging for debugging
  - Better error message extraction from FastAPI validation errors

---

### 3. Chart.js Not Loading - Energy Consumption Chart Error

**Problem**: Energy consumption chart displayed error: "error loading data: chart is not defined". Chart.js library was being blocked by Content Security Policy (CSP).

**Root Cause**: The CSP header was set to only allow scripts from `'self'`, blocking external CDN resources like Chart.js from `cdn.jsdelivr.net`.

**Solution**: Updated Content Security Policy to allow Chart.js and Font Awesome from their respective CDNs.

**Files Changed**:
- `src/tapo_camera_mcp/web/server.py`
  - Updated CSP header to allow scripts from `cdn.jsdelivr.net`
  - Updated CSP header to allow styles from `cdnjs.cloudflare.com`

**Code Changes**:
```python
response.headers["Content-Security-Policy"] = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
    "style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; "
    "img-src 'self' data:;"
)
```

**Frontend Changes**:
- `src/tapo_camera_mcp/web/templates/energy.html`
  - Added Chart.js loading checks in `loadChartData()` and `initChart()`
  - Added retry logic if Chart.js hasn't loaded yet
  - Improved error messages for Chart.js loading failures

---

## Testing

All fixes have been tested and verified:

1. ✅ **Device Display**: All 3 configured Tapo P115 devices (Aircon, Kitchen Zojirushi, Server) now appear on the energy page
2. ✅ **Toggle Functionality**: Device toggle on/off works correctly for non-read-only devices
3. ✅ **Energy Charts**: Chart.js loads successfully and energy consumption chart displays properly

## Impact

- **User Experience**: Energy dashboard is now fully functional
- **Reliability**: Devices are discovered on server startup, ensuring consistent availability
- **Security**: CSP updated to allow necessary CDN resources while maintaining security
- **Code Quality**: Proper request validation using Pydantic models

## Related Files

- `src/tapo_camera_mcp/web/server.py` - Server startup and CSP configuration
- `src/tapo_camera_mcp/web/api/sensors.py` - API endpoint with Pydantic validation
- `src/tapo_camera_mcp/web/templates/energy.html` - Frontend JavaScript and error handling
- `src/tapo_camera_mcp/tools/energy/tapo_plug_tools.py` - Device manager (no changes needed)

## Notes

- Server restart required after CSP changes
- All fixes are backward compatible
- No breaking changes to API or configuration

---

*Documentation created: November 26, 2025*

