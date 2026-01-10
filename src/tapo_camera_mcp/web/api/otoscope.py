"""Simplified otoscope API endpoints for basic USB camera control."""

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ...mcp_client import call_mcp_tool

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/otoscope", tags=["otoscope"])


class CameraRequest(BaseModel):
    """Base request model for camera operations."""

    camera_name: str


class CaptureImageRequest(CameraRequest):
    """Request model for capturing images."""

    filename: Optional[str] = None


@router.get("/info/{camera_name}", response_model=Dict[str, Any])
async def get_otoscope_info(camera_name: str) -> Dict[str, Any]:
    """Get information about an otoscope camera via MCP."""
    try:
        result = await call_mcp_tool(
            "camera_management", {"action": "info", "camera_name": camera_name}
        )
        if result.get("success"):
            return result.get("data", result)
        raise HTTPException(status_code=404, detail=f"Camera not found: {camera_name}")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to get camera info via MCP")
        raise HTTPException(status_code=500, detail=f"Failed to get camera info: {e!s}")


@router.get("/stream/{camera_name}", response_model=Dict[str, Any])
async def get_otoscope_stream(camera_name: str) -> Dict[str, Any]:
    """Get stream URL for otoscope camera via MCP."""
    try:
        result = await call_mcp_tool(
            "camera_management", {"action": "get_stream_url", "camera_name": camera_name}
        )
        if result.get("success"):
            return result.get("data", result)
        raise HTTPException(status_code=404, detail=f"Camera not found: {camera_name}")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to get stream URL via MCP")
        raise HTTPException(status_code=500, detail=f"Failed to get stream URL: {e!s}")


@router.post("/capture", response_model=Dict[str, Any])
async def capture_image(request: CaptureImageRequest) -> Dict[str, Any]:
    """Capture an image from the otoscope camera via MCP."""
    try:
        result = await call_mcp_tool(
            "camera_management",
            {"action": "capture", "camera_name": request.camera_name, "filename": request.filename},
        )
        if result.get("success"):
            return result.get("data", result)
        raise HTTPException(status_code=500, detail="Failed to capture image")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to capture image via MCP")
        raise HTTPException(status_code=500, detail=f"Failed to capture image: {e!s}")
