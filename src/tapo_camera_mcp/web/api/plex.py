"""
Plex Webhook API endpoints and state management.
Includes control functionality via Plex Media Server API.
"""

import json
import logging
from datetime import datetime

import httpx
from fastapi import APIRouter, HTTPException, Request

from ...config import get_config
from ...core.messaging_service import MessageCategory, get_messaging_service

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


def _get_plex_config():
    config = get_config()
    return config.get("plex", {})


def _condense_metadata(metadata: dict) -> dict:
    """
    Condense Plex metadata to just the essentials to avoid logging massive blobs.
    """
    if not metadata:
        return {}

    return {
        "title": metadata.get("title"),
        "type": metadata.get("type"),
        "grandparentTitle": metadata.get("grandparentTitle"),  # Series Name
        "parentTitle": metadata.get("parentTitle"),  # Season Name
        "summary": metadata.get("summary"),
        "thumb": metadata.get("thumb"),
    }


@router.post("/webhook")
async def plex_webhook(request: Request):
    """
    Handle Plex webhook POST request.
    """
    try:
        form_data = await request.form()
        payload_str = form_data.get("payload")

        if not payload_str:
            logger.warning("Plex webhook received with no payload")
            raise HTTPException(status_code=400, detail="No payload found in request")

        payload = json.loads(payload_str)

        event = payload.get("event")
        user = payload.get("Account", {}).get("title")
        player = payload.get("Player", {}).get("title")
        raw_metadata = payload.get("Metadata", {})
        media_title = raw_metadata.get("title")

        condensed_metadata = _condense_metadata(raw_metadata)

        global _now_playing_state
        _now_playing_state.update(
            {
                "active": event in ["media.play", "media.resume"],
                "event": event,
                "user": user,
                "player": player,
                "media": media_title,
                "timestamp": datetime.now().isoformat(),
                "metadata": condensed_metadata,
            }
        )

        logger.info(f"Plex Event: {event} | User: {user} | Player: {player} | Media: {media_title}")

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
                "metadata": condensed_metadata,
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
    """Get the current media being played."""
    return _now_playing_state


@router.get("/status")
async def get_plex_status():
    """Get current Plex integration status."""
    config = _get_plex_config()
    return {
        "status": "active" if config.get("server_url") else "not_configured",
        "webhook_listener": "active",
        "last_event": _now_playing_state.get("event"),
        "active_stream": _now_playing_state.get("active"),
    }


# --- Control Endpoints ---


@router.get("/clients")
async def list_plex_clients():
    """List available Plex clients (players)."""
    config = _get_plex_config()
    server_url = config.get("server_url")
    token = config.get("token")

    if not server_url or not token:
        # Fallback to defaults or error
        if not server_url:
            server_url = "http://localhost:32400"
        if not token:
            return {"clients": [], "error": "Plex token not configured"}

    headers = {"X-Plex-Token": token, "Accept": "application/json"}
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{server_url}/clients", headers=headers, timeout=5.0)
            if resp.status_code == 200:
                # Plex /clients XML usually, but /clients header accept json?
                # Newer Plex might need /resources or /status/sessions
                # Let's try /status/sessions (active) + /clients (available but often deprecated/local)
                # Or /resources (cloud)

                # For simplicity, returning mock if failed or basic list
                # Wait, response might be XML even with Accept: application/json for old endpoints.
                # Assuming JSON supported or simple parse.
                # If XML, we might need ElementTree.
                # Let's assume JSON for now or return raw.
                data = (
                    resp.json()
                    if "application/json" in resp.headers.get("Content-Type", "")
                    else {"raw": resp.text}
                )
                return {"clients": data}
            return {"clients": [], "error": f"Plex returned {resp.status_code}"}
    except Exception as e:
        logger.error(f"Failed to list clients: {e}")
        return {"clients": [], "error": str(e)}


@router.post("/control/{client_id}/{command}")
async def control_plex_client(client_id: str, command: str):
    """
    Control a Plex client.
    Command: play, pause, stop, stepForward, stepBack
    """
    config = _get_plex_config()
    server_url = config.get("server_url", "http://localhost:32400")
    token = config.get("token")

    if not token:
        raise HTTPException(status_code=400, detail="Plex token not configured")

    # Logic to send command to player.
    # Usually: GET /system/players/{clientIdentifier}/playback/{command}?X-Plex-Token=...

    headers = {"X-Plex-Token": token}
    url = f"{server_url}/system/players/{client_id}/playback/{command}"

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                return {"status": "success", "command": command}
            return {
                "status": "error",
                "code": resp.status_code,
                "detail": resp.text,
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send command: {e}")
