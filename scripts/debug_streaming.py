"""Debug camera streaming issues."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tapo_camera_mcp.core.server import TapoCameraServer


async def debug_camera_streaming(camera_id: str):
    """Debug streaming issues for a specific camera."""
    print(f"\n{'='*60}")
    print(f"Debugging streaming for camera: {camera_id}")
    print(f"{'='*60}")

    try:
        # Get server instance
        server = await TapoCameraServer.get_instance()

        # Get camera manager
        if not hasattr(server, "camera_manager") or not server.camera_manager:
            print("❌ No camera manager available")
            return

        # Get camera
        camera = server.camera_manager.cameras.get(camera_id)
        if not camera:
            print(f"❌ Camera {camera_id} not found")
            return

        print(f"[OK] Found camera: {camera}")
        print(f"   Type: {camera.config.type}")
        print(f"   Name: {camera.config.name}")

        # Check if camera is connected
        is_connected = await camera.is_connected()
        print(f"   Connected: {is_connected}")

        if not is_connected:
            print("[ERROR] Camera is not connected - cannot stream")
            return

        # Try to get stream URL
        print("\n[DEBUG] Testing get_stream_url()...")
        try:
            stream_url = await asyncio.wait_for(camera.get_stream_url(), timeout=15.0)
            if stream_url:
                print(f"[OK] Got stream URL: {stream_url[:50]}...")
            else:
                print("[ERROR] get_stream_url() returned None")
        except asyncio.TimeoutError:
            print("[ERROR] get_stream_url() timed out (15s)")
        except Exception as e:
            print(f"[ERROR] get_stream_url() failed: {e}")
            import traceback
            traceback.print_exc()

        # Test snapshot (should work if camera is online)
        print("\n[DEBUG] Testing snapshot...")
        try:
            snapshot = await camera.get_snapshot()
            if snapshot:
                print(f"[OK] Snapshot successful (size: {len(snapshot)} bytes)")
            else:
                print("[ERROR] Snapshot returned None")
        except Exception as e:
            print(f"[ERROR] Snapshot failed: {e}")

    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Debug kitchen camera streaming."""
    print("="*60)
    print("Camera Streaming Debug Tool")
    print("="*60)

    await debug_camera_streaming("kitchen_cam")


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code or 0)
    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Debug cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
