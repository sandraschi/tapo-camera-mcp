"""Test if camera requires 'admin' as username for API access."""

import sys

from pytapo import Tapo


def test_with_admin(ip, password):
    """Test with 'admin' as username (common for Tapo API)."""
    print("Testing with 'admin' as username (Camera Account password)...")
    print(f"IP: {ip}")
    print("Username: admin")
    print(f"Password: {'*' * len(password)}")
    print()

    try:
        camera = Tapo(ip, "admin", password)
        info = camera.getBasicInfo()

        device_info = info.get("device_info", {})
        print("[SUCCESS] Connection successful with 'admin' username!")
        print(f"Model: {device_info.get('device_model', 'Unknown')}")
        print(f"Firmware: {device_info.get('firmware_version', 'Unknown')}")
        print(f"Serial: {device_info.get('serial_number', 'Unknown')}")
        print(f"MAC: {device_info.get('mac', 'Unknown')}")
        return True
    except Exception as e:
        error_msg = str(e)
        if "Invalid authentication" in error_msg:
            print("[FAILED] 'admin' username didn't work")
            return False
        if "Temporary Suspension" in error_msg:
            print("[LOCKOUT] Camera is locked out")
            return "locked"
        print(f"[ERROR] {error_msg}")
        return False

if __name__ == "__main__":
    import yaml

    ip = "192.168.0.164"
    password = "Sec1000kitchen"  # Camera Account password

    # Load from config
    try:
        with open("config.yaml", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        kitchen_cfg = config.get("cameras", {}).get("tapo_kitchen", {}).get("params", {})
        password = kitchen_cfg.get("password", password)
    except:
        pass

    print("=" * 60)
    print("Testing Tapo Camera with 'admin' username")
    print("=" * 60)
    print("\nNote: Some Tapo cameras require 'admin' as username")
    print("for API access, even if Camera Account has different username")
    print()

    result = test_with_admin(ip, password)

    if result is True:
        print("\n[SUCCESS] Use 'admin' as username for API access!")
        print("Update config.yaml:")
        print("  username: \"admin\"")
        print(f"  password: \"{password}\"")
    elif result == "locked":
        print("\n[LOCKOUT] Power cycle camera and try again")
    else:
        print("\n[FAILED] Both 'sandraschi' and 'admin' usernames failed")
        print("Check:")
        print("1. Camera Account password is correct in app")
        print("2. Camera Account is enabled for API access")
        print("3. Camera firmware is up to date")

    sys.exit(0 if result is True else 1)

