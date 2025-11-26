"""
Ring doorbell and alarm API endpoints.
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from tapo_camera_mcp.integrations.ring_client import (
    RingAlarmMode,
    get_ring_client,
    init_ring_client,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ring", tags=["Ring"])


class Ring2FARequest(BaseModel):
    code: str


class RingAlarmModeRequest(BaseModel):
    mode: str  # "disarmed", "home", "away"


class RingAuthRequest(BaseModel):
    email: str
    password: str


class RingSummaryResponse(BaseModel):
    initialized: bool
    two_fa_pending: bool = False
    doorbells: list = []
    doorbell_count: int = 0
    alarm: Optional[dict] = None
    recent_events: list = []
    last_event: Optional[dict] = None


@router.get("/status")
async def get_ring_status():
    """Get Ring connection status."""
    client = get_ring_client()
    if not client:
        return {
            "connected": False,
            "initialized": False,
            "two_fa_pending": False,
            "message": "Ring client not configured",
        }

    if client.is_2fa_pending:
        message = "2FA code required"
    elif client.is_initialized:
        message = "Connected"
    else:
        message = "Not initialized"

    return {
        "connected": True,
        "initialized": client.is_initialized,
        "two_fa_pending": client.is_2fa_pending,
        "message": message,
    }


@router.get("/summary", response_model=RingSummaryResponse)
async def get_ring_summary():
    """Get Ring summary for dashboard."""
    client = get_ring_client()
    if not client:
        return RingSummaryResponse(initialized=False)

    if not client.is_initialized:
        return RingSummaryResponse(
            initialized=False,
            two_fa_pending=client.is_2fa_pending,
        )

    try:
        summary = await client.get_summary()
        return RingSummaryResponse(
            initialized=summary["initialized"],
            two_fa_pending=summary["2fa_pending"],
            doorbells=summary["doorbells"],
            doorbell_count=summary["doorbell_count"],
            alarm=summary["alarm"],
            recent_events=summary["recent_events"],
            last_event=summary["last_event"],
        )
    except Exception as e:
        logger.exception("Failed to get Ring summary")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/doorbells")
async def get_doorbells():
    """Get all Ring doorbells."""
    client = get_ring_client()
    if not client or not client.is_initialized:
        raise HTTPException(status_code=503, detail="Ring not initialized")

    try:
        doorbells = await client.get_doorbells()
        return {"doorbells": [d.to_dict() for d in doorbells]}
    except Exception as e:
        logger.exception("Failed to get Ring doorbells")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/alarm")
async def get_alarm_status():
    """Get Ring alarm status."""
    client = get_ring_client()
    if not client or not client.is_initialized:
        raise HTTPException(status_code=503, detail="Ring not initialized")

    try:
        status = await client.get_alarm_status()
        if not status:
            return {"alarm": None, "message": "No alarm found"}
        return {"alarm": status.to_dict()}
    except Exception as e:
        logger.exception("Failed to get Ring alarm status")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/alarm/mode")
async def set_alarm_mode(request: RingAlarmModeRequest):
    """Set Ring alarm mode."""
    client = get_ring_client()
    if not client or not client.is_initialized:
        raise HTTPException(status_code=503, detail="Ring not initialized")

    mode_map = {
        "disarmed": RingAlarmMode.DISARMED,
        "home": RingAlarmMode.HOME,
        "away": RingAlarmMode.AWAY,
    }

    mode = mode_map.get(request.mode.lower())
    if not mode:
        raise HTTPException(status_code=400, detail=f"Invalid mode: {request.mode}")

    try:
        success = await client.set_alarm_mode(mode)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to set alarm mode")
        return {"success": True, "mode": request.mode}
    except Exception as e:
        logger.exception("Failed to set Ring alarm mode")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/events")
async def get_recent_events(limit: int = 10):
    """Get recent Ring events."""
    client = get_ring_client()
    if not client or not client.is_initialized:
        raise HTTPException(status_code=503, detail="Ring not initialized")

    try:
        events = await client.get_recent_events(limit=limit)
        return {"events": events}
    except Exception as e:
        logger.exception("Failed to get Ring events")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/auth/2fa")
async def submit_2fa_code(request: Ring2FARequest):
    """Submit Ring 2FA verification code."""
    client = get_ring_client()
    if not client:
        raise HTTPException(status_code=503, detail="Ring client not configured")

    if not client.is_2fa_pending:
        raise HTTPException(status_code=400, detail="No 2FA pending")

    try:
        success = await client.submit_2fa_code(request.code)
        if not success:
            raise HTTPException(status_code=400, detail="Invalid 2FA code")
        return {"success": True, "message": "Ring authenticated successfully"}
    except Exception as e:
        logger.exception("Failed to submit Ring 2FA code")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/auth/init")
async def initialize_ring(request: RingAuthRequest):
    """Initialize Ring with credentials (for first-time setup)."""
    try:
        client = await init_ring_client(
            email=request.email,
            password=request.password,
        )

        if client.is_2fa_pending:
            return {
                "success": False,
                "two_fa_required": True,
                "message": "2FA code required - check your email/SMS",
            }

        if client.is_initialized:
            return {
                "success": True,
                "two_fa_required": False,
                "message": "Ring initialized successfully",
            }

        return {
            "success": False,
            "two_fa_required": False,
            "message": "Failed to initialize Ring",
        }
    except Exception as e:
        logger.exception("Failed to initialize Ring")
        raise HTTPException(status_code=500, detail=str(e)) from e

