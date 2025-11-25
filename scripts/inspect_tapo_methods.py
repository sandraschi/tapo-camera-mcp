"""Inspect Tapo P115 plug object to see what methods are available."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tapo_camera_mcp.ingest.tapo_p115 import TapoP115IngestionService


async def inspect_plug_methods(host: str, name: str):
    """Inspect the plug object to see what methods are available."""
    print(f"\n{'='*60}")
    print(f"Inspecting {name} (IP: {host})")
    print(f"{'='*60}")
    
    try:
        service = TapoP115IngestionService()
        client = await service._get_client()
        plug = await client.p115(host)
        
        print(f"\nPlug object type: {type(plug)}")
        print(f"\nPlug object methods:")
        methods = [attr for attr in dir(plug) if not attr.startswith('_') and callable(getattr(plug, attr))]
        for method in sorted(methods):
            print(f"  - {method}")
        
        # Try to get device info and see what's available
        print(f"\nDevice info:")
        device_info = await plug.get_device_info()
        print(f"  Device info type: {type(device_info)}")
        print(f"  Device info attributes: {[attr for attr in dir(device_info) if not attr.startswith('_')]}")
        
        # Try to see if device_info has energy data
        print(f"\nDevice info values:")
        for attr in dir(device_info):
            if not attr.startswith('_'):
                try:
                    val = getattr(device_info, attr)
                    if not callable(val):
                        print(f"  {attr}: {val}")
                except:
                    pass
        
        # Try get_energy_usage
        print(f"\nEnergy usage:")
        energy = await plug.get_energy_usage()
        print(f"  Energy type: {type(energy)}")
        print(f"  Energy attributes: {[attr for attr in dir(energy) if not attr.startswith('_')]}")
        print(f"  today_energy: {energy.today_energy}")
        print(f"  month_energy: {energy.month_energy}")
        
        # Check if there's a to_dict method
        if hasattr(energy, 'to_dict'):
            print(f"\nEnergy as dict:")
            energy_dict = energy.to_dict()
            for key, val in energy_dict.items():
                print(f"  {key}: {val}")
        
        return True
        
    except Exception as e:
        print(f"[FAILED] Inspection failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Inspect Server plug methods."""
    print("="*60)
    print("Tapo P115 Plug Methods Inspection")
    print("="*60)
    
    # Inspect Server plug
    success = await inspect_plug_methods("192.168.0.38", "Server")
    
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

