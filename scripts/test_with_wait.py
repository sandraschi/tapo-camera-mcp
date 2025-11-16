"""Test camera connection after waiting for full initialization."""

import os
import sys
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import yaml

from scripts.test_tapo_connection import test_connection


def test_after_wait(ip, username, password, wait_seconds=30):
    """Wait then test connection."""
    print(f"Waiting {wait_seconds} seconds for camera to fully initialize after reboot...")
    print("(Some cameras need time to fully initialize services after reboot)")

    for i in range(wait_seconds, 0, -5):
        print(f"  {i} seconds remaining...")
        time.sleep(5)

    print("\nTesting connection now...")
    return test_connection(ip, username, password, max_attempts=1)

if __name__ == "__main__":
    import os

    import yaml

    ip = "192.168.0.164"
    username = "sandraschi"
    password = "Sec1000kitchen"

    # Load from config
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
    print("Testing Tapo Camera After Full Initialization")
    print("=" * 60)
    print(f"\nCamera IP: {ip}")
    print(f"Username: {username}")
    print(f"Password: {'*' * len(password)}")
    print("\nNote: Camera may need time to fully initialize after reboot")
    print()

    # Wait 30 seconds then test
    success = test_after_wait(ip, username, password, wait_seconds=30)

    if not success:
        print("\n" + "=" * 60)
        print("Still failing. Check:")
        print("=" * 60)
        print("1. Third-Party Compatibility is ON in Tapo app")
        print("2. Camera Account username/password are correct")
        print("3. Disable Two-Step Verification in Tapo app:")
        print("   Me -> View Account -> Login Security -> Turn OFF Two-Step Verification")
        print("4. Camera firmware is up to date")
        print("5. Try waiting longer (some cameras need 2-3 minutes after reboot)")
        print("=" * 60)

    sys.exit(0 if success else 1)

