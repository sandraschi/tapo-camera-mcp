#!/usr/bin/env python3
"""List all Hue scenes to see what they are."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from collections import defaultdict

from tapo_camera_mcp.tools.lighting.hue_tools import hue_manager


async def main():
    await hue_manager.initialize()
    scenes = await hue_manager.get_all_scenes()

    print(f"\nTotal scenes: {len(scenes)}\n")
    print("=" * 60)

    # Group by room/group
    by_group = defaultdict(list)
    for scene in scenes:
        group = scene.group or "Ungrouped"
        by_group[group].append(scene.name)

    # Print grouped
    for group in sorted(by_group.keys()):
        scenes_list = sorted(by_group[group])
        print(f"\n{group}: {len(scenes_list)} scenes")
        print("-" * 60)
        for name in scenes_list:
            print(f"  • {name}")


if __name__ == "__main__":
    asyncio.run(main())

