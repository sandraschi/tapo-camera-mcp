"""Motion detection API for ONVIF cameras."""

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ...mcp_client import call_mcp_tool

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/motion", tags=["motion"])


class MotionSubscriptionRequest(BaseModel):
    """Request to subscribe to motion events."""

    camera_id: str


@router.get("/status", response_model=Dict[str, Any])
async def get_motion_status() -> Dict[str, Any]:
    """Get status of motion detection subscriptions via MCP."""
    try:
        result = await call_mcp_tool("motion_management", {"action": "status"})
        if result.get("success"):
            return result.get("data", {})
        raise HTTPException(
            status_code=500, detail=result.get("error", "Failed to get motion status")
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to get motion status via MCP")
        raise HTTPException(status_code=500, detail=f"Failed to get motion status: {e!s}")


@router.get("/events", response_model=Dict[str, Any])
async def get_motion_events(camera_id: Optional[str] = None, limit: int = 20) -> Dict[str, Any]:
    """Get recent motion events via MCP."""
    try:
        args = {"action": "events", "limit": limit}
        if camera_id:
            args["camera_id"] = camera_id

        result = await call_mcp_tool("motion_management", args)
        if result.get("success"):
            return result.get("data", {})
        raise HTTPException(
            status_code=500, detail=result.get("error", "Failed to get motion events")
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to get motion events via MCP")
        raise HTTPException(status_code=500, detail=f"Failed to get motion events: {e!s}")


@router.post("/subscribe/{camera_id}", response_model=Dict[str, Any])
async def subscribe_to_motion(camera_id: str) -> Dict[str, Any]:
    """Subscribe to motion events from a camera via MCP.

    Note: Not all cameras support ONVIF events. Tapo C200 has limited event support.
    """
    try:
        result = await call_mcp_tool(
            "motion_management", {"action": "subscribe", "camera_id": camera_id}
        )

        if result.get("success"):
            data = result.get("data", {})
            return {
                "success": True,
                "message": data.get("note", f"Subscribed to motion events from {camera_id}"),
                "camera_id": camera_id,
                "subscribed": data.get("subscribed", True),
            }
        error_msg = result.get("error", "Failed to subscribe to motion events")
        if "not found" in error_msg.lower():
            raise HTTPException(status_code=404, detail=error_msg)
        if "not ONVIF" in error_msg.lower() or "only for ONVIF" in error_msg.lower():
            raise HTTPException(status_code=400, detail=error_msg)
        raise HTTPException(status_code=500, detail=error_msg)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to subscribe to motion events for {camera_id} via MCP")
        raise HTTPException(status_code=500, detail=f"Failed to subscribe to motion events: {e!s}")


@router.post("/unsubscribe/{camera_id}", response_model=Dict[str, Any])
async def unsubscribe_from_motion(camera_id: str) -> Dict[str, Any]:
    """Unsubscribe from motion events via MCP."""
    try:
        result = await call_mcp_tool(
            "motion_management", {"action": "unsubscribe", "camera_id": camera_id}
        )

        if result.get("success"):
            data = result.get("data", {})
            return {
                "success": True,
                "message": f"Unsubscribed from {camera_id}",
                "camera_id": camera_id,
                "unsubscribed": data.get("unsubscribed", True),
            }
        raise HTTPException(
            status_code=500,
            detail=result.get("error", "Failed to unsubscribe from motion events"),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to unsubscribe from motion events for {camera_id} via MCP")
        raise HTTPException(
            status_code=500, detail=f"Failed to unsubscribe from motion events: {e!s}"
        )


@router.get("/capabilities", response_model=Dict[str, Any])
async def get_motion_capabilities() -> Dict[str, Any]:
    """Get motion detection capabilities for different camera types via MCP."""
    try:
        result = await call_mcp_tool("motion_management", {"action": "capabilities"})
        if result.get("success"):
            return result.get("data", {})
        raise HTTPException(
            status_code=500, detail=result.get("error", "Failed to get motion capabilities")
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to get motion capabilities via MCP")
        raise HTTPException(status_code=500, detail=f"Failed to get motion capabilities: {e!s}")


@router.post("/test/{camera_id}", response_model=Dict[str, Any])
async def test_motion_support(camera_id: str) -> Dict[str, Any]:
    """Test if a camera supports ONVIF events via MCP."""
    try:
        result = await call_mcp_tool(
            "motion_management", {"action": "test", "camera_id": camera_id}
        )

        if result.get("success"):
            data = result.get("data", {})
            return {
                "camera_id": camera_id,
                "camera_type": data.get("camera_type"),
                "onvif_events_support": data.get("onvif_events_support", False),
                "details": data.get("details", {}),
                "note": data.get("note", ""),
            }
        error_msg = result.get("error", "Failed to test motion support")
        if "not found" in error_msg.lower():
            raise HTTPException(status_code=404, detail=error_msg)
        raise HTTPException(status_code=500, detail=error_msg)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to test motion support for {camera_id} via MCP")
        raise HTTPException(status_code=500, detail=f"Failed to test motion support: {e!s}")
