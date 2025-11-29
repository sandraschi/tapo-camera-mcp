"""
Ring Doorbell Management Portmanteau Tool

Consolidates all Ring doorbell operations into a single tool with action-based interface.
"""

import logging
from typing import Any, Literal

from fastmcp import FastMCP

logger = logging.getLogger(__name__)

RING_ACTIONS = {
    "status": "Get Ring connection status and summary",
    "doorbells": "List all Ring doorbells",
    "events": "Get recent doorbell events (dings, motions)",
    "live_view": "Get WebRTC live view info",
    "snapshot": "Get doorbell snapshot (requires subscription)",
    "alarm_status": "Get Ring alarm system status",
    "capabilities": "Get Ring device capabilities",
    "2fa": "Submit 2FA verification code",
    "initialize": "Initialize Ring client with credentials",
}


def register_ring_management_tool(mcp: FastMCP) -> None:
    """Register the Ring management portmanteau tool."""

    @mcp.tool()
    async def ring_management(
        action: Literal[
            "status",
            "doorbells",
            "events",
            "live_view",
            "snapshot",
            "alarm_status",
            "capabilities",
            "2fa",
            "initialize",
        ],
        device_id: str | None = None,
        limit: int = 10,
        code: str | None = None,
        email: str | None = None,
        password: str | None = None,
    ) -> dict[str, Any]:
        """
        Comprehensive Ring doorbell management portmanteau tool.

        PORTMANTEAU PATTERN RATIONALE:
        Instead of creating 9+ separate tools (one per operation), this tool consolidates related
        Ring operations into a single interface. Prevents tool explosion while maintaining
        full functionality. Follows FastMCP 2.12+ best practices.

        Args:
            action (Literal, required): The operation to perform. Must be one of:
                - "status": Get Ring connection status and device summary (no params required)
                - "doorbells": List all Ring doorbells (no params required)
                - "events": Get recent doorbell events (optional: device_id, limit)
                - "live_view": Get WebRTC live view connection info (requires: device_id)
                - "snapshot": Get doorbell snapshot - requires Ring Protect (requires: device_id)
                - "alarm_status": Get Ring alarm system status (no params required)
                - "capabilities": Get Ring device capabilities (optional: device_id)
                - "2fa": Submit 2FA verification code (requires: code)
                - "initialize": Initialize Ring client (requires: email, password)

            device_id (str | None): Ring device ID. Required for: live_view, snapshot.
                Optional for: events, capabilities.

            limit (int): Maximum number of events to return. Used by: events action. Default: 10

            code (str | None): 2FA verification code. Required for: 2fa action.

            email (str | None): Ring account email. Required for: initialize action.

            password (str | None): Ring account password. Required for: initialize action.

        Returns:
            dict[str, Any]: Dictionary containing:
                - success (bool): Whether operation succeeded
                - action (str): The action that was performed
                - data (dict): Operation-specific result data
                - error (str | None): Error message if success is False

        Examples:
            # Get Ring status
            result = await ring_management(action="status")

            # List doorbells
            result = await ring_management(action="doorbells")

            # Get recent events
            result = await ring_management(action="events", limit=20)

            # Get events for specific device
            result = await ring_management(action="events", device_id="12345", limit=5)

            # Get live view info
            result = await ring_management(action="live_view", device_id="12345")

            # Submit 2FA code
            result = await ring_management(action="2fa", code="123456")
        """
        try:
            if action not in RING_ACTIONS:
                return {
                    "success": False,
                    "error": f"Invalid action '{action}'. Available: {list(RING_ACTIONS.keys())}",
                    "available_actions": RING_ACTIONS,
                }

            logger.info(f"Executing Ring management action: {action}")

            # Import Ring client
            from tapo_camera_mcp.integrations.ring_client import (
                get_ring_client,
                init_ring_client,
            )

            # Handle initialize action separately
            if action == "initialize":
                if not email or not password:
                    return {
                        "success": False,
                        "action": action,
                        "error": "email and password are required for initialize action",
                    }
                success = await init_ring_client(email=email, password=password)
                if success:
                    return {
                        "success": True,
                        "action": action,
                        "data": {"message": "Ring client initialized successfully"},
                    }
                # Check if 2FA is needed
                client = get_ring_client()
                if client and client.needs_2fa:
                    return {
                        "success": False,
                        "action": action,
                        "needs_2fa": True,
                        "error": "2FA required. Use action='2fa' with your verification code.",
                    }
                return {
                    "success": False,
                    "action": action,
                    "error": "Failed to initialize Ring client",
                }

            # Handle 2FA action
            if action == "2fa":
                if not code:
                    return {
                        "success": False,
                        "action": action,
                        "error": "code is required for 2fa action",
                    }
                client = get_ring_client()
                if not client:
                    return {
                        "success": False,
                        "action": action,
                        "error": "Ring client not initialized. Use initialize action first.",
                    }
                success = await client.submit_2fa_code(code)
                return {
                    "success": success,
                    "action": action,
                    "data": {"message": "2FA code accepted" if success else "2FA code rejected"},
                }

            # For other actions, get the client
            client = get_ring_client()
            if not client or not client.is_initialized:
                return {
                    "success": False,
                    "action": action,
                    "error": "Ring not initialized. Check config.yaml or use initialize action.",
                }

            # Route to appropriate handler
            if action == "status":
                summary = await client.get_summary()
                return {"success": True, "action": action, "data": summary}

            if action == "doorbells":
                summary = await client.get_summary()
                return {
                    "success": True,
                    "action": action,
                    "data": {
                        "doorbells": summary.get("doorbells", []),
                        "count": len(summary.get("doorbells", [])),
                    },
                }

            if action == "events":
                events = await client.get_events(device_id=device_id, limit=limit)
                return {
                    "success": True,
                    "action": action,
                    "data": {"events": events, "count": len(events)},
                }

            if action == "live_view":
                if not device_id:
                    # Get first doorbell
                    summary = await client.get_summary()
                    doorbells = summary.get("doorbells", [])
                    if doorbells:
                        device_id = str(doorbells[0].get("id"))
                    else:
                        return {
                            "success": False,
                            "action": action,
                            "error": "No doorbells found. Provide device_id.",
                        }
                return {
                    "success": True,
                    "action": action,
                    "data": {
                        "device_id": device_id,
                        "webrtc_url": "/api/ring/webrtc/offer",
                        "dashboard_url": "/alarms",
                        "note": "Use WebRTC API or open /alarms page for live view",
                    },
                }

            if action == "snapshot":
                if not device_id:
                    return {
                        "success": False,
                        "action": action,
                        "error": "device_id is required for snapshot action",
                    }
                # Note: snapshots require Ring Protect subscription
                return {
                    "success": False,
                    "action": action,
                    "error": "Snapshots require Ring Protect subscription. Use live_view instead.",
                    "data": {
                        "device_id": device_id,
                        "alternative": "Use action='live_view' for WebRTC stream (no subscription needed)",
                    },
                }

            if action == "alarm_status":
                alarm_status = await client.get_alarm_status()
                return {"success": True, "action": action, "data": alarm_status}

            if action == "capabilities":
                summary = await client.get_summary()
                capabilities = {
                    "live_view": True,
                    "two_way_talk": True,
                    "motion_detection": True,
                    "ding_detection": True,
                    "recording": summary.get("has_subscription", False),
                    "snapshot": summary.get("has_subscription", False),
                    "note": "Live view and two-way talk work WITHOUT Ring Protect subscription",
                }
                return {"success": True, "action": action, "data": capabilities}

            return {"success": False, "error": f"Action '{action}' not implemented"}

        except Exception as e:
            logger.exception(f"Error in Ring management action '{action}'")
            return {"success": False, "action": action, "error": str(e)}

