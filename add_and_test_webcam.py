import asyncio
import sys
sys.path.insert(0, r'D:\Dev\repos\tapo-camera-mcp')

async def add_and_test_webcam():
    from tapo_camera_mcp.core.server import TapoCameraServer

    server = await TapoCameraServer.get_instance()

    # Add webcam
    print('Adding webcam...')
    result = await server.add_camera(
        camera_name='usb_webcam_0',
        camera_type='webcam',
        device_id=0
    )
    print(f'Add result: {result}')

    # Check cameras
    cameras_result = await server.list_cameras()
    cameras = cameras_result.get('cameras', [])
    print(f'Cameras after adding: {len(cameras)}')

    if cameras:
        cam = cameras[0]
        print(f'Camera: {cam["name"]} - Status: {cam["status"]}')

        # Test stream URL
        try:
            camera_obj = await server.camera_manager.get_camera(cam['name'])
            if hasattr(camera_obj, 'get_stream_url'):
                stream_url = await camera_obj.get_stream_url()
                print(f'Local stream URL: {stream_url}')
            else:
                print('No get_stream_url method')
                print(f'Available methods: {[m for m in dir(camera_obj) if not m.startswith("_")]}')
        except Exception as e:
            print(f'Error getting stream URL: {e}')

if __name__ == "__main__":
    asyncio.run(add_and_test_webcam())
