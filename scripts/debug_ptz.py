"""Debug PTZ functionality for Tapo C200 cameras."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tapo_camera_mcp.core.server import TapoCameraServer


async def debug_ptz_capabilities(camera_id: str):
    """Debug PTZ capabilities for a specific camera."""
    print(f"\n{'='*60}")
    print(f"Debugging PTZ for camera: {camera_id}")
    print(f"{'='*60}")

    try:
        # Get server instance
        server = await TapoCameraServer.get_instance()

        # Get camera manager
        if not hasattr(server, "camera_manager") or not server.camera_manager:
            print("[ERROR] No camera manager available")
            return

        # Get camera
        camera = server.camera_manager.cameras.get(camera_id)
        if not camera:
            print(f"[ERROR] Camera {camera_id} not found")
            return

        print(f"[OK] Found camera: {camera}")
        print(f"   Type: {camera.config.type}")
        print(f"   Name: {camera.config.name}")

        # Check if camera is connected
        is_connected = await camera.is_connected()
        print(f"   Connected: {is_connected}")

        if not is_connected:
            print("[ERROR] Camera is not connected - cannot test PTZ")
            return

        # Get camera status to check PTZ capability
        status = await camera.get_status()
        print(f"\n[STATUS] Camera Status:")
        print(f"   PTZ Capable: {status.get('ptz_capable', False)}")
        print(f"   Model: {status.get('model', 'Unknown')}")
        print(f"   Manufacturer: {status.get('manufacturer', 'Unknown')}")

        # Check if camera has PTZ methods
        print(f"\n[STATUS] PTZ Methods Available:")
        ptz_methods = ['ptz_move', 'ptz_stop', 'ptz_go_to_preset', 'ptz_get_presets', 'ptz_go_home']
        for method in ptz_methods:
            has_method = hasattr(camera, method)
            print(f"   {method}: {'YES' if has_method else 'NO'}")

        if not status.get('ptz_capable', False):
            print("[ERROR] Camera reports as not PTZ capable - cannot test PTZ functions")
            return

        # Test PTZ service connection
        print("\n[TEST] Testing PTZ Service Connection...")
        try:
            # Try to access the underlying ONVIF PTZ service
            if hasattr(camera, '_camera') and camera._camera:
                ptz_service = camera._camera.get_ptz_service()
                print("[OK] PTZ service accessible")

                # Get PTZ status
                profiles = camera._camera.get_media_profiles()
                if profiles:
                    print(f"[OK] Found {len(profiles)} media profiles")
                    profile = profiles[0]

                    # Try to get PTZ configuration
                    try:
                        ptz_config = ptz_service.GetConfiguration(profile.token)
                        print(f"[OK] PTZ Configuration retrieved")
                        print(f"   DefaultTimeout: {getattr(ptz_config, 'DefaultTimeout', 'N/A')}")
                        print(f"   PanTiltLimits: {getattr(ptz_config, 'PanTiltLimits', 'N/A')}")
                        print(f"   ZoomLimits: {getattr(ptz_config, 'ZoomLimits', 'N/A')}")
                    except Exception as e:
                        print(f"[WARN] Could not get PTZ config: {e}")

                    # Try to get PTZ status
                    try:
                        ptz_status = ptz_service.GetStatus(profile.token)
                        print(f"[OK] PTZ Status retrieved")
                        if hasattr(ptz_status, 'Position'):
                            pos = ptz_status.Position
                            if hasattr(pos, 'PanTilt'):
                                print(f"   Current Pan: {getattr(pos.PanTilt, 'x', 'N/A')}")
                                print(f"   Current Tilt: {getattr(pos.PanTilt, 'y', 'N/A')}")
                            if hasattr(pos, 'Zoom'):
                                print(f"   Current Zoom: {getattr(pos.Zoom, 'x', 'N/A')}")
                    except Exception as e:
                        print(f"[WARN] Could not get PTZ status: {e}")

                else:
                    print("[ERROR] No media profiles found")

            else:
                print("[ERROR] Cannot access underlying ONVIF camera object")

        except Exception as e:
            print(f"[ERROR] PTZ service connection failed: {e}")

        # Test small PTZ movement
        print("\n[TEST] Testing Small PTZ Movement...")
        try:
            # Move right for 1 second
            print("   Moving RIGHT for 1 second (speed=0.3)...")
            await camera.ptz_move(pan=0.3, tilt=0, zoom=0)  # Small pan right
            await asyncio.sleep(1.0)
            await camera.ptz_stop()
            print("[OK] Small PTZ movement test completed")

        except Exception as e:
            print(f"[ERROR] PTZ movement test failed: {e}")
            import traceback
            traceback.print_exc()

        # Test presets
        print("\n[TEST] Testing PTZ Presets...")
        try:
            if hasattr(camera, 'ptz_get_presets'):
                presets = await camera.ptz_get_presets()
                print(f"[OK] Found {len(presets)} presets")
                for preset in presets[:3]:  # Show first 3
                    print(f"   - {preset.get('name', 'Unknown')}: {preset.get('token', 'Unknown')}")
            else:
                print("[ERROR] ptz_get_presets method not available")

        except Exception as e:
            print(f"[ERROR] Preset retrieval failed: {e}")

    except Exception as e:
        print(f"[ERROR] Debug failed: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Debug kitchen camera PTZ."""
    print("="*60)
    print("PTZ Debug Tool - Tapo C200 Camera")
    print("="*60)

    await debug_ptz_capabilities("kitchen_cam")


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
