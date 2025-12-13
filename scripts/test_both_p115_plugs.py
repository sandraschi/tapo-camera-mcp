"""Test both Tapo P115 plugs: 192.168.0.17 (Living Room) and 192.168.0.137 (Kitchen)."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tapo_camera_mcp.ingest.tapo_p115 import TapoP115IngestionService


async def test_plug(host: str, name: str):
    """Test a single plug connection and get energy data."""
    print(f"\n{'='*60}")
    print(f"Testing {name} (IP: {host})")
    print(f"{'='*60}")

    try:
        service = TapoP115IngestionService()
        snapshot = await service._fetch_device_snapshot(host)

        if snapshot:
            print("[SUCCESS] Connection successful!")
            print("\nDevice Info:")
            print(f"  Device ID: {snapshot.get('device_id')}")
            print(f"  Name: {snapshot.get('name')}")
            print(f"  Location: {snapshot.get('location')}")
            print(f"  Model: {snapshot.get('device_model')}")
            print("\nPower State:")
            print(f"  Power: {'ON' if snapshot.get('power_state') else 'OFF'}")
            print("\nEnergy Monitoring:")
            print(f"  Current Power: {snapshot.get('current_power', 0):.2f} W")
            print(f"  Voltage: {snapshot.get('voltage', 0):.2f} V")
            print(f"  Current: {snapshot.get('current', 0):.3f} A")
            print(f"  Today's Energy: {snapshot.get('daily_energy', 0):.3f} kWh")
            print(f"  Monthly Energy: {snapshot.get('monthly_energy', 0):.2f} kWh")
            print(f"  Last Seen: {snapshot.get('last_seen')}")
            return True
        print("[FAILED] Connection failed - no data returned")
        return False

    except Exception as e:
        print(f"[FAILED] Connection failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Test all plugs."""
    print("="*60)
    print("Tapo P115 Plug Connection Test")
    print("="*60)

    results = []

    # Test Living Room plug (192.168.0.17)
    results.append(await test_plug("192.168.0.17", "Living Room Aircon"))

    # Test Kitchen plug (192.168.0.137)
    results.append(await test_plug("192.168.0.137", "Kitchen Zojirushi"))

    # Test Server plug (192.168.0.38)
    results.append(await test_plug("192.168.0.38", "Server"))

    # Summary
    print(f"\n{'='*60}")
    print("Test Summary")
    print(f"{'='*60}")
    print(f"Living Room (192.168.0.17): {'[PASS]' if results[0] else '[FAIL]'}")
    print(f"Kitchen (192.168.0.137): {'[PASS]' if results[1] else '[FAIL]'}")
    print(f"Server (192.168.0.38): {'[PASS]' if results[2] else '[FAIL]'}")
    print(f"\nOverall: {'[SUCCESS] All tests passed' if all(results) else '[FAILED] Some tests failed'}")

    return 0 if all(results) else 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Test cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

