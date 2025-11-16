"""Test Tapo camera connection."""

import sys

from pytapo import Tapo


def test_connection(ip, username, password, max_attempts=1):
    """Test connection to Tapo camera.
    
    Args:
        ip: Camera IP address
        username: Local admin username
        password: Local admin password
        max_attempts: Maximum login attempts (default 1 to prevent lockouts)
    
    Returns:
        bool: True if connection successful, False otherwise
    """
    # Only attempt once to prevent lockouts
    attempts = 0
    while attempts < max_attempts:
        attempts += 1
        try:
            print(f"Testing connection to {ip}... (attempt {attempts}/{max_attempts})")
            camera = Tapo(ip, username, password)
            info = camera.getBasicInfo()

            device_info = info.get("device_info", {})
            print("\n[SUCCESS] Connection successful!")
            print(f"Model: {device_info.get('device_model', 'Unknown')}")
            print(f"Firmware: {device_info.get('firmware_version', 'Unknown')}")
            print(f"Serial: {device_info.get('serial_number', 'Unknown')}")
            print(f"MAC: {device_info.get('mac', 'Unknown')}")
            print(f"Hostname: {device_info.get('device_alias', 'Unknown')}")
            return True
        except Exception as e:
            error_msg = str(e)

            # Check for lockout - stop immediately if detected
            if "Temporary Suspension" in error_msg or "1800 seconds" in error_msg:
                print(f"\n[LOCKOUT] Camera at {ip} is temporarily locked out!")
                print("Reason: Too many failed login attempts")
                print("Action: Wait 30 minutes (1800 seconds) before trying again")
                print("Prevention: This script only attempts once to avoid lockouts")
                return False

            # Check for authentication errors - don't retry
            if "Invalid authentication" in error_msg or "Invalid auth" in error_msg:
                print(f"\n[ERROR] Authentication failed for {ip}")
                print("Possible causes:")
                print("  1. Wrong username/password (use LOCAL admin, not cloud account)")
                print("  2. Camera requires different credentials")
                print("  3. Camera security settings changed")
                print("\nNote: Tapo cameras require LOCAL admin credentials set in the Tapo app.")
                print("Go to: Tapo app -> Camera -> Device Settings -> Advanced -> Local Device Settings")
                return False

            # Other errors - might retry if allowed
            if attempts < max_attempts:
                print(f"[WARNING] Attempt {attempts} failed: {error_msg}")
                print(f"Retrying... (max {max_attempts} attempts)")
            else:
                print(f"\n[ERROR] Connection failed after {attempts} attempt(s): {error_msg}")
                return False

    return False

if __name__ == "__main__":
    import os
    import sys

    import yaml

    # Try to load credentials from config.yaml
    ip = "192.168.0.164"  # Kitchen camera
    username = "admin"
    password = "admin"

    config_path = "config.yaml"
    if os.path.exists(config_path):
        try:
            with open(config_path, encoding="utf-8") as f:
                config = yaml.safe_load(f)

            # Get kitchen camera credentials from config
            kitchen_cfg = config.get("cameras", {}).get("tapo_kitchen", {}).get("params", {})
            config_username = kitchen_cfg.get("username", "")
            config_password = kitchen_cfg.get("password", "")

            if config_username and config_password:
                username = config_username
                password = config_password
                print("Using credentials from config.yaml")
        except Exception as e:
            print(f"[WARNING] Could not load config.yaml: {e}")
            print("Using default credentials (update config.yaml)")

    print("Testing Tapo camera credentials...")
    print(f"Camera IP: {ip}")
    print(f"Username: {username}")
    print(f"Password: {'*' * len(password)}")
    print()

    success = test_connection(ip, username, password)

    if not success:
        print("\n" + "="*60)
        print("Connection failed. Check:")
        print("="*60)
        print("1. Credentials in config.yaml (cameras.tapo_kitchen.params)")
        print("2. Camera Account settings in Tapo app")
        print("3. Camera is online and accessible on network")
        print("="*60)

    sys.exit(0 if success else 1)

