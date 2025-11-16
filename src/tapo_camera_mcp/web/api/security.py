from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter

from ...config import get_model
from ...config.models import SecuritySettings

router = APIRouter(prefix="/api/security", tags=["security"])


def _compute_ring_status() -> Dict[str, Any]:
    cfg = get_model(SecuritySettings)
    enabled = bool(cfg.integrations.ring_mcp.get("enabled", False))
    # Placeholder until real integration: no devices listed yet
    devices: list[Dict[str, Any]] = []
    devices_total = len(devices)
    health = {"ok": True, "msg": "Ring integration enabled" if enabled else "Ring disabled"}
    summary = {"enabled": enabled, "devices_total": devices_total}
    return {
        "enabled": enabled,
        "devices_total": devices_total,
        "devices": devices,
        "health": health,
        "summary": summary,
    }


def _compute_nest_status() -> Dict[str, Any]:
    cfg = get_model(SecuritySettings)
    enabled = bool(cfg.integrations.nest_protect.get("enabled", False))
    # Placeholder until real integration: no devices listed yet
    devices: list[Dict[str, Any]] = []
    devices_total = len(devices)
    health = {
        "ok": True,
        "msg": "Nest Protect integration enabled" if enabled else "Nest Protect disabled",
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
    return _compute_ring_status()


@router.get("/nest/status", summary="Get Nest Protect integration status")
async def get_nest_status() -> Dict[str, Any]:
    return _compute_nest_status()


