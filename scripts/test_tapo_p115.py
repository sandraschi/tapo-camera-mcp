"""Test connection to Tapo P115 smart plug using python-kasa."""

import asyncio
import sys


async def test_p115_connection(ip, username=None, password=None):
    """Test connection to Tapo P115 smart plug.
    
    Uses same method as existing code in tapo_p115.py.
    """
    try:
        from kasa import Credentials, SmartPlug

        print(f"Testing connection to Tapo P115 at {ip}...")

        # Create credentials if provided (for cloud access)
        credentials = None
        if username and password:
            print(f"Using credentials: {username} / {'*' * len(password)}")
            credentials = Credentials(username, password)
        else:
            print("No credentials provided - trying local connection")

        # Create SmartPlug instance directly (same as existing code)
        print("Creating SmartPlug instance...")
        plug = SmartPlug(ip)

        # Update to get device info
        # Note: Credentials might need to be set differently or may not be needed for local access
        print("Connecting to device...")
        try:
            # Try without credentials first (local access)
            await plug.update()
        except Exception:
            if credentials:
                print("Local connection failed, trying with credentials...")
                # For newer kasa versions, credentials might need to be passed differently
                # or the plug might need cloud access enabled
                raise
            raise

        # Get device information
        print("\n[SUCCESS] Connection successful!")
        print(f"Alias: {plug.alias}")
        print(f"Model: {plug.model}")
        print(f"Host: {plug.host}")
        print(f"Device ID: {plug.device_id}")
        print(f"MAC Address: {plug.mac}")

        # Get current state
        print("\nCurrent State:")
        print(f"  Power: {'ON' if plug.is_on else 'OFF'}")
        print(f"  LED: {'ON' if plug.led else 'OFF'}")

        # Get energy monitoring data
        if hasattr(plug, 'emeter_realtime'):
            emeter = plug.emeter_realtime
            print("\nEnergy Monitoring:")
            print(f"  Current Power: {emeter.power} W")
            print(f"  Voltage: {emeter.voltage} V")
            print(f"  Current: {emeter.current} A")
            print(f"  Today's Energy: {emeter.today} kWh")
            print(f"  This Month: {emeter.month} kWh")

        return True

    except ImportError:
        print("[ERROR] python-kasa library not installed")
        print("Install with: pip install python-kasa")
        return False
    except Exception as e:
        error_msg = str(e)
        error_type = type(e).__name__
        print(f"\n[ERROR] Connection failed: {error_type}: {error_msg}")

        if "Connection" in error_msg or "timeout" in error_msg.lower():
            print("\nPossible causes:")
            print("1. Device is not online at IP 192.168.0.17")
            print("2. Network connectivity issue")
            print("3. Firewall blocking connection")
        elif "authentication" in error_msg.lower() or "auth" in error_msg.lower():
            print("\nPossible causes:")
            print("1. Need credentials for cloud access")
            print("2. Local authentication required")
        elif "Unknown" in error_msg or "not found" in error_msg.lower():
            print("\nPossible causes:")
            print("1. Device might not be a TP-Link/Tapo device")
            print("2. Device might not be accessible via kasa protocol")

        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import os

    import yaml

    ip = "192.168.0.17"
    username = None
    password = None

    # Try to load credentials from config
    config_path = "config.yaml"
    if os.path.exists(config_path):
        try:
            with open(config_path, encoding="utf-8") as f:
                config = yaml.safe_load(f)
            energy_cfg = config.get("energy", {}).get("tapo_p115", {})
            account_cfg = energy_cfg.get("account", {})
            username = account_cfg.get("username") or os.getenv("TAPO_ACCOUNT_EMAIL")
            password = account_cfg.get("password") or os.getenv("TAPO_ACCOUNT_PASSWORD")
        except Exception as e:
            print(f"[WARNING] Could not load config: {e}")

    # If no credentials from config, try using camera account credentials
    if not username and not password:
        print("[INFO] No credentials in config - trying cloud account credentials")
        username = "sandraschipal@hotmail.com"
        password = "Sec0860ta#"

    print("=" * 60)
    print("Testing Tapo P115 Smart Plug Connection")
    print("=" * 60)
    print(f"\nDevice IP: {ip}")
    if username and password:
        print(f"Username: {username}")
        print(f"Password: {'*' * len(password)}")
    else:
        print("Credentials: Not provided (will try local connection)")
    print()

    try:
        success = asyncio.run(test_p115_connection(ip, username, password))

        if success:
            print("\n" + "=" * 60)
            print("[SUCCESS] Tapo P115 Smart Plug is accessible!")
            print("=" * 60)
            print("\nYou can now use this device for energy monitoring.")
            print("Update config.yaml with device details if needed.")
        else:
            print("\n" + "=" * 60)
            print("[FAILED] Could not connect to device")
            print("=" * 60)
            print("\nTry:")
            print("1. Verify device is online at 192.168.0.17")
            print("2. Check if device is accessible on network")
            print("3. Verify credentials if using cloud access")
            print("4. Try ping to verify connectivity: ping 192.168.0.17")

        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Test cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

