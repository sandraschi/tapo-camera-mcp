"""Test different PTZ speed values for Tapo C200."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tapo_camera_mcp.core.server import TapoCameraServer


async def test_ptz_speeds(camera_id: str):
    """Test different PTZ speed values."""
    print(f"\n{'='*60}")
    print(f"Testing PTZ speeds for camera: {camera_id}")
    print(f"{'='*60}")

    try:
        # Get server instance
        server = await TapoCameraServer.get_instance()

        # Get camera
        camera = server.camera_manager.cameras.get(camera_id)
        if not camera:
            print(f"[ERROR] Camera {camera_id} not found")
            return

        print(f"[OK] Found camera: {camera.config.name}")

        # Test different speed values
        test_speeds = [0.1, 0.2, 0.3, 0.5, 0.7, 1.0]

        for speed in test_speeds:
            print(f"\n[TEST] Testing speed: {speed}")
            try:
                # Move right
                print(f"   Moving RIGHT at speed {speed} for 2 seconds...")
                await camera.ptz_move(pan=speed, tilt=0, zoom=0)
                await asyncio.sleep(2.0)
                await camera.ptz_stop()

                # Wait a moment
                await asyncio.sleep(0.5)

                # Move left to return
                print(f"   Moving LEFT at speed {speed} for 2 seconds...")
                await camera.ptz_move(pan=-speed, tilt=0, zoom=0)
                await asyncio.sleep(2.0)
                await camera.ptz_stop()

                print(f"[OK] Speed {speed} test completed")

            except Exception as e:
                print(f"[ERROR] Speed {speed} test failed: {e}")

            # Wait between tests
            await asyncio.sleep(1.0)

        # Test tilt (up/down)
        print("
[TEST] Testing TILT movements..."        try:
            print("   Moving UP for 2 seconds...")
            await camera.ptz_move(pan=0, tilt=0.5, zoom=0)
            await asyncio.sleep(2.0)
            await camera.ptz_stop()

            await asyncio.sleep(0.5)

            print("   Moving DOWN for 2 seconds...")
            await camera.ptz_move(pan=0, tilt=-0.5, zoom=0)
            await asyncio.sleep(2.0)
            await camera.ptz_stop()

            print("[OK] Tilt test completed")

        except Exception as e:
            print(f"[ERROR] Tilt test failed: {e}")

        # Test zoom if available
        print("
[TEST] Testing ZOOM..."        try:
            print("   Zooming IN for 2 seconds...")
            await camera.ptz_move(pan=0, tilt=0, zoom=0.3)
            await asyncio.sleep(2.0)
            await camera.ptz_stop()

            await asyncio.sleep(0.5)

            print("   Zooming OUT for 2 seconds...")
            await camera.ptz_move(pan=0, tilt=0, zoom=-0.3)
            await asyncio.sleep(2.0)
            await camera.ptz_stop()

            print("[OK] Zoom test completed")

        except Exception as e:
            print(f"[ERROR] Zoom test failed: {e}")

        print("
[COMPLETE] PTZ speed testing finished"        print("Recommended speed settings for Tapo C200:")
        print("  - Pan/Tilt: 0.5-0.7 (good balance of speed and control)")
        print("  - Zoom: 0.3 (slower for precision)")

    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Test PTZ speeds on kitchen camera."""
    print("="*60)
    print("PTZ Speed Test - Tapo C200 Camera")
    print("="*60)
    print("This will move the camera - ensure it's safe to do so!")
    print("Press Ctrl+C to stop early")
    print("="*60)

    await test_ptz_speeds("kitchen_cam")


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code or 0)
    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] PTZ speed test cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

















