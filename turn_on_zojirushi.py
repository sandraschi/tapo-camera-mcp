"""Turn on Zojirushi hot water dispenser."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path("src")))

from tapo_camera_mcp.ingest.tapo_p115 import TapoP115IngestionService

async def turn_on():
    service = TapoP115IngestionService()
    host = "192.168.0.17"
    
    print("Turning on Zojirushi hot water dispenser...")
    await service.control_device(host, turn_on=True)
    print("[OK] Turned ON")
    
    await asyncio.sleep(2)
    snapshot = await service._fetch_device_snapshot(host)
    if snapshot:
        print(f"State: {'ON' if snapshot.get('power_state') else 'OFF'}")
        print(f"Power: {snapshot.get('current_power')}W")

asyncio.run(turn_on())

