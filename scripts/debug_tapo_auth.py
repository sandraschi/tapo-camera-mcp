"""Debug Tapo camera authentication to see exact error."""

import sys

from pytapo import Tapo


def debug_auth(ip, username, password):
    """Test authentication with detailed error info."""
    print(f"Testing authentication to {ip}")
    print(f"Username: {username}")
    print(f"Password: {'*' * len(password)}")
    print()

    try:
        print("Creating Tapo instance...")
        camera = Tapo(ip, username, password)
        print("✅ Tapo instance created")

        print("\nCalling getBasicInfo()...")
        info = camera.getBasicInfo()
        print("✅ getBasicInfo() successful!")

        device_info = info.get("device_info", {})
        print("\n[SUCCESS] Camera connected!")
        print(f"Model: {device_info.get('device_model', 'Unknown')}")
        print(f"Firmware: {device_info.get('firmware_version', 'Unknown')}")
        print(f"Serial: {device_info.get('serial_number', 'Unknown')}")
        print(f"MAC: {device_info.get('mac', 'Unknown')}")
        print(f"Hostname: {device_info.get('device_alias', 'Unknown')}")
        return True

    except Exception as e:
        error_type = type(e).__name__
        error_msg = str(e)
        print(f"\n[ERROR] {error_type}: {error_msg}")
        print("\nFull error details:")
        import traceback
        traceback.print_exc()

        # Check for specific error patterns
        if "Temporary Suspension" in error_msg or "1800 seconds" in error_msg:
            print("\n❌ Camera is LOCKED OUT")
            print("   Wait 30 minutes or power cycle camera")
        elif "Invalid authentication" in error_msg or "Invalid auth" in error_msg:
            print("\n❌ Authentication failed")
            print("   Possible issues:")
            print("   1. Wrong username/password")
            print("   2. Camera Account not enabled")
            print("   3. Camera Account type mismatch")
            print("   4. Camera needs to be re-authenticated in app")
        elif "Connection" in error_msg or "timeout" in error_msg.lower():
            print("\n❌ Connection failed")
            print("   Check camera is online and IP is correct")
        else:
            print(f"\n❌ Unknown error: {error_type}")

        return False

if __name__ == "__main__":
    import os

    import yaml

    # Load credentials from config
    ip = "192.168.0.164"
    username = "sandraschi"
    password = "Sec1000kitchen"

    config_path = "config.yaml"
    if os.path.exists(config_path):
        try:
            with open(config_path, encoding="utf-8") as f:
                config = yaml.safe_load(f)
            kitchen_cfg = config.get("cameras", {}).get("tapo_kitchen", {}).get("params", {})
            username = kitchen_cfg.get("username", username)
            password = kitchen_cfg.get("password", password)
        except Exception as e:
            print(f"[WARNING] Could not load config: {e}")

    print("=" * 60)
    print("Tapo Camera Authentication Debug")
    print("=" * 60)
    print()

    success = debug_auth(ip, username, password)

    if not success:
        print("\n" + "=" * 60)
        print("Troubleshooting Steps:")
        print("=" * 60)
        print("1. Verify Camera Account is enabled in Tapo app")
        print("2. Try changing Camera Account password in app")
        print("3. Make sure you're using Camera Account (not cloud account)")
        print("4. Some cameras require 'admin' as username for API access")
        print("5. Check if Camera Account has API access enabled")
        print("=" * 60)

    sys.exit(0 if success else 1)

