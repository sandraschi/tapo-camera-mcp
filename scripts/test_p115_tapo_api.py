"""Test Tapo P115 smart plug using tapo library (not python-kasa).

Tapo P115 uses the Tapo API (same as cameras) not the Kasa protocol.
"""

import asyncio
import sys


async def test_p115_tapo_api(ip, username, password):
    """Test connection to Tapo P115 using tapo library."""
    try:
        from tapo import ApiClient

        print("Testing Tapo P115 connection using Tapo API...")
        print(f"IP: {ip}")
        print(f"Username: {username}")
        print(f"Password: {'*' * len(password)}")
        print()

        # Create API client
        print("Creating Tapo API client...")
        client = ApiClient(username, password)

        # Connect to P115 device
        print(f"Connecting to P115 at {ip}...")
        plug = await client.p115(ip)

        # Get device info (returns object, not dict)
        device_info = await plug.get_device_info()

        print("\n[SUCCESS] Connection successful!")
        print(f"Device Info Type: {type(device_info).__name__}")

        # Access attributes directly (object, not dict)
        device_name = getattr(device_info, 'nickname', getattr(device_info, 'name', 'Unknown'))
        model = getattr(device_info, 'model', 'Unknown')
        firmware = getattr(device_info, 'fw_ver', getattr(device_info, 'firmware_version', 'Unknown'))
        mac = getattr(device_info, 'mac', 'Unknown')
        device_id = getattr(device_info, 'device_id', 'Unknown')

        print(f"Device Name: {device_name}")
        print(f"Model: {model}")
        print(f"Firmware: {firmware}")
        print(f"MAC: {mac}")
        print(f"Device ID: {device_id}")

        # Get current state (different API methods for P115)
        print("\nCurrent State:")
        try:
            # Try different methods to get state
            is_on = await plug.is_on()
            print(f"  Power: {'ON' if is_on else 'OFF'}")
        except AttributeError:
            try:
                state = await plug.get_state()
                is_on = getattr(state, 'is_on', getattr(state, 'device_on', False))
                print(f"  Power: {'ON' if is_on else 'OFF'}")
            except Exception:
                print("  Power: State information not available")

        # Get energy usage if available
        try:
            energy_usage = await plug.get_energy_usage()
            if energy_usage:
                print("\nEnergy Usage:")
                current_power = getattr(energy_usage, 'current_power', getattr(energy_usage, 'power', 0))
                today_energy = getattr(energy_usage, 'today_energy', getattr(energy_usage, 'today', 0))
                month_energy = getattr(energy_usage, 'month_energy', getattr(energy_usage, 'month', 0))
                print(f"  Current Power: {current_power} W")
                print(f"  Today's Energy: {today_energy} kWh")
                print(f"  This Month: {month_energy} kWh")
        except Exception as e:
            print(f"\nNote: Energy usage not available: {e}")

        return True

    except ImportError:
        print("[ERROR] tapo library not installed")
        print("Install with: pip install tapo")
        print("\nNote: Tapo P115 uses 'tapo' library (Tapo API), not 'python-kasa'")
        return False
    except Exception as e:
        error_msg = str(e)
        error_type = type(e).__name__
        print(f"\n[ERROR] Connection failed: {error_type}: {error_msg}")

        if "Temporary Suspension" in error_msg or "1800 seconds" in error_msg:
            print("\n[LOCKOUT] Device is temporarily locked out")
            print("Wait 30 minutes or power cycle the device")
        elif "Invalid authentication" in error_msg or "Invalid auth" in error_msg:
            print("\n[FAILED] Authentication failed")
            print("Check username/password")
            print("Note: Tapo P115 uses Tapo account credentials (cloud account)")
        elif "Connection" in error_msg or "timeout" in error_msg.lower():
            print("\n[FAILED] Connection failed")
            print("Check:")
            print("1. Device is online at IP 192.168.0.17")
            print("2. Device is accessible on network")
            print("3. Third-Party Compatibility is enabled in Tapo app")

        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    ip = "192.168.0.17"
    username = "sandraschipal@hotmail.com"
    password = "Sec0860ta#"

    print("=" * 60)
    print("Testing Tapo P115 Smart Plug via Tapo API")
    print("=" * 60)
    print("\nNote: Tapo P115 uses Tapo API (same as cameras)")
    print("Uses 'tapo' Python library, not 'python-kasa'")
    print()

    try:
        success = asyncio.run(test_p115_tapo_api(ip, username, password))

        if success:
            print("\n" + "=" * 60)
            print("[SUCCESS] Tapo P115 is accessible via Tapo API!")
            print("=" * 60)
            print("\nThis confirms Tapo API works for smart plugs.")
            print("The authentication issue is likely specific to cameras.")
        else:
            print("\n" + "=" * 60)
            print("[FAILED] Could not connect to P115")
            print("=" * 60)
            print("\nTroubleshooting:")
            print("1. Verify device is online and accessible")
            print("2. Check credentials (use cloud account)")
            print("3. Enable Third-Party Compatibility in Tapo app")
            print("4. Make sure 'tapo' library is installed")

        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Test cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

