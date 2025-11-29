"""
Audio Management Portmanteau Tool

Consolidates all audio streaming operations into a single tool with action-based interface.
"""

import logging
from typing import Any, Literal

from fastmcp import FastMCP

logger = logging.getLogger(__name__)

AUDIO_ACTIONS = {
    "get_url": "Get RTSP stream URL with audio for a camera",
    "capabilities": "Get audio capabilities for all camera types",
    "player_url": "Get URL for browser audio player page",
    "vlc_command": "Get VLC command to play camera stream with audio",
}


def register_audio_management_tool(mcp: FastMCP) -> None:
    """Register the audio management portmanteau tool."""

    @mcp.tool()
    async def audio_management(
        action: Literal["get_url", "capabilities", "player_url", "vlc_command"],
        camera_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Comprehensive audio streaming management portmanteau tool.

        PORTMANTEAU PATTERN RATIONALE:
        Consolidates audio streaming operations into a single interface.
        Note: ONVIF cameras only support one-way audio (listening). Two-way
        audio requires the Tapo app. Ring doorbell supports full two-way via WebRTC.

        Args:
            action (Literal, required): The operation to perform. Must be one of:
                - "get_url": Get RTSP stream URL with audio (requires: camera_id)
                - "capabilities": Get audio capabilities overview (no params required)
                - "player_url": Get browser player page URL (requires: camera_id)
                - "vlc_command": Get VLC command to play stream (requires: camera_id)

            camera_id (str | None): Camera identifier. Required for: get_url, player_url, vlc_command.

        Returns:
            dict[str, Any]: Dictionary containing:
                - success (bool): Whether operation succeeded
                - action (str): The action that was performed
                - data (dict): Operation-specific result data
                - error (str | None): Error message if success is False

        Examples:
            # Get audio capabilities
            result = await audio_management(action="capabilities")

            # Get RTSP URL for camera
            result = await audio_management(action="get_url", camera_id="kitchen_cam")

            # Get VLC command
            result = await audio_management(action="vlc_command", camera_id="kitchen_cam")
        """
        try:
            if action not in AUDIO_ACTIONS:
                return {
                    "success": False,
                    "error": f"Invalid action '{action}'. Available: {list(AUDIO_ACTIONS.keys())}",
                    "available_actions": AUDIO_ACTIONS,
                }

            logger.info(f"Executing audio management action: {action}")

            # Handle capabilities action (no camera_id needed)
            if action == "capabilities":
                return {
                    "success": True,
                    "action": action,
                    "data": {
                        "onvif_cameras": {
                            "listen_audio": True,
                            "two_way_audio": False,
                            "note": "ONVIF Profile S does not support audio backchannel",
                        },
                        "ring_doorbell": {
                            "listen_audio": True,
                            "two_way_audio": True,
                            "note": "Ring supports two-way audio via WebRTC (no subscription needed)",
                        },
                        "tapo_app": {
                            "listen_audio": True,
                            "two_way_audio": True,
                            "note": "Full two-way audio in official Tapo app",
                        },
                        "recommendation": "For two-way audio with Tapo cameras, use the Tapo app. "
                                         "This tool provides listen-only RTSP streams.",
                    },
                }

            # Other actions require camera_id
            if not camera_id:
                return {
                    "success": False,
                    "action": action,
                    "error": f"camera_id is required for '{action}' action",
                }

            # Get camera and RTSP URL
            from urllib.parse import urlparse

            from tapo_camera_mcp.core.server import TapoCameraServer

            server = await TapoCameraServer.get_instance()
            camera = await server.camera_manager.get_camera(camera_id)

            if not camera:
                return {
                    "success": False,
                    "action": action,
                    "error": f"Camera '{camera_id}' not found",
                }

            # Connect if needed
            if not await camera.is_connected():
                await camera.connect()

            # Get stream URL
            stream_url = await camera.get_stream_url()
            if not stream_url:
                return {
                    "success": False,
                    "action": action,
                    "error": f"Could not get stream URL for '{camera_id}'",
                }

            # Add auth credentials
            parsed = urlparse(stream_url)
            username = camera.config.params.get("username", "")
            password = camera.config.params.get("password", "")

            if username and password:
                auth_url = f"rtsp://{username}:{password}@{parsed.hostname}:{parsed.port or 554}{parsed.path}"
            else:
                auth_url = stream_url

            # Safe URL (no password) for display
            safe_url = f"rtsp://{parsed.hostname}:{parsed.port or 554}{parsed.path}"

            if action == "get_url":
                return {
                    "success": True,
                    "action": action,
                    "data": {
                        "camera_id": camera_id,
                        "rtsp_url": auth_url,
                        "rtsp_url_safe": safe_url,
                        "audio_capable": True,
                        "two_way_audio": False,
                        "note": "Open this URL in VLC for video + audio playback",
                    },
                }

            if action == "player_url":
                return {
                    "success": True,
                    "action": action,
                    "data": {
                        "camera_id": camera_id,
                        "player_url": f"/api/audio/player/{camera_id}",
                        "vlc_link_url": f"/api/audio/vlc-link/{camera_id}",
                        "note": "Open player_url in browser for audio controls",
                    },
                }

            if action == "vlc_command":
                return {
                    "success": True,
                    "action": action,
                    "data": {
                        "camera_id": camera_id,
                        "vlc_command": f'vlc "{auth_url}"',
                        "ffplay_command": f'ffplay -i "{auth_url}"',
                        "note": "Run these commands in terminal to play stream with audio",
                    },
                }

            return {"success": False, "error": f"Action '{action}' not implemented"}

        except Exception as e:
            logger.exception(f"Error in audio management action '{action}'")
            return {"success": False, "action": action, "error": str(e)}

