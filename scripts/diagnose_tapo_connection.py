"""Diagnose Tapo camera connection issues, including KLAP protocol detection."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

try:
    import pytapo
    print(f"✅ pytapo installed: version {pytapo.__version__}")
except ImportError:
    print("❌ pytapo not installed")
    sys.exit(1)

# Check for KLAP support
print("\n📋 Checking for KLAP protocol support...")
try:
    # Check if Tapo class has KLAP-related methods or attributes
    # Check Tapo class signature and methods
    import inspect

    from pytapo import Tapo
    tapo_methods = [m for m in dir(Tapo) if not m.startswith('_')]

    print(f"   Tapo class methods: {len(tapo_methods)} found")

    # Look for KLAP-related methods
    klap_indicators = ['klap', 'KLAP', 'kasa', 'Kasa', 'local', 'Local']
    klap_methods = [m for m in tapo_methods if any(indicator in m for indicator in klap_indicators)]

    if klap_methods:
        print(f"   ⚠️  Found potential KLAP-related methods: {klap_methods}")
    else:
        print("   ⚠️  No obvious KLAP-related methods found")

    # Check Tapo.__init__ signature
    sig = inspect.signature(Tapo.__init__)
    print(f"   Tapo.__init__ parameters: {list(sig.parameters.keys())}")

except Exception as e:
    print(f"   ❌ Error checking Tapo class: {e}")

# Check for alternative libraries
print("\n📋 Checking for alternative libraries...")
try:
    import kasa
    print(f"   ✅ python-kasa installed: version {kasa.__version__}")
except ImportError:
    print("   ⚠️  python-kasa not installed (alternative library)")

try:
    from onvif import ONVIFCamera
    print("   ✅ python-onvif-zeep installed (ONVIF support)")
except ImportError:
    print("   ⚠️  python-onvif-zeep not installed (ONVIF fallback)")

# Test connection with config
print("\n📋 Testing connection with config.yaml...")
try:
    import yaml
    config_path = project_root / "config.yaml"

    if config_path.exists():
        with open(config_path, encoding="utf-8") as f:
            config = yaml.safe_load(f)

        kitchen_cfg = config.get("cameras", {}).get("tapo_kitchen", {}).get("params", {})
        if kitchen_cfg:
            host = kitchen_cfg.get("host", "")
            username = kitchen_cfg.get("username", "")
            password = kitchen_cfg.get("password", "")

            if host and username and password:
                print(f"   Testing connection to {host}...")
                print(f"   Username: {username}")
                print(f"   Password: {'*' * len(password)}")

                try:
                    camera = Tapo(host, username, password)
                    info = camera.getBasicInfo()
                    print("   ✅ Connection successful!")

                    device_info = info.get("device_info", {})
                    print(f"   Model: {device_info.get('device_model', 'Unknown')}")
                    print(f"   Firmware: {device_info.get('firmware_version', 'Unknown')}")

                    # Check firmware version for KLAP indicators
                    firmware = device_info.get('firmware_version', '')
                    if firmware:
                        # Newer firmware versions may indicate KLAP support
                        print(f"   ⚠️  Firmware version: {firmware}")
                        print("   Note: Check if firmware requires KLAP protocol")

                except Exception as e:
                    error_msg = str(e)
                    print(f"   ❌ Connection failed: {error_msg}")

                    # Check for KLAP-related errors
                    if "KLAP" in error_msg or "kasa" in error_msg.lower():
                        print("   ⚠️  KLAP protocol may be required!")
                    elif "Invalid authentication" in error_msg or "Invalid auth" in error_msg:
                        print("   ⚠️  Authentication failed - check credentials")
                    elif "Temporary Suspension" in error_msg:
                        print("   ⚠️  Camera is locked out - wait 30 minutes")
            else:
                print("   ⚠️  Missing credentials in config.yaml")
        else:
            print("   ⚠️  No tapo_kitchen config found")
    else:
        print("   ⚠️  config.yaml not found")

except Exception as e:
    print(f"   ❌ Error reading config: {e}")

print("\n📋 Recommendations:")
print("   1. Check pytapo GitHub for KLAP support: https://github.com/JurajNyiri/pytapo")
print("   2. Check camera firmware version in Tapo app")
print("   3. Verify Third-Party Compatibility is enabled in Tapo app")
print("   4. Consider testing python-kasa library as alternative")
print("   5. Test ONVIF protocol as fallback")

