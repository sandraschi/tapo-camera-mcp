#!/usr/bin/env python3
"""
Test script for Tapo lightstrip effects functionality.
"""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from tapo_camera_mcp.tools.portmanteau.tapo_control import tapo
from tapo_camera_mcp.tools.portmanteau.lighting_management import lighting_management


async def test_effects():
    """Test the effect functionality."""
    print("Testing Tapo lightstrip effects...")

    # Test listing lights
    print("\n1. Testing list lights:")
    result = await tapo(action="list lights")
    print(f"Result: {result}")

    if result.get('success'):
        tapo_lights = [light for light in result['data']['lights'] if light.get('light_type') == 'tapo']
        if tapo_lights:
            test_light_id = tapo_lights[0]['device_id']
            print(f"Found Tapo light: {test_light_id}")

            # Test setting rainbow effect
            print(f"\n2. Testing rainbow effect on {test_light_id}:")
            effect_result = await tapo(action="set effect", light_id=test_light_id, effect="Rainbow")
            print(f"Effect result: {effect_result}")

            # Test with lighting_management tool
            print(f"\n3. Testing with lighting_management tool:")
            lm_result = await lighting_management(action="control_light", light_id=test_light_id, effect="Ocean", on=True)
            print(f"Lighting management result: {lm_result}")

            # Wait a bit
            await asyncio.sleep(2)

            # Turn off
            print(f"\n4. Turning off light:")
            off_result = await tapo(action="turn off light", light_id=test_light_id)
            print(f"Off result: {off_result}")
        else:
            print("No Tapo lights found")
    else:
        print("Failed to list lights")

if __name__ == "__main__":
    asyncio.run(test_effects())