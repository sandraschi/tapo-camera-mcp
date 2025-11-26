from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import APIRouter

from ...config import get_model
from ...config.models import SecuritySettings
from ...core.server import TapoCameraServer
from ...security.integrations import SecurityIntegrationManager

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
    """Get real Ring device status with battery monitoring."""
    cfg = get_model(SecuritySettings)
    enabled = bool(cfg.integrations.ring_mcp.get("enabled", False))

    devices: list[Dict[str, Any]] = []
    battery_warnings = 0
    battery_critical = 0

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
                        # Get detailed camera info including battery
                        camera_info = cam.get("info", {})
                        battery_life = camera_info.get("battery_life")
                        battery_level = None
                        battery_status = "unknown"
                        is_charging = False

                        if battery_life is not None:
                            # battery_life can be a percentage (0-100) or "ok"/"low" string
                            if isinstance(battery_life, (int, float)):
                                battery_level = int(battery_life)
                                if battery_level <= 20:
                                    battery_status = "critical"
                                    battery_critical += 1
                                elif battery_level <= 40:
                                    battery_status = "low"
                                    battery_warnings += 1
                                else:
                                    battery_status = "good"
                            elif isinstance(battery_life, str):
                                battery_status = battery_life.lower()
                                if battery_status == "low":
                                    battery_warnings += 1
                                elif battery_status in ("critical", "dead"):
                                    battery_critical += 1

                        # Check if device is charging (if available in health data)
                        health_data = camera_info.get("health", {})
                        if isinstance(health_data, dict):
                            is_charging = health_data.get("charging", False) or health_data.get("powered", False)

                        devices.append({
                            "device_id": cam.get("name", ""),
                            "name": cam.get("name", ""),
                            "type": "doorbell",
                            "status": "online" if status_dict.get("connected") else "offline",
                            "location": "Unknown",
                            "battery_level": battery_level,
                            "battery_life": battery_life,
                            "battery_status": battery_status,
                            "is_charging": is_charging,
                            "model": camera_info.get("model", "Unknown"),
                        })
        except Exception:
            logger.exception("Failed to get Ring devices")

    devices_total = len(devices)
    health = {
        "ok": True,
        "msg": f"Ring integration: {devices_total} devices",
        "battery_warnings": battery_warnings,
        "battery_critical": battery_critical,
    }
    summary = {
        "enabled": enabled,
        "devices_total": devices_total,
        "battery_warnings": battery_warnings,
        "battery_critical": battery_critical,
    }
    return {
        "enabled": enabled,
        "devices_total": devices_total,
        "devices": devices,
        "health": health,
        "summary": summary,
    }


async def _compute_nest_status() -> Dict[str, Any]:
    """Get real Nest Protect device status with battery monitoring."""
    cfg = get_model(SecuritySettings)
    enabled = bool(cfg.integrations.nest_protect.get("enabled", False))

    devices: list[Dict[str, Any]] = []
    battery_warnings = 0
    battery_critical = 0

    if enabled:
        try:
            manager = await _get_security_manager()
            nest_devices = await manager.get_all_devices()
            for device in nest_devices:
                battery_level = device.battery_level
                battery_status = "unknown"

                # Determine battery status from level
                if battery_level is not None:
                    if battery_level <= 20:
                        battery_status = "critical"
                        battery_critical += 1
                    elif battery_level <= 40:
                        battery_status = "low"
                        battery_warnings += 1
                    else:
                        battery_status = "good"

                devices.append({
                    "device_id": device.id,
                    "name": device.name,
                    "type": device.type,
                    "status": device.status,
                    "location": device.location,
                    "battery_level": battery_level,
                    "battery_status": battery_status,
                    "last_seen": device.last_seen.isoformat() if device.last_seen else None,
                })
        except Exception:
            logger.exception("Failed to get Nest Protect devices")

    devices_total = len(devices)
    health = {
        "ok": True,
        "msg": f"Nest Protect: {devices_total} devices" if enabled else "Nest Protect disabled",
        "battery_warnings": battery_warnings,
        "battery_critical": battery_critical,
    }
    summary = {
        "enabled": enabled,
        "devices_total": devices_total,
        "battery_warnings": battery_warnings,
        "battery_critical": battery_critical,
    }
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


