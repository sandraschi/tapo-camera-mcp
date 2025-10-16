#!/usr/bin/env python3
import sys

sys.path.insert(0, "src")
import asyncio


async def main():
    from tapo_camera_mcp.core.server import TapoCameraServer

    server = await TapoCameraServer.get_instance()
    cameras = await server.camera_manager.list_cameras()

    print(f"Cameras in server: {len(cameras)}")
    for cam in cameras:
        print(f"  - {cam.get('name', 'unknown')}: {cam.get('status', 'unknown')}")


if __name__ == "__main__":
    asyncio.run(main())


