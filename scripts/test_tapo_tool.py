#!/usr/bin/env python3
"""Test the unified tapo tool."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


# Import the actual function
from tapo_camera_mcp.tools.portmanteau.tapo_control import tapo

print("Testing tapo tool...\n")


async def test_action(action: str, **kwargs):
    """Test a tapo action."""
    print(f"Testing: tapo(action='{action}', {kwargs})")
    try:
        result = await tapo(action=action, **kwargs)
        if result.get("success"):
            data = result.get("data", {})
            if "lights" in data:
                print(f"  [OK] Found {data.get('count', 0)} lights")
                for light in data.get("lights", [])[:3]:
                    print(f"    - {light.get('name')} (ID: {light.get('light_id')}) - {'ON' if light.get('on') else 'OFF'}")
            elif "devices" in data:
                print(f"  [OK] Found {data.get('count', 0)} devices")
                for device in data.get("devices", [])[:3]:
                    print(f"    - {device.get('name')} (ID: {device.get('device_id')}) - {'ON' if device.get('power_state') else 'OFF'}")
            else:
                print(f"  [OK] Success: {result}")
        else:
            print(f"  [ERROR] Error: {result.get('error')}")
    except Exception as e:
        print(f"  [EXCEPTION] Exception: {e}")
    print()


async def main():
    # Test list lights
    await test_action("list lights")

    # Test list plugs
    await test_action("list plugs")


if __name__ == "__main__":
    asyncio.run(main())

