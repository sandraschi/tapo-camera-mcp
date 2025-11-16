"""Check if Tapo camera needs initial setup.

Newer Tapo cameras often require initial setup through the Tapo app
before local API access works. This script checks if the camera
is set up and accessible.
"""

import sys

from pytapo import Tapo


def check_camera_status(ip, username, password):
    """Check if camera is accessible with given credentials."""
    try:
        print(f"Checking camera at {ip}...")
        print(f"Username: {username}")
        print(f"Password: {'*' * len(password) if password else '(empty)'}")

        camera = Tapo(ip, username, password)
        info = camera.getBasicInfo()

        device_info = info.get("device_info", {})
        print("\n[SUCCESS] Camera is accessible!")
        print(f"Model: {device_info.get('device_model', 'Unknown')}")
        print(f"Firmware: {device_info.get('firmware_version', 'Unknown')}")
        print(f"Serial: {device_info.get('serial_number', 'Unknown')}")
        print(f"MAC: {device_info.get('mac', 'Unknown')}")
        print(f"Hostname: {device_info.get('device_alias', 'Unknown')}")

        # Check if camera is in setup mode or fully configured
        is_configured = device_info.get("device_alias") and device_info.get("device_alias") != "TapoCamera"
        if not is_configured:
            print("\n[INFO] Camera appears to be in setup mode (default hostname)")
            print("You may need to complete setup in the Tapo app first.")

        return True

    except Exception as e:
        error_msg = str(e)

        if "Temporary Suspension" in error_msg or "1800 seconds" in error_msg:
            print("\n[LOCKOUT] Camera is temporarily locked out.")
            print("Wait 30 minutes or power cycle the camera.")
            return "locked"

        if "Invalid authentication" in error_msg or "Invalid auth" in error_msg:
            print(f"\n[FAILED] Authentication failed: {error_msg}")
            return False

        print(f"\n[ERROR] Connection failed: {error_msg}")
        return False


def try_setup_combinations(ip):
    """Try common credentials after factory reset."""
    print("\n" + "=" * 60)
    print("Trying common credential combinations after factory reset...")
    print("=" * 60)
    print("\nWARNING: Too many attempts will lock the camera!")
    print("Only trying safe combinations.\n")

    # Common combinations to try (in order of likelihood)
    combinations = [
        # After reset, some cameras accept cloud credentials if previously linked
        ("sandraschipal@hotmail.com", "Sec0860ta#"),
        # Default admin (common but we know it didn't work)
        ("admin", "admin"),
        # Empty password
        ("admin", ""),
        # Some cameras use serial number or MAC-based passwords
        # (can't try without knowing the actual values)
    ]

    for username, password in combinations:
        print(f"\nTrying: {username} / {password}")
        result = check_camera_status(ip, username, password)

        if result is True:
            print("\n[SUCCESS] Working credentials found!")
            print(f"Username: {username}")
            print(f"Password: {password}")
            return (username, password)

        if result == "locked":
            print("\n[STOPPED] Camera locked out. Cannot continue testing.")
            return None

    return None


if __name__ == "__main__":
    ip = "192.168.0.164"  # Kitchen camera

    print("Tapo Camera Setup Check")
    print("=" * 60)
    print(f"\nChecking camera at {ip}...")
    print("\nNote: Newer Tapo cameras may require:")
    print("1. Initial setup through Tapo app")
    print("2. Camera linked to cloud account")
    print("3. Local credentials set in app")
    print()

    # Try cloud credentials first (most likely after reset if previously linked)
    print("Trying cloud account credentials (if camera was previously linked)...")
    result = check_camera_status(ip, "sandraschipal@hotmail.com", "Sec0860ta#")

    if result is True:
        print("\n[SUCCESS] Cloud credentials work!")
        print("Your camera is set up and accessible.")
        sys.exit(0)

    if result == "locked":
        print("\n[LOCKOUT] Camera is locked out.")
        print("Options:")
        print("1. Wait 30 minutes for lockout to expire")
        print("2. Power cycle the camera (unplug/replug)")
        print("3. After unlock, try setting up camera in Tapo app first")
        sys.exit(1)

    # If cloud didn't work, try other combinations
    print("\nCloud credentials didn't work. Trying other combinations...")
    result = try_setup_combinations(ip)

    if result:
        print(f"\nWorking credentials: {result[0]}/{result[1]}")
        sys.exit(0)
    else:
        print("\n" + "=" * 60)
        print("[ACTION REQUIRED] Camera needs setup")
        print("=" * 60)
        print("\nSteps:")
        print("1. Open Tapo app on your phone")
        print("2. Add camera (scan QR code or enter serial number)")
        print("3. Complete initial setup in the app")
        print("4. After setup, check: Camera -> Advanced -> Local Device Settings")
        print("5. Set or view local admin credentials")
        print("\nOR:")
        print("1. Power cycle the camera")
        print("2. Wait 30 minutes for any lockouts to clear")
        print("3. Try cloud credentials again")
        print("=" * 60)
        sys.exit(1)

