"""Inspect Tapo P115 energy object to see what attributes are available."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tapo_camera_mcp.ingest.tapo_p115 import TapoP115IngestionService


async def inspect_energy(host: str, name: str):
    """Inspect the energy object to see what attributes are available."""
    print(f"\n{'='*60}")
    print(f"Inspecting {name} (IP: {host})")
    print(f"{'='*60}")

    try:
        service = TapoP115IngestionService()
        client = await service._get_client()
        plug = await client.p115(host)

        # Get device info first
        print("Getting device info...")
        device_info = await plug.get_device_info()
        print(f"Device info type: {type(device_info)}")
        print(f"Device info attributes: {[attr for attr in dir(device_info) if not attr.startswith('_')]}")

        # Try to get device info as dict
        if hasattr(device_info, '__dict__'):
            print("\nDevice info __dict__:")
            for key, val in device_info.__dict__.items():
                print(f"  {key}: {val}")

        # Get energy usage
        print("\n" + "="*50)
        print("Getting energy usage...")
        energy = await plug.get_energy_usage()

        print(f"\nEnergy object type: {type(energy)}")
        print("\nEnergy object attributes:")
        print(f"  dir(): {[attr for attr in dir(energy) if not attr.startswith('_')]}")

        print("\nTrying to access common attributes:")
        attrs_to_try = [
            "current_power", "power", "power_mw", "realtime_power",
            "voltage", "voltage_v", "realtime_voltage",
            "current", "current_a", "realtime_current", "current_ma",
            "today_energy", "today", "today_kwh", "energy_today",
            "month_energy", "month", "month_kwh", "energy_month",
        ]

        for attr in attrs_to_try:
            try:
                val = getattr(energy, attr, None)
                if val is not None:
                    print(f"  {attr}: {val} (type: {type(val)})")
            except Exception as e:
                print(f"  {attr}: ERROR - {e}")

        # Try to get as dict if possible
        if hasattr(energy, '__dict__'):
            print("\nEnergy object __dict__:")
            for key, val in energy.__dict__.items():
                print(f"  {key}: {val}")

        # Check if plug has other methods for power data
        print("\n" + "="*50)
        print("Checking plug object methods...")
        plug_methods = [method for method in dir(plug) if not method.startswith('_') and callable(getattr(plug, method))]
        print(f"Available methods: {plug_methods}")

        # Try get_current_power method
        print("\n" + "="*50)
        print("Testing get_current_power() method...")
        try:
            current_power_result = await plug.get_current_power()
            print(f"get_current_power() result type: {type(current_power_result)}")
            print(f"get_current_power() result: {current_power_result}")

            if hasattr(current_power_result, '__dict__'):
                print("get_current_power() result __dict__:")
                for key, val in current_power_result.__dict__.items():
                    print(f"  {key}: {val}")

            # Check if it has power attribute
            if hasattr(current_power_result, 'power'):
                print(f"Power from get_current_power(): {current_power_result.power}")
            elif hasattr(current_power_result, 'current_power'):
                print(f"Current power from get_current_power(): {current_power_result.current_power}")

        except Exception as e:
            print(f"get_current_power() failed: {e}")
            import traceback
            traceback.print_exc()

        # Try get_power_data method
        print("\n" + "="*50)
        print("Testing get_power_data() method...")
        try:
            power_data_result = await plug.get_power_data()
            print(f"get_power_data() result type: {type(power_data_result)}")
            print(f"get_power_data() result: {power_data_result}")

            if hasattr(power_data_result, '__dict__'):
                print("get_power_data() result __dict__:")
                for key, val in power_data_result.__dict__.items():
                    print(f"  {key}: {val}")

        except Exception as e:
            print(f"get_power_data() failed: {e}")

        # Try get_device_usage method
        print("\n" + "="*50)
        print("Testing get_device_usage() method...")
        try:
            device_usage_result = await plug.get_device_usage()
            print(f"get_device_usage() result type: {type(device_usage_result)}")
            print(f"get_device_usage() result: {device_usage_result}")

            if hasattr(device_usage_result, '__dict__'):
                print("get_device_usage() result __dict__:")
                for key, val in device_usage_result.__dict__.items():
                    print(f"  {key}: {val}")

        except Exception as e:
            print(f"get_device_usage() failed: {e}")

        return True

    except Exception as e:
        print(f"[FAILED] Inspection failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Inspect Server plug energy object."""
    print("="*60)
    print("Tapo P115 Energy Object Inspection")
    print("="*60)

    # Inspect Server plug (should be ~400W)
    success = await inspect_energy("192.168.0.38", "Server")

    return 0 if success else 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Inspection cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

