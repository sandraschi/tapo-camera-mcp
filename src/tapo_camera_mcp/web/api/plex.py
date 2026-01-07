"""
Plex Webhook API endpoints and state management.
"""

import json
import logging
from datetime import datetime

from fastapi import APIRouter, Request, HTTPException

from ...core.messaging_service import get_messaging_service, MessageCategory

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/plex", tags=["plex"])

# In-memory store for current media state
_now_playing_state = {
    "active": False,
    "event": None,
    "user": None,
    "player": None,
    "media": None,
    "timestamp": None,
    "metadata": {},
}


@router.post("/webhook")
async def plex_webhook(request: Request):
    """
    Handle Plex webhook POST request.
    Plex sends data as multipart/form-data with a 'payload' field containing JSON.
    """
    try:
        # Plex sends a multipart/form-data request with a 'payload' field
        form_data = await request.form()
        payload_str = form_data.get("payload")

        if not payload_str:
            logger.warning("Plex webhook received with no payload")
            raise HTTPException(status_code=400, detail="No payload found in request")

        payload = json.loads(payload_str)

        event = payload.get("event")
        user = payload.get("Account", {}).get("title")
        player = payload.get("Player", {}).get("title")
        metadata = payload.get("Metadata", {})
        media_title = metadata.get("title")

        # Update global state
        global _now_playing_state
        _now_playing_state.update(
            {
                "active": event in ["media.play", "media.resume"],
                "event": event,
                "user": user,
                "player": player,
                "media": media_title,
                "timestamp": datetime.now().isoformat(),
                "metadata": metadata,
            }
        )

        # Log to tapo_mcp.log
        logger.info(
            f"Plex Event: {event} | User: {user} | Player: {player} | Media: {media_title}"
        )

        # Record in MessagingService for UI timeline
        messaging = get_messaging_service()
        messaging.info(
            category=MessageCategory.MEDIA_EVENT,
            source=f"Plex:{player or 'Unknown'}",
            title=f"Media {event.split('.')[-1].capitalize()}",
            description=f"{user or 'Someone'} is {event.split('.')[-1]}ing '{media_title}' on {player or 'a player'}.",
            details={
                "event": event,
                "user": user,
                "player": player,
                "media": media_title,
                "metadata": metadata,
            },
        )

        return {"status": "success", "event": event}

    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode Plex webhook payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    except Exception as e:
        logger.exception(f"Error processing Plex webhook: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


@router.get("/now-playing")
async def get_now_playing():
    """
    Get the current media being played.
    """
    return _now_playing_state


@router.get("/status")
async def get_plex_status():
    """
    Get current Plex integration status.
    """
    return {
        "status": "Plex webhook listener active",
        "last_event": _now_playing_state.get("event"),
        "active_stream": _now_playing_state.get("active"),
    }
