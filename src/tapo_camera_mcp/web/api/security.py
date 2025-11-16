from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import APIRouter

from ...config import get_model
from ...config.models import SecuritySettings
from ...security.integrations import SecurityIntegrationManager
from ...core.server import TapoCameraServer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/security", tags=["security"])

# Global security manager instance
_security_manager: SecurityIntegrationManager | None = None


async def _get_security_manager() -> SecurityIntegrationManager:
    """Get or create security integration manager."""
    global _security_manager
    if _security_manager is None:
        _security_manager = SecurityIntegrationManager()
        cfg = get_model(SecuritySettings)
        await _security_manager.initialize(cfg.integrations.model_dump())
    return _security_manager


async def _compute_ring_status() -> Dict[str, Any]:
    """Get real Ring device status."""
    cfg = get_model(SecuritySettings)
    enabled = bool(cfg.integrations.ring_mcp.get("enabled", False))
    
    devices: list[Dict[str, Any]] = []
    
    if enabled:
        try:
            # Try to get Ring devices from camera manager
            server = await TapoCameraServer.get_instance()
            if hasattr(server, "camera_manager") and server.camera_manager:
                cameras = await server.camera_manager.list_cameras()
                ring_cameras = [c for c in cameras if c.get("type") == "ring"]
                for cam in ring_cameras:
                    status_dict = cam.get("status", {})
                    if isinstance(status_dict, dict):
                        devices.append({
                            "device_id": cam.get("name", ""),
                            "name": cam.get("name", ""),
                            "type": "doorbell",
                            "status": "online" if status_dict.get("connected") else "offline",
                            "location": "Unknown",
                        })
        except Exception as e:
            logger.exception("Failed to get Ring devices")
    
    devices_total = len(devices)
    health = {"ok": True, "msg": f"Ring integration: {devices_total} devices" if enabled else "Ring disabled"}
    summary = {"enabled": enabled, "devices_total": devices_total}
    return {
        "enabled": enabled,
        "devices_total": devices_total,
        "devices": devices,
        "health": health,
        "summary": summary,
    }


async def _compute_nest_status() -> Dict[str, Any]:
    """Get real Nest Protect device status."""
    cfg = get_model(SecuritySettings)
    enabled = bool(cfg.integrations.nest_protect.get("enabled", False))
    
    devices: list[Dict[str, Any]] = []
    
    if enabled:
        try:
            manager = await _get_security_manager()
            nest_devices = await manager.get_all_devices()
            for device in nest_devices:
                devices.append({
                    "device_id": device.id,
                    "name": device.name,
                    "type": device.type,
                    "status": device.status,
                    "location": device.location,
                    "battery_level": device.battery_level,
                })
        except Exception as e:
            logger.exception("Failed to get Nest Protect devices")
    
    devices_total = len(devices)
    health = {
        "ok": True,
        "msg": f"Nest Protect: {devices_total} devices" if enabled else "Nest Protect disabled",
    }
    summary = {"enabled": enabled, "devices_total": devices_total}
    return {
        "enabled": enabled,
        "devices_total": devices_total,
        "devices": devices,
        "health": health,
        "summary": summary,
    }


@router.get("/ring/status", summary="Get Ring integration status")
async def get_ring_status() -> Dict[str, Any]:
    return await _compute_ring_status()


@router.get("/nest/status", summary="Get Nest Protect integration status")
async def get_nest_status() -> Dict[str, Any]:
    return await _compute_nest_status()


