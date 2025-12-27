"""Debug PTZ movement issues."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tapo_camera_mcp.core.server import TapoCameraServer


async def debug_ptz_movement(camera_id: str):
    """Debug PTZ movement for a specific camera."""
    print(f"\n{'='*60}")
    print(f"Debugging PTZ movement for camera: {camera_id}")
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

        # Check if camera is connected
        is_connected = await camera.is_connected()
        print(f"   Connected: {is_connected}")

        if not is_connected:
            print("[ERROR] Camera is not connected - cannot test PTZ")
            return

        # Get current position
        print("\n[TEST] Getting current position...")
        try:
            current_pos = await camera.ptz_get_current_position()
            print(f"[OK] Current position: {current_pos}")
        except Exception as e:
            print(f"[ERROR] Could not get current position: {e}")

        # Test continuous movement
        print("\n[TEST] Testing continuous movement...")
        try:
            print("   Starting RIGHT movement for 3 seconds...")
            await camera.ptz_move(pan=0.8, tilt=0, zoom=0)
            await asyncio.sleep(3.0)
            await camera.ptz_stop()
            print("[OK] Continuous movement test completed")

            # Check new position
            await asyncio.sleep(1.0)
            new_pos = await camera.ptz_get_current_position()
            print(f"[OK] New position after movement: {new_pos}")

        except Exception as e:
            print(f"[ERROR] Continuous movement test failed: {e}")
            import traceback
            traceback.print_exc()

        # Test short movement (like frontend does)
        print("\n[TEST] Testing short movement (like frontend)...")
        try:
            print("   Quick RIGHT movement...")
            await camera.ptz_move(pan=0.8, tilt=0, zoom=0)
            await asyncio.sleep(0.1)  # Very short like frontend
            await camera.ptz_stop()
            print("[OK] Short movement test completed")

            # Check if position changed
            await asyncio.sleep(1.0)
            short_pos = await camera.ptz_get_current_position()
            print(f"[OK] Position after short movement: {short_pos}")

        except Exception as e:
            print(f"[ERROR] Short movement test failed: {e}")

        # Test different speeds
        print("\n[TEST] Testing different speeds...")
        speeds = [0.3, 0.5, 0.8, 1.0]
        for speed in speeds:
            try:
                print(f"   Testing speed {speed}...")
                await camera.ptz_move(pan=speed, tilt=0, zoom=0)
                await asyncio.sleep(1.0)
                await camera.ptz_stop()
                await asyncio.sleep(0.5)
                print(f"[OK] Speed {speed} test completed")
            except Exception as e:
                print(f"[ERROR] Speed {speed} test failed: {e}")

        # Test PTZ service methods directly
        print("\n[TEST] Testing PTZ service methods directly...")
        try:
            if hasattr(camera, '_camera') and camera._camera:
                ptz = camera._camera.get_ptz_service()
                profiles = camera._camera.get_media_profiles()

                if profiles:
                    print("[OK] Found PTZ service and profiles")

                    # Try to get PTZ configuration
                    try:
                        config = ptz.GetConfiguration(profiles[0].token)
                        print(f"[OK] PTZ Configuration: {config}")
                        if hasattr(config, 'DefaultPTZTimeout'):
                            print(f"   Default Timeout: {config.DefaultPTZTimeout}")
                        if hasattr(config, 'PanTiltLimits'):
                            print(f"   PanTilt Limits: {config.PanTiltLimits}")
                    except Exception as e:
                        print(f"[WARN] Could not get PTZ config: {e}")

                    # Test RelativeMove instead of ContinuousMove
                    print("\n[TEST] Testing RelativeMove...")
                    try:
                        request = ptz.create_type("RelativeMove")
                        request.ProfileToken = profiles[0].token
                        request.Translation = {
                            "PanTilt": {"x": 0.1, "y": 0},  # Small relative movement
                            "Zoom": {"x": 0}
                        }
                        ptz.RelativeMove(request)
                        print("[OK] RelativeMove executed")
                    except Exception as e:
                        print(f"[ERROR] RelativeMove failed: {e}")

        except Exception as e:
            print(f"[ERROR] Direct PTZ service test failed: {e}")

    except Exception as e:
        print(f"[ERROR] Debug failed: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Debug kitchen camera PTZ movement."""
    print("="*60)
    print("PTZ Movement Debug Tool - Tapo C200 Camera")
    print("="*60)
    print("This will move the camera - ensure it's safe to do so!")
    print("Press Ctrl+C to stop early")
    print("="*60)

    await debug_ptz_movement("kitchen_cam")


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code or 0)
    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] PTZ debug cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

















