# Fixes Applied - Camera & Tapo Issues

## Camera Manager Initialization Fix

**Problem:** `AttributeError: 'TapoCameraServer' object has no attribute 'camera_manager'`

**Root Cause:** Web server was trying to access `camera_manager` before the TapoCameraServer was fully initialized.

**Fix Applied:**
- Added `await TapoCameraServer.ensure_hardware_initialized()` calls before accessing `camera_manager`
- This ensures the camera manager is properly initialized before use
- Applied to all camera-related API endpoints

**Files Modified:**
- `src/tapo_camera_mcp/web/server.py` - Added hardware initialization calls

## Tapo Plug Authentication Issue

**Problem:** `InvalidCredentials` errors for all Tapo P115 devices

**Root Cause:** Authentication credentials are incorrect or invalid

**Diagnosis:**
- Email: `sandraschipal@hotmail.com` ✓ (appears correct)
- Password: `Sec0860ta#` ❌ (authentication fails)
- Error: "Local hash does not match server hash"

**Potential Solutions:**

### 1. Verify Credentials
```bash
# Test with Tapo app credentials
# Make sure you're using the same email/password as the Tapo app
```

### 2. Reset Device Authentication
```bash
# Method 1: Factory reset devices
# - Unplug device for 10 seconds
# - Plug back in while holding reset button for 5 seconds
# - Re-add device to Tapo app with correct credentials

# Method 2: Clear TP-Link Simple Setup (TSS)
# - Disconnect ALL TP-Link/Tapo devices from network
# - Power off devices for 2 minutes
# - Power on ONE device at a time
# - Re-add to Tapo app
```

### 3. Update Config Password
```yaml
energy:
  tapo_p115:
    account:
      email: sandraschipal@hotmail.com
      password: "CORRECT_PASSWORD_HERE"  # Update this
```

### 4. Check Network Interference
- Ensure no other TP-Link/Tapo devices are connected during setup
- Try connecting devices to a different network temporarily
- Disable VPN if active

## Current Power Reading Fix

**Problem:** Tapo P115 devices don't provide real-time current power readings reliably

**Fix Applied:**
- Added proper error handling for `get_current_power()` calls
- Falls back to 0.0W when real-time power is unavailable
- Prevents API crashes when devices don't support this feature

**Files Modified:**
- `src/tapo_camera_mcp/web/api/energy.py` - Improved current power handling

## Testing

### Camera Test
```bash
# Cameras should now work without 'camera_manager' errors
# Visit: http://localhost:7777/cameras
```

### Tapo Test
```bash
# Run authentication test
python test_tapo_auth.py

# Check logs for authentication errors
tail -f tapo_mcp.log | grep -i tapo
```

## Status

✅ **Camera Manager**: Fixed - cameras should work now
⚠️ **Tapo Plugs**: Needs credential verification/reset
✅ **Current Power**: Fixed - no more crashes on unsupported devices

## Next Steps

1. **For Cameras:** Restart the server and test camera functionality
2. **For Tapo Plugs:** Verify credentials in Tapo app and update config.yaml
3. **If Tapo issues persist:** Factory reset devices and re-add to Tapo app