"""
Camera Management Portmanteau Tool

Consolidates all camera-related operations into a single tool with action-based interface.
Replaces multiple individual camera tools with one comprehensive tool.
"""

import logging
from typing import Any, Literal

from fastmcp import FastMCP

# Import existing camera tool functions
from tapo_camera_mcp.tools.camera.camera_tools import (
    AddCameraTool,
    ConnectCameraTool,
    DisconnectCameraTool,
    GetCameraInfoTool,
    GetCameraStatusTool,
    ListCamerasTool,
    ManageCameraGroupsTool,
    RemoveCameraTool,
    SetActiveCameraTool,
)

logger = logging.getLogger(__name__)

# Define available actions
CAMERA_ACTIONS = {
    "list": "List all cameras",
    "add": "Add a new camera",
    "remove": "Remove a camera",
    "connect": "Connect to a camera",
    "disconnect": "Disconnect from a camera",
    "info": "Get detailed information about a camera",
    "status": "Get camera status",
    "set_active": "Set a camera as active",
    "manage_groups": "Manage camera groups",
}


def register_camera_management_tool(mcp: FastMCP) -> None:
    """Register the camera management portmanteau tool."""

    @mcp.tool()
    async def camera_management(
        action: Literal[
            "list",
            "add",
            "remove",
            "connect",
            "disconnect",
            "info",
            "status",
            "set_active",
            "manage_groups",
        ],
        camera_name: str | None = None,
        camera_id: str | None = None,
        camera_type: str | None = None,
        host: str | None = None,
        username: str | None = None,
        password: str | None = None,
        group_action: str | None = None,
        group_name: str | None = None,
    ) -> dict[str, Any]:
        """
        Comprehensive camera management portmanteau tool.

        PORTMANTEAU PATTERN RATIONALE:
        Instead of creating 9+ separate tools (one per operation), this tool consolidates related
        camera operations into a single interface. Prevents tool explosion (9+ tools → 1 tool) while maintaining
        full functionality and improving discoverability. Follows FastMCP 2.12+ best practices.

        Args:
            action (Literal, required): The operation to perform. Must be one of: "list", "add", "remove", "connect",
                "disconnect", "info", "status", "set_active", "manage_groups".
                - "list": List all cameras (no other parameters required)
                - "add": Add a new camera (requires: camera_name, camera_type, host, username, password)
                - "remove": Remove a camera (requires: camera_name or camera_id)
                - "connect": Connect to a camera (requires: camera_name or camera_id)
                - "disconnect": Disconnect from a camera (requires: camera_name or camera_id)
                - "info": Get detailed information about a camera (requires: camera_name or camera_id)
                - "status": Get camera status (requires: camera_name or camera_id)
                - "set_active": Set a camera as active (requires: camera_name or camera_id)
                - "manage_groups": Manage camera groups (requires: group_action, optionally group_name and camera_name)
            
            camera_name (str | None): Name of the camera. Required for: add, remove, connect, disconnect, info, status,
                set_active operations. Alternative to camera_id.
            
            camera_id (str | None): ID of the camera. Required for: remove, connect, disconnect, info, status,
                set_active operations. Alternative to camera_name.
            
            camera_type (str | None): Camera type for adding. Required for: add operation.
                Examples: "Tapo", "Ring", "Webcam"
            
            host (str | None): IP address or hostname for new cameras. Required for: add operation.
                Example: "192.168.1.100"
            
            username (str | None): Username for camera authentication. Required for: add operation.
            
            password (str | None): Password for camera authentication. Required for: add operation.
            
            group_action (str | None): Action for group management. Required for: manage_groups operation.
                Valid: "list", "create", "add", "remove"
            
            group_name (str | None): Group name for group operations. Required for: manage_groups operation when
                group_action is "create". Optional for: manage_groups operation when group_action is "add" or "remove"

        Returns:
            dict[str, Any]: Dictionary containing:
                - success (bool): Boolean indicating if operation succeeded
                - action (str): The action that was performed
                - data (dict): Operation-specific result data
                - error (str | None): Error message if success is False
                - count (int | None): Number of cameras (for "list" action)

        Examples:
            # List all cameras - simplest usage, no other parameters needed
            result = await camera_management(action="list")

            # Add a new camera - requires camera_name, camera_type, host, username, password
            result = await camera_management(
                action="add",
                camera_name="Front Door",
                camera_type="Tapo",
                host="192.168.1.100",
                username="admin",
                password="password123"
            )

            # Connect to a camera - requires camera_name
            result = await camera_management(action="connect", camera_name="Front Door")

            # Get camera information - requires camera_name
            result = await camera_management(action="info", camera_name="Front Door")

            # Manage camera groups - requires group_action
            result = await camera_management(
                action="manage_groups",
                group_action="list"
            )
        """
        try:
            # Validate action
            if action not in CAMERA_ACTIONS:
                return {
                    "success": False,
                    "error": f"Invalid action '{action}'. Available actions: {list(CAMERA_ACTIONS.keys())}",
                    "available_actions": CAMERA_ACTIONS,
                }

            logger.info(f"Executing camera management action: {action}")

            # Route to appropriate handler based on action
            if action == "list":
                return await _handle_list_cameras()

            if action == "add":
                return await _handle_add_camera(
                    camera_name=camera_name,
                    camera_type=camera_type,
                    host=host,
                    username=username,
                    password=password,
                )

            if action == "remove":
                return await _handle_remove_camera(camera_name=camera_name, camera_id=camera_id)

            if action == "connect":
                return await _handle_connect_camera(camera_name=camera_name, camera_id=camera_id)

            if action == "disconnect":
                return await _handle_disconnect_camera(camera_name=camera_name, camera_id=camera_id)

            if action == "info":
                return await _handle_get_camera_info(camera_name=camera_name, camera_id=camera_id)

            if action == "status":
                return await _handle_get_camera_status(camera_name=camera_name, camera_id=camera_id)

            if action == "set_active":
                return await _handle_set_active_camera(camera_name=camera_name, camera_id=camera_id)

            if action == "manage_groups":
                return await _handle_manage_groups(
                    group_action=group_action,
                    group_name=group_name,
                    camera_name=camera_name,
                )

            return {
                "success": False,
                "error": f"Action '{action}' not implemented",
                "available_actions": CAMERA_ACTIONS,
            }

        except Exception as e:
            logger.error(f"Error in camera management action '{action}': {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Failed to execute action '{action}': {e!s}",
                "action": action,
                "available_actions": CAMERA_ACTIONS,
            }


async def _handle_list_cameras() -> dict[str, Any]:
    """Handle list cameras action."""
    try:
        tool = ListCamerasTool()
        result = await tool.execute()
        if isinstance(result, dict) and result.get("success"):
            return {
                "success": True,
                "action": "list",
                "data": result,
                "count": result.get("total", 0),
            }
        return {"success": False, "action": "list", "error": "Failed to list cameras"}
    except Exception as e:
        return {"success": False, "action": "list", "error": f"Failed to list cameras: {e!s}"}


async def _handle_add_camera(
    camera_name: str | None = None,
    camera_type: str | None = None,
    host: str | None = None,
    username: str | None = None,
    password: str | None = None,
) -> dict[str, Any]:
    """Handle add camera action."""
    if not camera_name:
        return {
            "success": False,
            "action": "add",
            "error": "camera_name is required for add action",
        }

    if not camera_type:
        return {
            "success": False,
            "action": "add",
            "error": "camera_type is required for add action",
        }

    if not host:
        return {
            "success": False,
            "action": "add",
            "error": "host is required for add action",
        }

    try:
        tool = AddCameraTool()
        result = await tool.execute(
            camera_id=camera_name,
            camera_type=camera_type,
            host=host,
            username=username or "",
            password=password or "",
        )
        return {"success": True, "action": "add", "camera_name": camera_name, "data": result}
    except Exception as e:
        return {
            "success": False,
            "action": "add",
            "camera_name": camera_name,
            "error": f"Failed to add camera: {e!s}",
        }


async def _handle_remove_camera(
    camera_name: str | None = None, camera_id: str | None = None
) -> dict[str, Any]:
    """Handle remove camera action."""
    identifier = camera_name or camera_id
    if not identifier:
        return {
            "success": False,
            "action": "remove",
            "error": "camera_name or camera_id is required for remove action",
        }

    try:
        tool = RemoveCameraTool()
        result = await tool.execute(camera_id=identifier)
        return {"success": True, "action": "remove", "camera_id": identifier, "data": result}
    except Exception as e:
        return {
            "success": False,
            "action": "remove",
            "camera_id": identifier,
            "error": f"Failed to remove camera: {e!s}",
        }


async def _handle_connect_camera(
    camera_name: str | None = None, camera_id: str | None = None
) -> dict[str, Any]:
    """Handle connect camera action."""
    identifier = camera_name or camera_id
    if not identifier:
        return {
            "success": False,
            "action": "connect",
            "error": "camera_name or camera_id is required for connect action",
        }

    try:
        tool = ConnectCameraTool()
        result = await tool.execute(camera_id=identifier)
        return {"success": True, "action": "connect", "camera_id": identifier, "data": result}
    except Exception as e:
        return {
            "success": False,
            "action": "connect",
            "camera_id": identifier,
            "error": f"Failed to connect camera: {e!s}",
        }


async def _handle_disconnect_camera(
    camera_name: str | None = None, camera_id: str | None = None
) -> dict[str, Any]:
    """Handle disconnect camera action."""
    identifier = camera_name or camera_id
    if not identifier:
        return {
            "success": False,
            "action": "disconnect",
            "error": "camera_name or camera_id is required for disconnect action",
        }

    try:
        tool = DisconnectCameraTool()
        result = await tool.execute(camera_id=identifier)
        return {"success": True, "action": "disconnect", "camera_id": identifier, "data": result}
    except Exception as e:
        return {
            "success": False,
            "action": "disconnect",
            "camera_id": identifier,
            "error": f"Failed to disconnect camera: {e!s}",
        }


async def _handle_get_camera_info(
    camera_name: str | None = None, camera_id: str | None = None
) -> dict[str, Any]:
    """Handle get camera info action."""
    identifier = camera_name or camera_id
    if not identifier:
        return {
            "success": False,
            "action": "info",
            "error": "camera_name or camera_id is required for info action",
        }

    try:
        tool = GetCameraInfoTool()
        result = await tool.execute(camera_id=identifier)
        return {"success": True, "action": "info", "camera_id": identifier, "data": result}
    except Exception as e:
        return {
            "success": False,
            "action": "info",
            "camera_id": identifier,
            "error": f"Failed to get camera info: {e!s}",
        }


async def _handle_get_camera_status(
    camera_name: str | None = None, camera_id: str | None = None
) -> dict[str, Any]:
    """Handle get camera status action."""
    identifier = camera_name or camera_id
    if not identifier:
        return {
            "success": False,
            "action": "status",
            "error": "camera_name or camera_id is required for status action",
        }

    try:
        tool = GetCameraStatusTool()
        result = await tool.execute(camera_id=identifier)
        return {"success": True, "action": "status", "camera_id": identifier, "data": result}
    except Exception as e:
        return {
            "success": False,
            "action": "status",
            "camera_id": identifier,
            "error": f"Failed to get camera status: {e!s}",
        }


async def _handle_set_active_camera(
    camera_name: str | None = None, camera_id: str | None = None
) -> dict[str, Any]:
    """Handle set active camera action."""
    identifier = camera_name or camera_id
    if not identifier:
        return {
            "success": False,
            "action": "set_active",
            "error": "camera_name or camera_id is required for set_active action",
        }

    try:
        tool = SetActiveCameraTool()
        result = await tool.execute(camera_id=identifier)
        return {"success": True, "action": "set_active", "camera_id": identifier, "data": result}
    except Exception as e:
        return {
            "success": False,
            "action": "set_active",
            "camera_id": identifier,
            "error": f"Failed to set active camera: {e!s}",
        }


async def _handle_manage_groups(
    group_action: str | None = None,
    group_name: str | None = None,
    camera_name: str | None = None,
) -> dict[str, Any]:
    """Handle manage groups action."""
    if not group_action:
        return {
            "success": False,
            "action": "manage_groups",
            "error": "group_action is required for manage_groups action",
        }

    try:
        tool = ManageCameraGroupsTool()
        result = await tool.execute(
            group_action=group_action, group_name=group_name, camera_id=camera_name
        )
        return {
            "success": True,
            "action": "manage_groups",
            "group_action": group_action,
            "data": result,
        }
    except Exception as e:
        return {
            "success": False,
            "action": "manage_groups",
            "error": f"Failed to manage groups: {e!s}",
        }

