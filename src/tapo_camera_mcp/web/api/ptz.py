"""PTZ (Pan-Tilt-Zoom) API endpoints for ONVIF cameras."""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ptz", tags=["ptz"])


class PTZMoveRequest(BaseModel):
    """Request model for PTZ movement."""

    camera_name: str
    pan: float = 0.0  # -1.0 to 1.0 (left to right)
    tilt: float = 0.0  # -1.0 to 1.0 (down to up)
    zoom: float = 0.0  # -1.0 to 1.0 (out to in)


class PTZPresetRequest(BaseModel):
    """Request model for PTZ preset operations."""

    camera_name: str
    preset_token: str


async def _get_camera(camera_name: str):
    """Get camera instance by name."""
    from tapo_camera_mcp.core.server import TapoCameraServer

    server = await TapoCameraServer.get_instance()
    camera = await server.camera_manager.get_camera(camera_name)
    if not camera:
        raise HTTPException(status_code=404, detail=f"Camera not found: {camera_name}")
    return camera


@router.post("/move")
async def ptz_move(request: PTZMoveRequest):
    """Start continuous PTZ movement.
    
    Values range from -1.0 to 1.0:
    - pan: negative = left, positive = right
    - tilt: negative = down, positive = up
    - zoom: negative = zoom out, positive = zoom in
    """
    camera = await _get_camera(request.camera_name)

    # Check if camera supports PTZ
    if not hasattr(camera, "ptz_move"):
        raise HTTPException(
            status_code=400, detail="Camera does not support PTZ controls"
        )

    try:
        await camera.ptz_move(pan=request.pan, tilt=request.tilt, zoom=request.zoom)
        return {
            "success": True,
            "message": f"PTZ moving: pan={request.pan}, tilt={request.tilt}, zoom={request.zoom}",
        }
    except Exception as e:
        logger.exception("PTZ move failed")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/stop/{camera_name}")
async def ptz_stop(camera_name: str):
    """Stop all PTZ movement."""
    camera = await _get_camera(camera_name)

    if not hasattr(camera, "ptz_stop"):
        raise HTTPException(
            status_code=400, detail="Camera does not support PTZ controls"
        )

    try:
        await camera.ptz_stop()
        return {"success": True, "message": "PTZ movement stopped"}
    except Exception as e:
        logger.exception("PTZ stop failed")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/presets/{camera_name}")
async def get_presets(camera_name: str):
    """Get list of PTZ presets for a camera."""
    camera = await _get_camera(camera_name)

    if not hasattr(camera, "ptz_get_presets"):
        raise HTTPException(
            status_code=400, detail="Camera does not support PTZ presets"
        )

    try:
        presets = await camera.ptz_get_presets()
        return {"success": True, "presets": presets}
    except Exception as e:
        logger.exception("Failed to get PTZ presets")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/preset/goto")
async def goto_preset(request: PTZPresetRequest):
    """Move camera to a saved preset position."""
    camera = await _get_camera(request.camera_name)

    if not hasattr(camera, "ptz_go_to_preset"):
        raise HTTPException(
            status_code=400, detail="Camera does not support PTZ presets"
        )

    try:
        await camera.ptz_go_to_preset(request.preset_token)
        return {
            "success": True,
            "message": f"Moving to preset: {request.preset_token}",
        }
    except Exception as e:
        logger.exception("Failed to go to PTZ preset")
        raise HTTPException(status_code=500, detail=str(e)) from e


# Convenience endpoints for simple directional control
@router.post("/up/{camera_name}")
async def ptz_up(camera_name: str, speed: float = 0.5):
    """Tilt camera up."""
    return await ptz_move(PTZMoveRequest(camera_name=camera_name, tilt=speed))


@router.post("/down/{camera_name}")
async def ptz_down(camera_name: str, speed: float = 0.5):
    """Tilt camera down."""
    return await ptz_move(PTZMoveRequest(camera_name=camera_name, tilt=-speed))


@router.post("/left/{camera_name}")
async def ptz_left(camera_name: str, speed: float = 0.5):
    """Pan camera left."""
    return await ptz_move(PTZMoveRequest(camera_name=camera_name, pan=-speed))


@router.post("/right/{camera_name}")
async def ptz_right(camera_name: str, speed: float = 0.5):
    """Pan camera right."""
    return await ptz_move(PTZMoveRequest(camera_name=camera_name, pan=speed))


@router.post("/zoom-in/{camera_name}")
async def ptz_zoom_in(camera_name: str, speed: float = 0.3):
    """Zoom camera in."""
    return await ptz_move(PTZMoveRequest(camera_name=camera_name, zoom=speed))


@router.post("/zoom-out/{camera_name}")
async def ptz_zoom_out(camera_name: str, speed: float = 0.3):
    """Zoom camera out."""
    return await ptz_move(PTZMoveRequest(camera_name=camera_name, zoom=-speed))


class PTZHomeRequest(BaseModel):
    """Request model for PTZ home."""
    camera_name: str


@router.post("/home")
async def ptz_home(request: PTZHomeRequest):
    """Move camera to home position."""
    camera = await _get_camera(request.camera_name)

    # Try ptz_go_home first, then fall back to preset
    if hasattr(camera, "ptz_go_home"):
        try:
            await camera.ptz_go_home()
            return {"success": True, "message": "Moving to home position"}
        except Exception as e:
            logger.warning(f"ptz_go_home failed: {e}, trying home preset")

    # Try home preset
    if hasattr(camera, "ptz_go_to_preset"):
        try:
            await camera.ptz_go_to_preset("1")  # Preset 1 is typically home
            return {"success": True, "message": "Moving to home preset"}
        except Exception:
            pass

    # Just stop if nothing else works
    if hasattr(camera, "ptz_stop"):
        await camera.ptz_stop()
        return {"success": True, "message": "Stopped PTZ (no home support)"}

    raise HTTPException(status_code=400, detail="Camera does not support PTZ home")
