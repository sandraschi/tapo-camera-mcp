# Tapo Camera Authentication Status

**Date**: November 29, 2025  
**Status**: ✅ WORKING via ONVIF (pytapo still failing)

## Summary

**RESOLVED**: Both cameras now work via ONVIF protocol!

| Protocol | Status |
|----------|--------|
| pytapo 3.3.53 | ❌ "Invalid authentication data" |
| ONVIF | ✅ **Fully working** |

## ONVIF Solution

ONVIF provides full camera access without pytapo authentication issues:
- ✅ Device info and status
- ✅ RTSP stream URL (`rtsp://host:554/stream1`)
- ✅ Snapshot capture (via RTSP frame grab)
- ✅ PTZ control (pan, tilt, zoom)
- ✅ Media profiles (mainStream, minorStream, jpegStream)

### Configuration (config.yaml)
```yaml
cameras:
  kitchen_cam:
    type: onvif
    params:
      host: 192.168.0.164
      onvif_port: 2020
      username: sandraschi
      password: Sec1000kitchen
```

## Legacy pytapo Status (Still Failing)

Both cameras fail authentication with pytapo library, even with:
- ✅ Correct Camera Account credentials (verified in app)
- ✅ Third-Party Compatibility enabled (global setting)
- ✅ pytapo updated to latest version (3.3.53)
- ✅ Camera online (port 443 reachable)
- ✅ Credentials verified multiple times

## Current Configuration

### Kitchen Camera (192.168.0.164)
- Device Name: Kitchencam
- Username: sandraschi
- Password: Sec1000kitchen
- Status: Authentication failing

### Living Room Camera (192.168.0.206)
- Username: sandraschi
- Password: Sec1000living
- Static IP: Enabled
- Status: Authentication failing

## Attempted Solutions

1. ✅ Updated pytapo (3.3.49 → 3.3.51) - Still failing
2. ✅ Enabled Third-Party Compatibility - Still failing
3. ✅ Verified credentials multiple times - Still failing
4. 🔄 Testing ONVIF authentication (alternative protocol)

## Possible Causes

### 1. pytapo Library Issue
- Library may have compatibility issues with C200 firmware
- Authentication method may not match what C200 expects
- May need different initialization or connection method

### 2. Camera Firmware
- Firmware version may not be compatible with current pytapo
- May need firmware update in Tapo app
- Some firmware versions changed authentication

### 3. Missing Setting
- There may be another setting needed in Tapo app
- ONVIF might need to be enabled separately
- API access might need explicit enabling

### 4. Authentication Method Mismatch
- C200 might require different authentication flow
- Camera Account might work differently than expected
- May need to use ONVIF instead of Tapo API

## Next Steps

1. **Test ONVIF Authentication** (if library installed)
   - Alternative protocol some Tapo cameras support
   - Uses different authentication method
   - May work where pytapo fails

2. **Check pytapo GitHub Issues**
   - Search for C200 authentication issues
   - Check for known compatibility problems
   - Look for workarounds or fixes

3. **Try Alternative Library**
   - Look for other Tapo camera Python libraries
   - May have better C200 support
   - Home Assistant integration might have working code

4. **Contact TP-Link Support**
   - Report authentication issue with API access
   - Ask about C200 API compatibility
   - Request official API documentation

## Alternative Approaches

### Option 1: Use Home Assistant Integration
- Home Assistant has working Tapo integration
- Could use their codebase as reference
- May have already solved this issue

### Option 2: Direct HTTP API Calls
- Bypass pytapo and use raw HTTP
- May have better control over authentication
- Can debug exact requests/responses

### Option 3: RTSP Streaming Only
- Skip API control features
- Use RTSP for video streaming
- Control via Tapo app only

## Current Status

**Blocked**: Cannot authenticate to cameras using pytapo library despite:
- Correct credentials
- Third-Party Compatibility enabled
- Latest pytapo version
- Both cameras set up identically

**Next Action**: Test ONVIF authentication or investigate pytapo/C200 compatibility issue.

