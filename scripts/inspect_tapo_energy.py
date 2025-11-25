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
        
        # Get energy usage
        energy = await plug.get_energy_usage()
        
        print(f"\nEnergy object type: {type(energy)}")
        print(f"\nEnergy object attributes:")
        print(f"  dir(): {[attr for attr in dir(energy) if not attr.startswith('_')]}")
        
        print(f"\nTrying to access common attributes:")
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
            print(f"\nEnergy object __dict__:")
            for key, val in energy.__dict__.items():
                print(f"  {key}: {val}")
        
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

