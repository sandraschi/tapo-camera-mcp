import logging
import urllib.parse
from typing import TYPE_CHECKING, Any, Dict

import aiohttp
from fastapi import APIRouter, HTTPException, Query, Request, Response
from fastapi.responses import StreamingResponse

from ...mcp_client import call_mcp_tool

if TYPE_CHECKING:
    from ...core.server import TapoCameraServer

# Import Ring integration if available
try:
    from tapo_camera_mcp.api.ring import RingCameraIntegration
except ImportError:
    RingCameraIntegration = None

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/cameras", tags=["cameras"])


def get_camera_server() -> "TapoCameraServer":
    """Get the singleton CameraServer instance."""
    # This assumes CameraServer is a singleton or accessible via a global/common module.
    # Since CameraServer is typically instantiated in server.py, we might need a way to access it.
    # However, existing api/system.py uses 'CameraServer' but how does it get the instance?
    # In server.py it passes `self` or access globals?
    # Actually, most existing API modules in this project seem to import singletons or use simple logic.
    # But server.py INSTANTIATES CameraServer.
    # We might need a dependency injection or singleton pattern.
    # Let's check how other modules access camera list.
    # existing modules like 'onvif.py' or 'ptz.py' might define routes that take 'request: Request'.
    # In server.py, routes are methods of `TapoCameraMCPServer` which has `self`.
    # To move to APIRouter, we need access to the `server` instance.
    # We can attach the server instance to `app.state.server`.
    # I will assume `request.app.state.server` is available (I will update server.py to set it).


@router.get("", response_model=Dict[str, Any])
async def get_cameras(request: Request):
    """Get all available cameras and their status."""
    cameras = []

    # Get cameras from camera manager directly
    try:
        from ...core.server import TapoCameraServer
        server = await TapoCameraServer.get_instance()

        if hasattr(server, "camera_manager") and server.camera_manager:
            for camera_name, camera in server.camera_manager.cameras.items():
                try:
                    status = await camera.get_status()
                    cameras.append(
                        {
                            "id": camera_name,
                            "name": camera_name,
                            "type": camera.config.type.value if hasattr(camera.config, "type") else "unknown",
                            "status": "online" if status.get("connected", False) else "offline",
                            "model": status.get("model", "Unknown"),
                            "firmware": status.get("firmware", "Unknown"),
                            "streaming": status.get("streaming", False),
                            "stream_url": f"/api/cameras/{urllib.parse.quote(camera_name)}/stream",
                            "snapshot_url": f"/api/cameras/{urllib.parse.quote(camera_name)}/snapshot",
                        }
                    )
                except Exception as e:
                    logger.warning(f"Failed to get status for camera {camera_name}: {e}")
                    cameras.append(
                        {
                            "id": camera_name,
                            "name": camera_name,
                            "type": "unknown",
                            "status": "error",
                            "error": str(e),
                            "stream_url": f"/api/cameras/{urllib.parse.quote(camera_name)}/stream",
                            "snapshot_url": f"/api/cameras/{urllib.parse.quote(camera_name)}/snapshot",
                        }
                    )

    except Exception as e:
        logger.exception(f"Error getting cameras from camera manager: {e}")

    # Add Ring cameras
    try:
        from ...integrations.ring_client import get_ring_client, init_ring_client
        from ...config import get_config
        import asyncio

        ring_client = get_ring_client()
        if not ring_client or not ring_client.is_initialized:
            # Try to initialize Ring client
            config = get_config()
            ring_cfg = config.get("ring", {})
            if ring_cfg.get("enabled"):
                email = ring_cfg.get("email")
                password = ring_cfg.get("password")
                token_file = ring_cfg.get("token_file", "ring_token.cache")
                cache_ttl = ring_cfg.get("cache_ttl", 60)

                if email:
                    try:
                        ring_client = await init_ring_client(
                            email=email, password=password, token_file=token_file, cache_ttl=cache_ttl
                        )
                        logger.info("Ring client initialized in API")
                    except Exception as init_e:
                        logger.debug(f"Failed to initialize Ring client in API: {init_e}")

        if ring_client and ring_client.is_initialized:
            doorbells = await asyncio.wait_for(ring_client.get_doorbells(), timeout=3.0)
            for doorbell in doorbells:
                ring_camera = {
                    "id": f"ring_{doorbell.id}",
                    "name": f"Ring {doorbell.device_type}",
                    "type": "ring",
                    "status": "online" if doorbell.is_online else "offline",
                    "model": doorbell.device_type,
                    "firmware": doorbell.extra_data.get("firmware", "N/A"),
                    "battery_life": doorbell.battery_level,
                    "streaming": True,
                    "capture_capable": True,
                    "stream_url": f"/api/cameras/{urllib.parse.quote(f'ring_{doorbell.id}')}/stream",
                    "snapshot_url": f"/api/cameras/{urllib.parse.quote(f'ring_{doorbell.id}')}/snapshot",
                }
                cameras.append(ring_camera)
                logger.info(f"Added Ring camera to API: {ring_camera['name']}")
    except Exception as e:
        logger.debug(f"Could not add Ring cameras to API: {e}")

    return {"cameras": cameras, "count": len(cameras)}


@router.get("/status")
async def get_cameras_status(request: Request):
    """Get detailed status of all cameras."""
    try:
        # Get cameras status via MCP
        result = await call_mcp_tool("camera_management", {"action": "list"})
        cameras = result.get("cameras", [])
        tapo_count = sum(1 for cam in cameras if cam.get("type") == "tapo")
        total_active = sum(1 for cam in cameras if cam.get("status") == "online")

        return {
            "tapo_count": tapo_count,
            "total_active": total_active,
            "system_status": "nominal",
        }
    except Exception as e:
        logger.exception(f"Error getting camera status via MCP: {e}")
        return {
            "tapo_count": 0,
            "total_active": 0,
            "system_status": "error",
        }


@router.get("/{camera_id}/stream")
async def get_camera_stream(request: Request, camera_id: str):
    """Get MJPEG stream for a camera."""
    server = request.app.state.server
    decoded_id = urllib.parse.unquote(camera_id)

    # Ring - WebRTC streaming not supported via HTTP
    if decoded_id.startswith("ring_"):
        raise HTTPException(status_code=501, detail="Ring cameras use WebRTC streaming, not supported via HTTP API")

    # Get camera from manager
    try:
        camera = await server.camera_manager.get_camera(decoded_id)
        if not camera:
            raise HTTPException(status_code=404, detail=f"Camera '{decoded_id}' not found")

        # For Windows cameras, proxy to Windows camera server
        if hasattr(camera, '_windows_server_url'):
            stream_url = await camera.get_stream_url()
            if stream_url:
                # Proxy the stream from Windows camera server
                async def stream_generator():
                    try:
                        async with aiohttp.ClientSession() as session:
                            async with session.get(stream_url) as response:
                                if response.status == 200:
                                    async for chunk in response.content.iter_chunked(8192):
                                        yield chunk
                    except Exception as e:
                        logger.error(f"Error streaming from Windows camera server: {e}")
                        return

                return StreamingResponse(
                    stream_generator(),
                    media_type="multipart/x-mixed-replace; boundary=frame"
                )

        # For other cameras, try to get stream URL and proxy
        stream_url = await camera.get_stream_url()
        if stream_url:
            # Proxy the MJPEG stream
            async def stream_generator():
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(stream_url) as response:
                            if response.status == 200:
                                async for chunk in response.content.iter_chunked(8192):
                                    yield chunk
                except Exception as e:
                    logger.error(f"Error streaming camera {decoded_id}: {e}")
                    return

            return StreamingResponse(
                stream_generator(),
                media_type="multipart/x-mixed-replace; boundary=frame"
            )

        # Fallback: try to generate frames directly if camera has the method
        if hasattr(camera, 'generate_frames'):
            stream_generator = camera.generate_frames()
            return StreamingResponse(
                stream_generator, media_type="multipart/x-mixed-replace; boundary=frame"
            )

    except Exception as e:
        logger.error(f"Error getting camera stream for {decoded_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get camera stream: {str(e)}")

    raise HTTPException(status_code=404, detail=f"No streaming method available for camera '{decoded_id}'")


@router.get("/{camera_id}/snapshot")
async def get_camera_snapshot(request: Request, camera_id: str):
    """Get a single snapshot from the camera."""
    decoded_id = urllib.parse.unquote(camera_id)

    try:
        # Get snapshot via MCP
        result = await call_mcp_tool(
            "camera_control", {"action": "capture_image", "camera_name": decoded_id}
        )
        image_data = result.get("image_data")

        if not image_data:
            raise HTTPException(status_code=404, detail="Snapshot not available")

        return Response(content=image_data, media_type="image/jpeg")
    except Exception as e:
        logger.exception(f"Error getting snapshot via MCP: {e}")
        raise HTTPException(status_code=500, detail="Failed to capture snapshot")


def _parse_ptz_action(action: str) -> Dict[str, Any]:
    """Parse PTZ action string into MCP parameters."""
    action_map = {
        "pan_left": {"pan": -0.5, "tilt": 0.0, "zoom": 0.0},
        "pan_right": {"pan": 0.5, "tilt": 0.0, "zoom": 0.0},
        "tilt_up": {"pan": 0.0, "tilt": 0.3, "zoom": 0.0},
        "tilt_down": {"pan": 0.0, "tilt": -0.3, "zoom": 0.0},
        "zoom_in": {"pan": 0.0, "tilt": 0.0, "zoom": 0.2},
        "zoom_out": {"pan": 0.0, "tilt": 0.0, "zoom": -0.2},
    }
    return action_map.get(action, {"pan": 0.0, "tilt": 0.0, "zoom": 0.0})


@router.post("/{camera_id}/control")
async def control_camera(
    request: Request,
    camera_id: str,
    action: str = Query(..., description="pan_left, pan_right, tilt_up, tilt_down"),
):
    """Control PTZ features."""
    decoded_id = urllib.parse.unquote(camera_id)

    try:
        # Control camera via MCP
        ptz_params = _parse_ptz_action(action)
        await call_mcp_tool(
            "ptz_management", {"action": "move", "camera_name": decoded_id, **ptz_params}
        )
        return {"status": "success", "action": action}
    except Exception as e:
        logger.exception(f"Error controlling camera via MCP: {e}")
        raise HTTPException(status_code=500, detail="Control command failed")
