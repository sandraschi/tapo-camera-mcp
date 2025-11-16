"""Test connection to both Tapo cameras."""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.test_tapo_connection import test_connection


def test_all_cameras():
    """Test both cameras."""
    cameras = [
        {
            "name": "Kitchen Camera",
            "ip": "192.168.0.164",
            "username": "",  # Set in config.yaml
            "password": "",  # Set in config.yaml
        },
        {
            "name": "Living Room Camera",
            "ip": "192.168.0.206",
            "username": "",  # Set in config.yaml
            "password": "",  # Set in config.yaml
        },
    ]

    # Load credentials from config.yaml
    try:
        import yaml
        with open("config.yaml", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        # Get kitchen camera credentials
        kitchen_cfg = config.get("cameras", {}).get("tapo_kitchen", {}).get("params", {})
        cameras[0]["username"] = kitchen_cfg.get("username", "")
        cameras[0]["password"] = kitchen_cfg.get("password", "")

        # Get living room camera credentials
        living_room_cfg = config.get("cameras", {}).get("tapo_living_room", {}).get("params", {})
        cameras[1]["username"] = living_room_cfg.get("username", "")
        cameras[1]["password"] = living_room_cfg.get("password", "")
    except Exception as e:
        print(f"[WARNING] Could not load config.yaml: {e}")
        print("Please set credentials manually in config.yaml first")
        sys.exit(1)

    print("Testing Both Tapo Cameras")
    print("=" * 60)

    all_success = True

    for camera in cameras:
        print(f"\n{'=' * 60}")
        print(f"Testing: {camera['name']} ({camera['ip']})")
        print(f"{'=' * 60}")

        if not camera["username"] or not camera["password"]:
            print(f"[SKIP] {camera['name']} - No credentials set in config.yaml")
            print("Set username/password in config.yaml -> cameras -> tapo_kitchen/tapo_living_room")
            all_success = False
            continue

        success = test_connection(
            camera["ip"],
            camera["username"],
            camera["password"],
            max_attempts=1
        )

        if not success:
            all_success = False

    print("\n" + "=" * 60)
    if all_success:
        print("[SUCCESS] All cameras connected successfully!")
        print("\nBoth cameras are ready to use via API.")
    else:
        print("[INCOMPLETE] Some cameras failed or need credentials")
        print("\nNext steps:")
        print("1. Get Camera Account credentials from Tapo app:")
        print("   Camera -> Settings -> Advanced -> Camera Account")
        print("2. Update config.yaml with username/password for each camera")
        print("3. Run this script again to test")
    print("=" * 60)

    return all_success


if __name__ == "__main__":
    success = test_all_cameras()
    sys.exit(0 if success else 1)

