#!/usr/bin/env python3
"""
Demo script showcasing Tapo Camera MCP features.

Demonstrates:
- ONVIF camera connection
- PTZ controls (pan, tilt, zoom)
- Snapshot capture
- Ring doorbell status
- Camera info display

Usage:
    python scripts/demo.py
    python scripts/demo.py --camera kitchen_cam
    python scripts/demo.py --no-ptz  # Skip PTZ movements
"""

import argparse
import asyncio
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


async def demo_camera_info(camera):
    """Display camera information."""
    print("\n📹 Camera Information")
    print("=" * 50)
    info = await camera.get_info()
    for key, value in info.items():
        if key != "capabilities":
            print(f"  {key}: {value}")
    if "capabilities" in info:
        print("  Capabilities:")
        for cap, enabled in info["capabilities"].items():
            status = "✅" if enabled else "❌"
            print(f"    {status} {cap}")


async def demo_camera_status(camera):
    """Display camera status."""
    print("\n📊 Camera Status")
    print("=" * 50)
    status = await camera.get_status()
    for key, value in status.items():
        print(f"  {key}: {value}")


async def demo_ptz_movements(camera, camera_name: str):
    """Demonstrate PTZ movements."""
    print("\n🎮 PTZ Demo")
    print("=" * 50)

    movements = [
        ("Looking LEFT", -0.3, 0, 0, 1.5),
        ("Looking RIGHT", 0.3, 0, 0, 1.5),
        ("Looking UP", 0, 0.3, 0, 1.5),
        ("Looking DOWN", 0, -0.3, 0, 1.5),
        ("Centering...", 0, 0, 0, 0.5),
        ("Zooming IN", 0, 0, 0.3, 2.0),
        ("Zooming OUT", 0, 0, -0.3, 2.0),
    ]

    for description, pan, tilt, zoom, duration in movements:
        print(f"  🔄 {description}")
        await camera.ptz_move(pan=pan, tilt=tilt, zoom=zoom)
        await asyncio.sleep(duration)
        await camera.ptz_stop()
        await asyncio.sleep(0.3)

    print("  ✅ PTZ demo complete!")


async def demo_snapshot(camera, camera_name: str):
    """Capture and save a snapshot."""
    print("\n📸 Snapshot Demo")
    print("=" * 50)

    snapshot_dir = Path("demo_snapshots")
    snapshot_dir.mkdir(exist_ok=True)

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = snapshot_dir / f"{camera_name}_{timestamp}.jpg"

    print("  Capturing snapshot...")
    image = await camera.capture_still(str(filename))
    print(f"  ✅ Saved: {filename}")
    print(f"  📐 Size: {image.size[0]}x{image.size[1]}")

    return filename


async def demo_ring_status():
    """Show Ring doorbell status."""
    print("\n🔔 Ring Doorbell Status")
    print("=" * 50)

    try:
        from tapo_camera_mcp.integrations.ring_client import get_ring_client

        client = get_ring_client()
        if not client or not client.is_initialized:
            print("  ⚠️  Ring not initialized")
            return

        summary = await client.get_summary()
        print(f"  Initialized: {summary.get('initialized', False)}")
        print(f"  Doorbells: {summary.get('doorbell_count', 0)}")

        doorbells = await client.get_doorbells()
        for db in doorbells:
            print(f"\n  📍 {db.get('name', 'Unknown')}")
            print(f"     Battery: {db.get('battery_life', 'N/A')}%")
            print(f"     WiFi: {db.get('wifi_signal_strength', 'N/A')} dBm")

    except Exception as e:
        print(f"  ❌ Ring error: {e}")


async def demo_all_cameras():
    """List all available cameras."""
    print("\n📷 Available Cameras")
    print("=" * 50)

    try:
        from tapo_camera_mcp.core.server import TapoCameraServer

        server = await TapoCameraServer.get_instance()
        cameras = await server.camera_manager.list_cameras()

        for cam in cameras:
            status = cam.get("status", {})
            connected = status.get("connected", False) if isinstance(status, dict) else False
            icon = "🟢" if connected else "🔴"
            print(f"  {icon} {cam['name']} ({cam['type']})")
            if isinstance(status, dict):
                print(f"     Model: {status.get('model', 'Unknown')}")
                print(f"     Resolution: {status.get('resolution', 'Unknown')}")

    except Exception as e:
        print(f"  ❌ Error listing cameras: {e}")


async def run_demo(camera_name: str = "kitchen_cam", skip_ptz: bool = False):
    """Run the full demo."""
    print("\n" + "=" * 60)
    print("   🏠 Home Security MCP - Feature Demo")
    print("=" * 60)

    # Import camera classes
    from tapo_camera_mcp.camera.base import CameraConfig, CameraType
    from tapo_camera_mcp.camera.onvif_camera import ONVIFBasedCamera
    from tapo_camera_mcp.config import get_config

    # Load config
    config = get_config()
    cameras_config = config.get("cameras", {})

    if camera_name not in cameras_config:
        print(f"\n❌ Camera '{camera_name}' not found in config.yaml")
        print(f"   Available: {list(cameras_config.keys())}")
        return

    cam_config = cameras_config[camera_name]
    cam_config["name"] = camera_name

    # Create camera
    print(f"\n🔌 Connecting to {camera_name}...")
    camera_cfg = CameraConfig(
        name=camera_name,
        type=CameraType(cam_config["type"]),
        params=cam_config["params"]
    )
    camera = ONVIFBasedCamera(camera_cfg)

    try:
        await camera.connect()
        print("   ✅ Connected!")

        # Run demos
        await demo_camera_info(camera)
        await demo_camera_status(camera)

        if not skip_ptz:
            await demo_ptz_movements(camera, camera_name)
        else:
            print("\n⏭️  Skipping PTZ demo (--no-ptz)")

        await demo_snapshot(camera, camera_name)
        await demo_ring_status()
        await demo_all_cameras()

    finally:
        await camera.disconnect()

    print("\n" + "=" * 60)
    print("   ✅ Demo Complete!")
    print("=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Tapo Camera MCP Demo")
    parser.add_argument(
        "--camera", "-c",
        default="kitchen_cam",
        help="Camera name from config.yaml (default: kitchen_cam)"
    )
    parser.add_argument(
        "--no-ptz",
        action="store_true",
        help="Skip PTZ movement demo"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Just list available cameras"
    )

    args = parser.parse_args()

    if args.list:
        asyncio.run(demo_all_cameras())
    else:
        asyncio.run(run_demo(args.camera, args.no_ptz))


if __name__ == "__main__":
    main()

