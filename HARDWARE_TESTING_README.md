# Hardware Connectivity Testing Suite

## Overview

The hardware connectivity testing suite ensures that ALL hardware devices can connect successfully before deploying the webapp. If hardware devices don't work, the webapp is useless.

## Critical vs Optional Systems

### CRITICAL SYSTEMS (Must Work)
These systems are essential for basic webapp functionality:

- Tapo Cameras - Core camera functionality
- Configuration - System configuration validation
- USB Camera Server - Windows camera proxy (if using USB cameras)

### OPTIONAL SYSTEMS (Nice to Have)
These systems add features but aren't critical:

- Philips Hue Lighting - Smart lighting control
- Tapo Smart Lighting - Additional lighting options
- Tapo Smart Plugs - Energy monitoring
- Netatmo Weather Station - Weather data
- Ring Doorbell - Security cameras

## Testing Scripts

### 1. Hardware Connectivity Verification
**File**: `verify_hardware_connectivity.py`

**Purpose**: Comprehensive verification of all hardware devices.

**Usage**:
```bash
python verify_hardware_connectivity.py
```

**Output Example**:
```
============================================================
HARDWARE CONNECTIVITY VERIFICATION
============================================================
Testing Hardware Configuration...     OK - Configuration loaded: 4 cameras configured
Testing USB Camera Server...          FAIL - USB camera server not running
Testing Tapo Cameras...               OK - 2 Tapo cameras connected
Testing Philips Hue Lighting...       OK - Hue: 18 lights, 6 groups, 52 scenes
Testing Tapo Smart Lighting...        SKIP - Tapo lighting not configured
Testing Tapo Smart Plugs...           FAIL - Tapo plugs connection failed
Testing Netatmo Weather Station...    OK - Netatmo: 1 stations, 2 modules
Testing Ring Doorbell...              FAIL - Ring connection failed

============================================================
HARDWARE CONNECTIVITY RESULTS
============================================================
OK Configuration     PASS   (CRITICAL)
FAIL USB Camera Server FAIL   (CRITICAL) - FIX REQUIRED
OK Tapo Cameras      PASS   (CRITICAL)
OK Philips Hue       PASS   (OPTIONAL)
- Tapo Lighting     SKIP   (OPTIONAL)
FAIL Tapo Plugs        FAIL   (OPTIONAL)
OK Netatmo Weather   PASS   (OPTIONAL)
FAIL Ring Doorbell     FAIL   (OPTIONAL)

SUMMARY:
- Critical Systems: 2/3 working
- Optional Systems: 2/5 working
- Total Systems:    4/8 working

CRITICAL SYSTEMS FAILURE
   Webapp will NOT be functional - fix critical issues first.
```

### 2. Hardware Test Runner
**File**: `run_hardware_tests.py`

**Purpose**: Flexible test runner with multiple options.

**Usage**:
```bash
# Run all hardware tests
python run_hardware_tests.py

# Only test critical systems
python run_hardware_tests.py --critical-only

# Skip slow optional tests
python run_hardware_tests.py --quick

# Use pytest for detailed testing
python run_hardware_tests.py --pytest --verbose

# Run verification script only
python run_hardware_tests.py --verify
```

### 3. Pytest Hardware Tests
**File**: `tests/test_hardware_connectivity.py`

**Purpose**: Detailed unit tests for hardware connectivity.

**Usage**:
```bash
# Run all hardware tests
pytest tests/test_hardware_connectivity.py -v

# Run only critical tests
pytest tests/test_hardware_connectivity.py -m critical -v

# Run connectivity tests
pytest tests/test_hardware_connectivity.py -m connectivity -v

# Run integration tests
pytest tests/test_hardware_connectivity.py -m integration -v
```

## Test Markers

The hardware tests use pytest markers for flexible test selection:

- `@pytest.mark.hardware` - All hardware-related tests
- `@pytest.mark.connectivity` - Device connectivity tests
- `@pytest.mark.critical` - Critical system tests (must pass)
- `@pytest.mark.optional` - Optional system tests (can be skipped)
- `@pytest.mark.integration` - Hardware-webapp integration tests

## Current Status (As of Testing)

Based on recent test runs:

### WORKING SYSTEMS
- **Tapo Cameras**: 2 cameras connected successfully
- **Philips Hue**: 18 lights, 6 groups, 52 scenes
- **Netatmo Weather**: 1 station, 2 modules
- **Configuration**: All config files valid

### FAILING SYSTEMS
- **USB Camera Server**: Not running (needs `python windows_camera_server.py`)
- **Tapo Smart Plugs**: Connection failed (403 Forbidden errors)
- **Ring Doorbell**: Authentication/configuration issues

### 🔄 Not Configured
- **Tapo Smart Lighting**: Not configured in system

## Troubleshooting Guide

### USB Camera Server Issues
```bash
# Start the USB camera server
python windows_camera_server.py

# Verify it's running
curl http://127.0.0.1:7778/status
```

### Tapo Device Issues
- Check device IP addresses in `config.yaml`
- Verify Tapo app credentials
- Ensure devices are on the same network
- Check firewall settings

### Ring Doorbell Issues
- Verify Ring account credentials in `config.yaml`
- Check 2FA setup
- Ensure Ring app is logged in

### Philips Hue Issues
- Verify bridge IP in `config.yaml`
- Press bridge button to authenticate
- Check Hue app connectivity

### Netatmo Issues
- Verify API credentials
- Check token cache files
- Ensure internet connectivity

## Integration with CI/CD

Add to your deployment pipeline:

```yaml
# GitHub Actions example
- name: Test Hardware Connectivity
  run: |
    python verify_hardware_connectivity.py
    if [ $? -ne 0 ]; then
      echo "Hardware connectivity tests failed!"
      exit 1
    fi

- name: Deploy Webapp
  run: |
    # Only deploy if hardware tests pass
    echo "All hardware systems working - safe to deploy"
```

## Development Workflow

1. **Before Development**: Run `python verify_hardware_connectivity.py`
2. **During Development**: Run `python run_hardware_tests.py --critical-only`
3. **Before Deployment**: Run full `python run_hardware_tests.py`
4. **CI/CD**: Include hardware tests in pipeline

## Test Results Interpretation

### Exit Codes
- `0`: All tests passed - webapp will be functional
- `1`: Critical tests failed - webapp will NOT be functional
- `2`: Optional tests failed but critical tests passed - webapp functional with reduced features

### Critical Failure Indicators
- Tapo cameras not connecting
- Configuration errors
- USB camera server not running (if using USB cameras)

### Optional Failure Indicators
- Lighting systems not working
- Weather station offline
- Security cameras unavailable

## Contributing

When adding new hardware support:

1. Add connectivity test in `test_hardware_connectivity.py`
2. Update verification script in `verify_hardware_connectivity.py`
3. Add appropriate pytest markers
4. Update this documentation
5. Test on actual hardware before merging

## Support

If hardware tests are failing:

1. Run `python verify_hardware_connectivity.py` for detailed diagnostics
2. Check device power and network connectivity
3. Verify configuration in `config.yaml`
4. Consult device-specific troubleshooting sections above
5. Check system logs for detailed error messages

**Remember**: Hardware connectivity is critical for webapp functionality. Never deploy without passing critical hardware tests!