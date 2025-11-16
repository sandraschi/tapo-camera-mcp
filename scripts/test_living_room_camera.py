"""Test living room camera connection specifically."""

import os
import sys

import yaml

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.test_tapo_connection import test_connection

if __name__ == "__main__":
    # Load living room camera credentials from config
    ip = "192.168.0.206"
    username = "sandraschi"
    password = "Sec1000living"

    config_path = "config.yaml"
    if os.path.exists(config_path):
        try:
            with open(config_path, encoding="utf-8") as f:
                config = yaml.safe_load(f)
            living_room_cfg = config.get("cameras", {}).get("tapo_living_room", {}).get("params", {})
            username = living_room_cfg.get("username", username)
            password = living_room_cfg.get("password", password)
        except Exception as e:
            print(f"[WARNING] Could not load config: {e}")

    print("=" * 60)
    print("Testing Living Room Camera")
    print("=" * 60)
    print(f"\nCamera IP: {ip} (static)")
    print(f"Username: {username}")
    print(f"Password: {'*' * len(password)}")
    print("\nThis test will help us understand if the authentication")
    print("issue is camera-specific (kitchen) or general.")
    print()

    success = test_connection(ip, username, password, max_attempts=1)

    if success:
        print("\n" + "=" * 60)
        print("[SUCCESS] Living Room Camera Connected!")
        print("=" * 60)
        print("\nThis means:")
        print("✅ Authentication method works correctly")
        print("✅ Third-Party Compatibility is working")
        print("✅ Issue is specific to Kitchen Camera")
        print("\nNext: Investigate kitchen camera-specific issues")
    else:
        print("\n" + "=" * 60)
        print("[FAILED] Living Room Camera Also Failed")
        print("=" * 60)
        print("\nThis means:")
        print("[ISSUE] Authentication issue is general (both cameras)")
        print("[ISSUE] May be pytapo library issue or configuration")
        print("[ISSUE] Need to investigate authentication method")
        print("\nPossible causes:")
        print("1. pytapo library incompatibility with C200")
        print("2. Camera Account credentials format issue")
        print("3. Third-Party Compatibility setting not fully working")
        print("4. Need different authentication method")

    print("=" * 60)
    sys.exit(0 if success else 1)

