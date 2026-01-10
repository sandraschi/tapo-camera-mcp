"""PTZ (Pan-Tilt-Zoom) API endpoints for ONVIF cameras."""

import logging
from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ...mcp_client import call_mcp_tool

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


@router.post("/move", response_model=Dict[str, Any])
async def ptz_move(request: PTZMoveRequest) -> Dict[str, Any]:
    """Start continuous PTZ movement via MCP.

    Values range from -1.0 to 1.0:
    - pan: negative = left, positive = right
    - tilt: negative = down, positive = up
    - zoom: negative = zoom out, positive = zoom in
    """
    # Validate and clamp values to prevent issues
    pan = max(-1.0, min(1.0, request.pan))
    tilt = max(-1.0, min(1.0, request.tilt))
    zoom = max(-1.0, min(1.0, request.zoom))

    # For Tapo C200, ensure minimum movement threshold
    # Very small values might not register
    min_threshold = 0.05
    if abs(pan) < min_threshold and abs(tilt) < min_threshold and abs(zoom) < min_threshold:
        # If all values are too small, stop movement instead
        try:
            result = await call_mcp_tool(
                "ptz_management", {"action": "stop", "camera_name": request.camera_name}
            )
            if result.get("success"):
                return {
                    "success": True,
                    "message": "PTZ stopped (values too small for movement)",
                }
        except Exception as e:
            logger.warning(f"Failed to stop PTZ movement: {e}")

    try:
        result = await call_mcp_tool(
            "ptz_management",
            {
                "action": "move",
                "camera_name": request.camera_name,
                "pan": pan,
                "tilt": tilt,
                "zoom": zoom,
                "speed": 5,
            },
        )
        if result.get("success"):
            return {
                "success": True,
                "message": f"PTZ moving: pan={pan:.3f}, tilt={tilt:.3f}, zoom={zoom:.3f}",
            }
        raise HTTPException(status_code=400, detail=result.get("error", "PTZ move failed"))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("PTZ move failed via MCP")
        raise HTTPException(status_code=500, detail=f"PTZ move failed: {e!s}")


@router.post("/stop/{camera_name}", response_model=Dict[str, Any])
async def ptz_stop(camera_name: str) -> Dict[str, Any]:
    """Stop all PTZ movement via MCP."""
    try:
        result = await call_mcp_tool(
            "ptz_management", {"action": "stop", "camera_name": camera_name}
        )
        if result.get("success"):
            return {"success": True, "message": "PTZ movement stopped"}
        raise HTTPException(status_code=400, detail=result.get("error", "PTZ stop failed"))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("PTZ stop failed via MCP")
        raise HTTPException(status_code=500, detail=f"PTZ stop failed: {e!s}")


@router.get("/presets/{camera_name}", response_model=Dict[str, Any])
async def get_presets(camera_name: str) -> Dict[str, Any]:
    """Get list of PTZ presets for a camera via MCP."""
    try:
        result = await call_mcp_tool(
            "ptz_management", {"action": "list_presets", "camera_name": camera_name}
        )
        if result.get("success"):
            return {"success": True, "presets": result.get("presets", [])}
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to get presets"))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to get PTZ presets via MCP")
        raise HTTPException(status_code=500, detail=f"Failed to get PTZ presets: {e!s}")


@router.post("/preset/goto", response_model=Dict[str, Any])
async def goto_preset(request: PTZPresetRequest) -> Dict[str, Any]:
    """Move camera to a saved preset position via MCP."""
    try:
        result = await call_mcp_tool(
            "ptz_management",
            {
                "action": "recall_preset",
                "camera_name": request.camera_name,
                "preset_name": request.preset_token,
            },
        )
        if result.get("success"):
            return {
                "success": True,
                "message": f"Moving to preset: {request.preset_token}",
            }
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to recall preset"))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to go to PTZ preset via MCP")
        raise HTTPException(status_code=500, detail=f"Failed to go to PTZ preset: {e!s}")


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


@router.post("/home", response_model=Dict[str, Any])
async def ptz_home(request: PTZHomeRequest) -> Dict[str, Any]:
    """Move camera to home position via MCP."""
    try:
        result = await call_mcp_tool(
            "ptz_management", {"action": "home", "camera_name": request.camera_name}
        )
        if result.get("success"):
            return {"success": True, "message": "Moving to home position"}
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to go to home"))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to go to PTZ home via MCP")
        raise HTTPException(status_code=500, detail=f"Failed to go to PTZ home: {e!s}")
