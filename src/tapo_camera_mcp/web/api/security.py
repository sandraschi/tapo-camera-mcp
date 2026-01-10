from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import APIRouter

from ...mcp_client import call_mcp_tool

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/security", tags=["security"])


@router.get("/ring/status", summary="Get Ring integration status")
async def get_ring_status() -> Dict[str, Any]:
    """Get Ring integration status."""
    try:
        result = await call_mcp_tool("ring_management", {"action": "status"})
        return result
    except Exception as e:
        logger.exception("Failed to get Ring status")
        return {"error": str(e)}


@router.get("/nest/status", summary="Get Nest Protect integration status")
async def get_nest_status() -> Dict[str, Any]:
    """Get Nest Protect integration status."""
    try:
        result = await call_mcp_tool("security_management", {"action": "nest_status"})
        return result
    except Exception as e:
        logger.exception("Failed to get Nest status")
        return {"error": str(e)}


@router.get("/nest/devices", summary="Get all Nest Protect devices")
async def get_nest_devices() -> Dict[str, Any]:
    """Get all Nest Protect devices."""
    try:
        result = await call_mcp_tool("security_management", {"action": "nest_status"})
        return result
    except Exception as e:
        logger.exception("Failed to get Nest devices")
        return {"devices": [], "count": 0, "error": str(e)}


@router.get("/nest/alerts", summary="Get Nest Protect alerts")
async def get_nest_alerts() -> Dict[str, Any]:
    """Get Nest Protect alerts."""
    try:
        result = await call_mcp_tool("security_management", {"action": "nest_alerts"})
        return result
    except Exception as e:
        logger.exception("Failed to get Nest alerts")
        return {"alerts": [], "total_alerts": 0, "error": str(e)}


@router.get("/nest/summary", summary="Get Nest Protect summary")
async def get_nest_summary() -> Dict[str, Any]:
    """Get Nest Protect summary."""
    try:
        result = await call_mcp_tool("security_management", {"action": "nest_status"})
        return result
    except Exception as e:
        logger.exception("Failed to get Nest summary")
        return {"initialized": False, "error": str(e)}
