"""
Sensor API endpoints for real-world ingestion data.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from ...tools.energy.tapo_plug_tools import tapo_plug_manager

router = APIRouter(prefix="/api/sensors", tags=["sensors"])


def _model_dump(model: Any) -> dict[str, Any]:
    """Serialize Pydantic models across v1/v2."""
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()  # type: ignore[attr-defined]


@router.get("/tapo-p115", summary="List Tapo P115 smart plugs")
async def list_tapo_p115_devices() -> dict[str, Any]:
    """
    Return all Tapo P115 smart plugs with realtime metrics.
    """
    devices = await tapo_plug_manager.get_all_devices()
    response = []
    for device in devices:
        data = _model_dump(device)
        data["host"] = tapo_plug_manager.get_device_host(device.device_id)
        data["readonly"] = tapo_plug_manager.is_device_readonly(device.device_id)
        response.append(data)
    return {"devices": response, "count": len(response)}


@router.get(
    "/tapo-p115/{device_id}/history",
    summary="Get energy usage history",
)
async def get_tapo_p115_history(
    device_id: str,
    hours: int = Query(24, ge=1, le=168),
) -> dict[str, Any]:
    """
    Retrieve energy usage history for the specified Tapo P115 plug.
    """
    device = await tapo_plug_manager.get_device_status(device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device {device_id} not found")

    history = await tapo_plug_manager.get_energy_usage_history(device_id, hours=hours)
    serialized = [_model_dump(entry) for entry in history]
    return {
        "device_id": device_id,
        "device_name": device.name,
        "hours": hours,
        "data_points": serialized,
        "count": len(serialized),
    }


@router.post(
    "/tapo-p115/{device_id}/toggle",
    summary="Toggle P115 plug power state",
)
async def toggle_tapo_p115(
    device_id: str,
    turn_on: bool,
) -> dict[str, Any]:
    """
    Toggle power state of a Tapo P115 plug.
    """
    device = await tapo_plug_manager.get_device_status(device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device {device_id} not found")

    # Enforce read-only
    if tapo_plug_manager.is_device_readonly(device_id):
        raise HTTPException(status_code=403, detail="Device is read-only; toggling is disabled")

    success = await tapo_plug_manager.toggle_device(device_id, turn_on)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to toggle device")

    # Refresh device status
    updated_device = await tapo_plug_manager.get_device_status(device_id)
    return {
        "success": True,
        "device_id": device_id,
        "power_state": updated_device.power_state if updated_device else turn_on,
        "message": f"Device turned {'ON' if turn_on else 'OFF'}",
    }
