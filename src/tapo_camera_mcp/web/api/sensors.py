"""
Sensor API endpoints for real-world ingestion data.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ...db import TimeSeriesDB
from ...mcp_client import call_mcp_tool

logger = logging.getLogger(__name__)


class ToggleRequest(BaseModel):
    """Request model for toggling device power state."""

    turn_on: bool

    class Config:
        """Pydantic config."""

        json_schema_extra = {"example": {"turn_on": False}}


router = APIRouter(prefix="/api/sensors", tags=["sensors"])
_db = TimeSeriesDB()  # Initialize database for historical data


def _model_dump(model: Any) -> dict[str, Any]:
    """Serialize Pydantic models across v1/v2."""
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()  # type: ignore[attr-defined]


@router.get("/tapo-p115", summary="List Tapo P115 smart plugs")
async def list_tapo_p115_devices() -> dict[str, Any]:
    """
    Return all Tapo P115 smart plugs with realtime metrics via MCP.
    """
    try:
        result = await call_mcp_tool("energy_management", {"action": "status"})
        if result.get("success"):
            devices = result.get("data", {}).get("devices", [])
            return {"devices": devices, "count": len(devices)}
        return {
            "devices": [],
            "count": 0,
            "error": result.get("error", "Failed to get devices"),
        }
    except Exception as e:
        logger.exception("Failed to list Tapo P115 devices via MCP")
        return {"devices": [], "count": 0, "error": str(e)}


@router.get(
    "/tapo-p115/{device_id}/history",
    summary="Get energy usage history",
)
async def get_tapo_p115_history(
    device_id: str,
    hours: int = Query(24, ge=1, le=168),
) -> dict[str, Any]:
    """
    Retrieve energy usage history for the specified Tapo P115 plug from database.
    """
    try:
        # Check if device exists via MCP
        status_result = await call_mcp_tool(
            "energy_management", {"action": "status", "device_id": device_id}
        )
        if not status_result.get("success"):
            raise HTTPException(status_code=404, detail=f"Device {device_id} not found")

        device_data = status_result.get("data", {})
        device_name = device_data.get("name", device_id)

        # Get historical data from database
        history = _db.get_energy_history(device_id=device_id, hours=hours)

        # Format data points for frontend
        data_points = [
            {
                "timestamp": point["timestamp"],
                "power_w": point["power_w"],
                "voltage_v": point["voltage_v"],
                "current_a": point["current_a"],
                "power_consumption": point["power_w"],  # Alias for compatibility
            }
            for point in history
        ]

        return {
            "device_id": device_id,
            "device_name": device_name,
            "hours": hours,
            "data_points": data_points,
            "count": len(data_points),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to get history for device {device_id}")
        raise HTTPException(status_code=500, detail=f"Failed to get device history: {e!s}")


@router.post(
    "/tapo-p115/{device_id}/toggle",
    summary="Toggle P115 plug power state",
)
async def toggle_tapo_p115(
    device_id: str,
    toggle_request: ToggleRequest,
) -> dict[str, Any]:
    """
    Toggle power state of a Tapo P115 plug via MCP.
    """
    try:
        turn_on = toggle_request.turn_on
        logger.info(f"Toggle request for device {device_id}: turn_on={turn_on}")

        # Toggle device via MCP
        result = await call_mcp_tool(
            "energy_management",
            {
                "action": "control",
                "device_id": device_id,
                "power_state": "on" if turn_on else "off",
            },
        )

        if result.get("success"):
            data = result.get("data", {})
            return {
                "success": True,
                "device_id": device_id,
                "power_state": turn_on,
                "message": f"Device turned {'ON' if turn_on else 'OFF'}",
            }
        error_msg = result.get("error", "Failed to toggle device")
        if "not found" in error_msg.lower():
            raise HTTPException(status_code=404, detail=error_msg)
        if "read-only" in error_msg.lower() or "readonly" in error_msg.lower():
            raise HTTPException(status_code=403, detail=error_msg)
        raise HTTPException(status_code=500, detail=error_msg)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error toggling device {device_id}")
        raise HTTPException(status_code=500, detail=f"Internal error: {e!s}")
