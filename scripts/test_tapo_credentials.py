"""Test different Tapo credential combinations to find working method."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

import yaml
from pytapo import Tapo

# Load config
config_path = project_root / "config.yaml"
with open(config_path, encoding="utf-8") as f:
    config = yaml.safe_load(f)

kitchen_cfg = config.get("cameras", {}).get("tapo_kitchen", {}).get("params", {})
host = kitchen_cfg.get("host", "192.168.0.164")
camera_username = kitchen_cfg.get("username", "")
camera_password = kitchen_cfg.get("password", "")

print("=" * 70)
print("Testing Tapo Camera Credentials - Multiple Combinations")
print("=" * 70)
print(f"Camera IP: {host}")
print()

# Test different credential combinations
test_combinations = [
    {
        "name": "Camera Account (from config)",
        "username": camera_username,
        "password": camera_password,
    },
    {
        "name": "Admin (default)",
        "username": "admin",
        "password": camera_password,  # Try camera password with admin username
    },
    {
        "name": "Admin + Admin",
        "username": "admin",
        "password": "admin",
    },
    {
        "name": "Camera Account username + Admin password",
        "username": camera_username,
        "password": "admin",
    },
]

successful = None

for i, combo in enumerate(test_combinations, 1):
    if not combo["username"] or not combo["password"]:
        print(f"[SKIP] Test {i}: {combo['name']} - Missing credentials")
        continue

    print(f"[TEST {i}] {combo['name']}")
    print(f"   Username: {combo['username']}")
    print(f"   Password: {'*' * len(combo['password'])}")

    try:
        camera = Tapo(host, combo["username"], combo["password"])
        info = camera.getBasicInfo()

        device_info = info.get("device_info", {})
        print("   [SUCCESS] Connection successful!")
        print(f"   Model: {device_info.get('device_model', 'Unknown')}")
        print(f"   Firmware: {device_info.get('firmware_version', 'Unknown')}")
        print(f"   Serial: {device_info.get('serial_number', 'Unknown')}")

        successful = combo
        break

    except Exception as e:
        error_msg = str(e)
        print(f"   [FAILED] {error_msg}")

        if "Temporary Suspension" in error_msg or "1800 seconds" in error_msg:
            print("   [WARNING] Camera is locked out - wait 30 minutes")
            print("   [STOP] Stopping tests to prevent further lockouts")
            break
        elif "Invalid authentication" in error_msg or "Invalid auth" in error_msg:
            print("   [INFO] Authentication failed - trying next combination")
        else:
            print("   [INFO] Connection error - trying next combination")

    print()

print()
print("=" * 70)
print("RESULTS")
print("=" * 70)

if successful:
    print("[SUCCESS] Working credentials found!")
    print(f"   Method: {successful['name']}")
    print(f"   Username: {successful['username']}")
    print(f"   Password: {'*' * len(successful['password'])}")
    print()
    print("Update config.yaml with these credentials:")
    print(f"   username: \"{successful['username']}\"")
    print(f"   password: \"{successful['password']}\"")
else:
    print("[FAILED] No working credentials found")
    print()
    print("Troubleshooting:")
    print("  1. Verify Third-Party Compatibility is enabled:")
    print("     Tapo App -> Me -> Tapo Lab -> Third-Party Compatibility -> On")
    print()
    print("  2. Verify Camera Account is set up:")
    print("     Tapo App -> Camera -> Settings -> Advanced -> Camera Account")
    print("     Create a username and password specifically for API access")
    print()
    print("  3. Check if camera is locked out:")
    print("     Wait 30 minutes if you see 'Temporary Suspension' errors")
    print()
    print("  4. Verify camera firmware is up to date")
    print("  5. Check network connectivity to camera")

print()
print("=" * 70)

