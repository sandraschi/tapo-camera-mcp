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
    """Get Ring alarm status including sensors and base station."""
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


@router.get("/alarm/devices")
async def get_alarm_devices():
    """Get all Ring Alarm devices (base station, sensors, keypads, etc.)."""
    client = get_ring_client()
    if not client or not client.is_initialized:
        raise HTTPException(status_code=503, detail="Ring not initialized")

    try:
        devices = await client.get_alarm_devices()
        return {
            "devices": [d.to_dict() for d in devices],
            "count": len(devices),
        }
    except Exception as e:
        logger.exception("Failed to get Ring alarm devices")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/alarm/events")
async def get_alarm_events(limit: int = 50):
    """Get recent Ring Alarm events (arm, disarm, sensor triggers, etc.)."""
    client = get_ring_client()
    if not client or not client.is_initialized:
        raise HTTPException(status_code=503, detail="Ring not initialized")

    try:
        events = await client.get_alarm_events(limit=limit)
        return {"events": events, "count": len(events)}
    except Exception as e:
        logger.exception("Failed to get Ring alarm events")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/alarm/mode")
async def set_alarm_mode(request: RingAlarmModeRequest):
    """Set Ring alarm mode (disarm, home, away)."""
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


class RingSirenRequest(BaseModel):
    activate: bool = True
    duration: int = 30  # seconds


@router.post("/alarm/siren")
async def control_siren(request: RingSirenRequest):
    """Control Ring alarm siren (activate/deactivate).

    Args:
        activate: True to sound siren, False to stop
        duration: Siren duration in seconds (only for activation)
    """
    client = get_ring_client()
    if not client or not client.is_initialized:
        raise HTTPException(status_code=503, detail="Ring not initialized")

    try:
        success = await client.trigger_siren(
            activate=request.activate,
            duration=request.duration,
        )
        if not success:
            raise HTTPException(status_code=500, detail="Failed to control siren")

        action = "activated" if request.activate else "deactivated"
        return {"success": True, "action": action}
    except Exception as e:
        logger.exception("Failed to control Ring siren")
        raise HTTPException(status_code=500, detail=str(e)) from e


class RingSirenTestRequest(BaseModel):
    duration: int = 3  # Short test burst (seconds)
    countdown: int = 5  # Countdown before siren (seconds) - warn the girlfriend!


@router.post("/alarm/siren/test")
async def test_siren(request: RingSirenTestRequest):
    """Test Ring alarm siren with countdown warning.
    
    WARNING: This WILL be loud (104dB)! 
    
    Args:
        duration: How long siren sounds (default 3 seconds)
        countdown: Seconds before siren starts (default 5 - RUN!)
    
    Returns:
        Countdown info, then triggers siren after delay
    """
    import asyncio

    client = get_ring_client()
    if not client or not client.is_initialized:
        raise HTTPException(status_code=503, detail="Ring not initialized")

    # Sanity limits
    if request.duration > 10:
        raise HTTPException(status_code=400, detail="Max test duration is 10 seconds (have mercy)")
    if request.countdown < 3:
        raise HTTPException(status_code=400, detail="Min countdown is 3 seconds (warn your girlfriend!)")
    if request.countdown > 30:
        raise HTTPException(status_code=400, detail="Max countdown is 30 seconds")

    logger.warning(f"[ALARM] SIREN TEST INITIATED - {request.countdown}s countdown, {request.duration}s duration")

    # Wait for countdown
    await asyncio.sleep(request.countdown)

    try:
        # FIRE! 🔊
        success = await client.trigger_siren(
            activate=True,
            duration=request.duration,
        )

        if not success:
            raise HTTPException(status_code=500, detail="Failed to trigger test siren")

        return {
            "success": True,
            "action": "test_complete",
            "duration": request.duration,
            "warning": "🔊 SIREN ACTIVATED - Hope she wasn't holding coffee!",
        }
    except Exception as e:
        logger.exception("Failed to test Ring siren")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/alarm/siren/stop")
async def stop_siren():
    """Emergency siren stop - silence all sirens immediately."""
    client = get_ring_client()
    if not client or not client.is_initialized:
        raise HTTPException(status_code=503, detail="Ring not initialized")

    try:
        success = await client.trigger_siren(activate=False, duration=0)
        return {"success": success, "action": "sirens_silenced"}
    except Exception as e:
        logger.exception("Failed to stop Ring siren")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/events")
async def get_recent_events(limit: int = 10):
    """Get recent Ring events (motion, ding, on-demand).

    Returns motion and doorbell events with video URLs when available.
    """
    client = get_ring_client()
    if not client or not client.is_initialized:
        raise HTTPException(status_code=503, detail="Ring not initialized")

    try:
        events = await client.get_recent_events(limit=limit)

        # Categorize events
        motion_events = [e for e in events if e.get("event_type") == "motion"]
        ding_events = [e for e in events if e.get("event_type") == "ding"]
        other_events = [e for e in events if e.get("event_type") not in ["motion", "ding"]]

        return {
            "events": events,
            "summary": {
                "total": len(events),
                "motion": len(motion_events),
                "dings": len(ding_events),
                "other": len(other_events),
            },
            "latest_motion": motion_events[0] if motion_events else None,
            "latest_ding": ding_events[0] if ding_events else None,
        }
    except Exception as e:
        logger.exception("Failed to get Ring events")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/events/{device_id}/video/{recording_id}")
async def get_event_video_url(device_id: str, recording_id: str):
    """Get video URL for a specific Ring event.

    Note: Requires Ring Protect subscription to access recordings.
    """
    import asyncio

    client = get_ring_client()
    if not client or not client.is_initialized:
        raise HTTPException(status_code=503, detail="Ring not initialized")

    try:
        # Run in separate thread to avoid event loop issues
        def get_url():
            for db in client._ring.video_devices():
                if str(db.id) == device_id:
                    if not db.has_subscription:
                        return {"error": "subscription_required", "has_subscription": False}
                    url = db.recording_url(recording_id)
                    return {"url": url, "has_subscription": True}
            return None

        result = await asyncio.to_thread(get_url)

        if not result:
            raise HTTPException(status_code=404, detail="Device not found")

        if result.get("error") == "subscription_required":
            return {
                "video_url": None,
                "recording_id": recording_id,
                "has_subscription": False,
                "message": "Ring Protect subscription required to access video recordings"
            }

        if not result.get("url"):
            return {
                "video_url": None,
                "recording_id": recording_id,
                "message": "Video not available for this recording"
            }

        return {"video_url": result["url"], "recording_id": recording_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to get Ring video URL")
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


@router.get("/snapshot/{device_id}")
async def get_doorbell_snapshot(device_id: str):
    """Get a snapshot image from a Ring doorbell.

    Note: Ring snapshots require a Ring Protect subscription.
    Without subscription, this returns the last recorded event thumbnail.
    """
    from fastapi.responses import Response

    client = get_ring_client()
    if not client or not client.is_initialized:
        raise HTTPException(status_code=503, detail="Ring not initialized")

    try:

        # Get the doorbell device
        await client._update_data()
        doorbell = None
        for db in client._ring.video_devices():
            if str(db.id) == device_id:
                doorbell = db
                break

        if not doorbell:
            raise HTTPException(status_code=404, detail=f"Doorbell {device_id} not found")

        # Try async_get_snapshot directly
        try:
            snapshot = await doorbell.async_get_snapshot()
        except (IndexError, KeyError) as e:
            # Snapshot not available - try getting last recording thumbnail
            logger.warning(f"Snapshot unavailable ({e}), trying last recording...")
            try:
                # Get last recording ID
                last_id = await doorbell.async_get_last_recording_id()
                if last_id:
                    # Get recording URL for thumbnail
                    url = await doorbell.async_recording_url(last_id)
                    return {"message": "Snapshot unavailable", "last_recording_url": url, "recording_id": last_id}
            except Exception as e:
                logger.debug("Could not get fallback recording URL: %s", e)
            raise HTTPException(
                status_code=503,
                detail="Snapshot unavailable. Ring Protect subscription may be required for live snapshots."
            ) from None

        if not snapshot:
            raise HTTPException(status_code=500, detail="Failed to get snapshot")

        return Response(content=snapshot, media_type="image/jpeg")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to get Ring snapshot")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/last-recording/{device_id}")
async def get_last_recording(device_id: str):
    """Get the last recorded video from Ring doorbell.

    Works without Ring Protect subscription for recent motion/ding events.
    """
    client = get_ring_client()
    if not client or not client.is_initialized:
        raise HTTPException(status_code=503, detail="Ring not initialized")

    try:
        # Get the doorbell device
        await client._update_data()
        doorbell = None
        for db in client._ring.video_devices():
            if str(db.id) == device_id:
                doorbell = db
                break

        if not doorbell:
            raise HTTPException(status_code=404, detail=f"Doorbell {device_id} not found")

        # Get last recording ID
        last_id = await doorbell.async_get_last_recording_id()
        if not last_id:
            return {"message": "No recordings available", "has_subscription": doorbell.has_subscription}

        # Get recording URL
        url = await doorbell.async_recording_url(last_id)

        return {
            "recording_id": last_id,
            "video_url": url,
            "has_subscription": doorbell.has_subscription,
            "message": "Use video_url to view the last recording"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to get Ring recording")
        raise HTTPException(status_code=500, detail=str(e)) from e


class WebRTCOfferRequest(BaseModel):
    sdp_offer: str
    device_id: str


class WebRTCCandidateRequest(BaseModel):
    candidate: str
    device_id: str


@router.post("/webrtc/offer")
async def create_webrtc_stream(request: WebRTCOfferRequest):
    """Create WebRTC stream for live view and two-way talk.

    Send browser's SDP offer, get Ring's SDP answer back.
    """
    import asyncio

    client = get_ring_client()
    if not client or not client.is_initialized:
        raise HTTPException(status_code=503, detail="Ring not initialized")

    try:
        # Find the doorbell
        doorbell = None
        for db in client._ring.video_devices():
            if str(db.id) == request.device_id:
                doorbell = db
                break

        if not doorbell:
            raise HTTPException(status_code=404, detail=f"Doorbell {request.device_id} not found")

        # Generate WebRTC stream - this returns SDP answer
        def get_answer():
            return doorbell.generate_webrtc_stream(request.sdp_offer, keep_alive_timeout=60)

        sdp_answer = await asyncio.to_thread(get_answer)

        return {
            "sdp_answer": sdp_answer,
            "device_id": request.device_id,
            "status": "stream_created"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to create WebRTC stream")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/webrtc/candidate")
async def send_ice_candidate(request: WebRTCCandidateRequest):
    """Send ICE candidate to Ring for WebRTC connection."""
    import asyncio

    client = get_ring_client()
    if not client or not client.is_initialized:
        raise HTTPException(status_code=503, detail="Ring not initialized")

    try:
        # Find the doorbell
        doorbell = None
        for db in client._ring.video_devices():
            if str(db.id) == request.device_id:
                doorbell = db
                break

        if not doorbell:
            raise HTTPException(status_code=404, detail=f"Doorbell {request.device_id} not found")

        # Send ICE candidate
        def send_candidate():
            doorbell.on_webrtc_candidate(request.candidate)

        await asyncio.to_thread(send_candidate)

        return {"status": "candidate_sent"}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to send ICE candidate")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/webrtc/keepalive/{device_id}")
async def keepalive_webrtc_stream(device_id: str):
    """Keep WebRTC stream alive."""
    import asyncio

    client = get_ring_client()
    if not client or not client.is_initialized:
        raise HTTPException(status_code=503, detail="Ring not initialized")

    try:
        doorbell = None
        for db in client._ring.video_devices():
            if str(db.id) == device_id:
                doorbell = db
                break

        if not doorbell:
            raise HTTPException(status_code=404, detail=f"Doorbell {device_id} not found")

        await asyncio.to_thread(doorbell.keep_alive_webrtc_stream)
        return {"status": "keepalive_sent"}
    except Exception as e:
        logger.exception("Failed to send keepalive")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/webrtc/close/{device_id}")
async def close_webrtc_stream(device_id: str):
    """Close WebRTC stream."""
    import asyncio

    client = get_ring_client()
    if not client or not client.is_initialized:
        raise HTTPException(status_code=503, detail="Ring not initialized")

    try:
        doorbell = None
        for db in client._ring.video_devices():
            if str(db.id) == device_id:
                doorbell = db
                break

        if not doorbell:
            raise HTTPException(status_code=404, detail=f"Doorbell {device_id} not found")

        await asyncio.to_thread(doorbell.close_webrtc_stream)
        return {"status": "stream_closed"}
    except Exception as e:
        logger.exception("Failed to close stream")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/webrtc/ice-servers")
async def get_ice_servers():
    """Get ICE servers for WebRTC connection."""
    import asyncio

    client = get_ring_client()
    if not client or not client.is_initialized:
        raise HTTPException(status_code=503, detail="Ring not initialized")

    try:
        doorbell = None
        for db in client._ring.video_devices():
            doorbell = db
            break

        if not doorbell:
            raise HTTPException(status_code=404, detail="No doorbell found")

        ice_servers = await asyncio.to_thread(doorbell.get_ice_servers)
        return {"ice_servers": ice_servers}
    except Exception as e:
        logger.exception("Failed to get ICE servers")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/capabilities/{device_id}")
async def get_doorbell_capabilities(device_id: str):
    """Get Ring doorbell capabilities and subscription status."""
    client = get_ring_client()
    if not client or not client.is_initialized:
        raise HTTPException(status_code=503, detail="Ring not initialized")

    try:
        await client._update_data()
        doorbell = None
        for db in client._ring.video_devices():
            if str(db.id) == device_id:
                doorbell = db
                break

        if not doorbell:
            raise HTTPException(status_code=404, detail=f"Doorbell {device_id} not found")

        return {
            "device_id": device_id,
            "name": doorbell.name,
            "model": doorbell.model,
            "has_subscription": doorbell.has_subscription,
            "battery_life": doorbell.battery_life,
            "wifi_signal": doorbell.wifi_signal_strength,
            "firmware": doorbell.firmware,
            "features": {
                "live_view": doorbell.has_subscription,  # Requires subscription
                "snapshots": doorbell.has_subscription,  # Requires subscription
                "recordings": True,  # Last 60 days of motion/ring events
                "motion_detection": True,
                "two_way_audio": True,
            },
            "note": "Live snapshots and on-demand live view require Ring Protect subscription"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to get Ring capabilities")
        raise HTTPException(status_code=500, detail=str(e)) from e
