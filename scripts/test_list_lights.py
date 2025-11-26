#!/usr/bin/env python3
"""Test listing lights via lighting management."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tapo_camera_mcp.tools.lighting.hue_tools import hue_manager


async def main():
    await hue_manager.initialize()
    lights = await hue_manager.get_all_lights()
    
    print(f"\nFound {len(lights)} lights:\n")
    print("=" * 60)
    
    for i, light in enumerate(lights, 1):
        status = "ON" if light.on else "OFF"
        reachable = "[OK]" if light.reachable else "[X]"
        print(f"{i:2d}. {light.name:30s} (ID: {light.light_id:3s}) - {status:3s} - {light.brightness_percent:3d}% - {reachable}")


if __name__ == "__main__":
    asyncio.run(main())

