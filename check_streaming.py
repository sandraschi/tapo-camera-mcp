import asyncio
import sys
sys.path.insert(0, r'D:\Dev\repos\tapo-camera-mcp')

async def test_streaming():
    from tapo_camera_mcp.core.server import TapoCameraServer
    server = await TapoCameraServer.get_instance()

    # Get cameras to see what's available
    result = await server.list_cameras()
    cameras = result.get('cameras', [])
    print(f'Available cameras: {len(cameras)}')

    if cameras:
        cam = cameras[0]
        print(f'Camera: {cam["name"]} - Status: {cam["status"]}')

        # Try to get stream URL if available
        try:
            camera_obj = await server.camera_manager.get_camera(cam['name'])
            if hasattr(camera_obj, 'get_stream_url'):
                stream_url = await camera_obj.get_stream_url()
                print(f'Stream URL: {stream_url}')
            else:
                print('No stream_url method available')
                print(f'Available methods: {[m for m in dir(camera_obj) if not m.startswith("_")]}')
        except Exception as e:
            print(f'Error getting stream: {e}')
    else:
        print('No cameras found')

if __name__ == "__main__":
    asyncio.run(test_streaming())
