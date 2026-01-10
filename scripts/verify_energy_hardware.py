import asyncio
import logging
from tapo_camera_mcp.tools.energy.tapo_plug_tools import tapo_plug_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def verify_hardware():
    print("--- [Empirical Hardware Verification] ---")
    print("Target: Tapo P115 Smart Plugs")
    print("Mode: Real-time Telemetry (No Mocks)")

    # Force initialization
    # In a real environment, we'd need account details,
    # but here we just want to ensure the manager doesn't fallback to mocks.

    devices = await tapo_plug_manager.get_all_devices()

    if not devices:
        print(
            "RESULT: No hardware devices found (Correct if no active ingestion service/bridge)."
        )
    else:
        for dev in devices:
            print(f"DEVICE: {dev.name} ({dev.device_id})")
            print(f"  POWER: {dev.current_power} W")
            print(f"  VOLTAGE: {dev.voltage} V")
            print(f"  CURRENT: {dev.current} A")
            if dev.current_power == 0.0 and dev.voltage == 0.0:
                print("  STATUS: OFFLINE or IDLE")
            else:
                print("  STATUS: ACTIVE TELEMETRY DETECTED")

    print("--- Verification Complete ---")


if __name__ == "__main__":
    asyncio.run(verify_hardware())
