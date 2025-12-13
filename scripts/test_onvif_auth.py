"""Test Tapo camera using ONVIF authentication instead of pytapo.

Some Tapo cameras support ONVIF protocol which may work better
than the Tapo API for authentication.
"""

import sys


def test_onvif_connection(ip, username, password):
    """Test ONVIF authentication to Tapo camera."""
    try:
        from onvif import ONVIFCamera

        print(f"Testing ONVIF connection to {ip}...")
        print(f"Username: {username}")
        print(f"Password: {'*' * len(password)}")

        # Tapo C200 typically uses port 2020 for ONVIF
        camera = ONVIFCamera(ip, 2020, username, password)

        # Get device capabilities
        print("\nGetting device capabilities...")
        capabilities = camera.devicemgmt.GetCapabilities()

        print("[SUCCESS] ONVIF connection successful!")
        print(f"Device Manufacturer: {capabilities.Device.Manufacturer if hasattr(capabilities.Device, 'Manufacturer') else 'Unknown'}")
        print(f"Device Model: {capabilities.Device.Model if hasattr(capabilities.Device, 'Model') else 'Unknown'}")

        # Try to get profiles
        media_service = camera.create_media_service()
        profiles = media_service.GetProfiles()
        print(f"Video Profiles: {len(profiles)}")

        return True

    except ImportError:
        print("[ERROR] ONVIF library not installed")
        print("Install with: pip install onvif-zeep")
        return False
    except Exception as e:
        error_msg = str(e)
        print(f"\n[ERROR] ONVIF connection failed: {error_msg}")

        if "401" in error_msg or "Unauthorized" in error_msg:
            print("Authentication failed - check username/password")
        elif "Connection refused" in error_msg or "timeout" in error_msg.lower():
            print("Camera may not support ONVIF or port 2020 is not open")
            print("Some Tapo cameras use different ports or don't support ONVIF")

        return False

if __name__ == "__main__":
    import os

    import yaml

    # Load kitchen camera credentials from config
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
    print("Testing ONVIF Authentication to Tapo Camera")
    print("=" * 60)
    print("\nNote: ONVIF is an alternative protocol that some Tapo cameras support")
    print("If this works, we may need to use ONVIF instead of pytapo")
    print()

    success = test_onvif_connection(ip, username, password)

    if not success:
        print("\n" + "=" * 60)
        print("ONVIF Authentication Failed")
        print("=" * 60)
        print("\nPossible reasons:")
        print("1. Camera doesn't support ONVIF")
        print("2. ONVIF port (2020) is not open")
        print("3. ONVIF is not enabled in camera settings")
        print("4. Wrong credentials")
        print("\nCheck camera settings:")
        print("- Camera -> Settings -> Advanced -> ONVIF")
        print("- Enable ONVIF if available")
        print("=" * 60)

    sys.exit(0 if success else 1)

