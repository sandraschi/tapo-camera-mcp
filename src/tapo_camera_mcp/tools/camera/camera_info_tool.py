"""
Camera Info Portmanteau Tool

Combines camera information operations:
- Get camera info
- Get camera status
- Manage camera groups
"""

import logging
import time
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from ...tools.base_tool import BaseTool, ToolCategory, ToolResult, tool

logger = logging.getLogger(__name__)


@tool("camera_info")
class CameraInfoTool(BaseTool):
    """Camera information management tool.

    Provides unified camera information management including getting camera info,
    status, and managing camera groups.

    Parameters:
        operation: Type of info operation (info, status, groups).
        camera_id: Camera ID for info/status operations.
        group_action: Group action (list, create, add, remove) for groups operation.
        group_name: Group name for group operations.

    Returns:
        A dictionary containing the camera information result.
    """

    class Meta:
        name = "camera_info"
        description = (
            "Unified camera information management including info, status, and group management"
        )
        category = ToolCategory.CAMERA

        class Parameters(BaseModel):
            operation: str = Field(..., description="Info operation: 'info', 'status', 'groups'")
            camera_id: Optional[str] = Field(
                None, description="Camera ID for info/status operations"
            )
            group_action: Optional[str] = Field(
                None, description="Group action: 'list', 'create', 'add', 'remove'"
            )
            group_name: Optional[str] = Field(None, description="Group name for group operations")

    async def execute(self, **kwargs) -> ToolResult:
        """Execute the camera info tool."""
        try:
            # Extract parameters from kwargs
            operation = kwargs.get("operation", "info")
            camera_id = kwargs.get("camera_id")
            group_action = kwargs.get("group_action")
            group_name = kwargs.get("group_name")

            # Call the existing _run method
            result = await self._run(operation, camera_id, group_action, group_name)

            # Return as ToolResult
            return ToolResult(content=result, is_error=not result.get("success", True))

        except Exception as e:
            logger.exception("Camera info tool execution failed")
            return ToolResult(content={"success": False, "error": str(e)}, is_error=True)

    async def execute(
        self,
        operation: str,
        camera_id: Optional[str] = None,
        group_action: Optional[str] = None,
        group_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute camera info operation."""
        try:
            logger.info(f"Camera info {operation} operation")

            if operation == "info":
                return await self._get_camera_info(camera_id)
            if operation == "status":
                return await self._get_camera_status(camera_id)
            if operation == "groups":
                return await self._manage_groups(group_action, group_name, camera_id)
            return {
                "success": False,
                "error": f"Invalid operation: {operation}. Must be 'info', 'status', or 'groups'",
                "timestamp": time.time(),
            }

        except Exception as e:
            logger.exception(f"Camera info {operation} operation failed")
            return {
                "success": False,
                "error": str(e),
                "operation": operation,
                "timestamp": time.time(),
            }

    async def _get_camera_info(self, camera_id: Optional[str]) -> Dict[str, Any]:
        """Get camera information."""
        if not camera_id:
            return {
                "success": False,
                "error": "Camera ID is required for info operation",
                "timestamp": time.time(),
            }

        # Simulate camera info
        camera_info = {
            "camera_id": camera_id,
            "name": "Front Door Camera",
            "model": "Tapo C200",
            "firmware_version": "1.2.3",
            "hardware_version": "1.0",
            "serial_number": "TC200123456789",
            "ip_address": "192.168.1.100",
            "mac_address": "AA:BB:CC:DD:EE:FF",
            "resolution": "1920x1080",
            "fps": 30,
            "night_vision": True,
            "ptz_support": True,
            "audio_support": True,
            "storage": "microSD",
            "location": "Front Door",
            "installation_date": "2024-01-15",
        }

        return {
            "success": True,
            "operation": "info",
            "camera_info": camera_info,
            "message": f"Camera info retrieved for {camera_id}",
            "timestamp": time.time(),
        }

    async def _get_camera_status(self, camera_id: Optional[str]) -> Dict[str, Any]:
        """Get camera status."""
        if not camera_id:
            return {
                "success": False,
                "error": "Camera ID is required for status operation",
                "timestamp": time.time(),
            }

        # Simulate camera status

        camera_status = {
            "camera_id": camera_id,
            "status": "online",
            "connection_quality": "excellent",
            "signal_strength": 85,
            "battery_level": 100,
            "storage_usage": 45.2,
            "last_motion": time.time() - 300,
            "recording_status": "active",
            "night_mode": False,
            "privacy_mode": False,
            "led_status": "on",
            "motion_detection": "enabled",
            "audio_recording": "enabled",
            "cloud_storage": "connected",
            "last_sync": time.time() - 60,
        }

        return {
            "success": True,
            "operation": "status",
            "camera_status": camera_status,
            "message": f"Camera status retrieved for {camera_id}",
            "timestamp": time.time(),
        }

    async def _manage_groups(
        self, group_action: Optional[str], group_name: Optional[str], camera_id: Optional[str]
    ) -> Dict[str, Any]:
        """Manage camera groups."""
        if not group_action:
            return {
                "success": False,
                "error": "Group action is required for groups operation",
                "timestamp": time.time(),
            }

        if group_action == "list":
            # Simulate group listing
            groups = [
                {
                    "group_id": "group_001",
                    "name": "Outdoor Cameras",
                    "cameras": ["cam_001", "cam_002", "cam_003"],
                    "created": "2024-01-15",
                    "description": "All outdoor security cameras",
                },
                {
                    "group_id": "group_002",
                    "name": "Indoor Cameras",
                    "cameras": ["cam_004", "cam_005"],
                    "created": "2024-01-20",
                    "description": "Indoor monitoring cameras",
                },
            ]

            return {
                "success": True,
                "operation": "groups",
                "group_action": "list",
                "groups": groups,
                "total_groups": len(groups),
                "message": f"Found {len(groups)} camera groups",
                "timestamp": time.time(),
            }

        if group_action == "create":
            if not group_name:
                return {
                    "success": False,
                    "error": "Group name is required for create action",
                    "timestamp": time.time(),
                }

            import secrets

            group_id = f"group_{secrets.randbelow(1000):03d}"

            return {
                "success": True,
                "operation": "groups",
                "group_action": "create",
                "group": {
                    "group_id": group_id,
                    "name": group_name,
                    "cameras": [],
                    "created": time.strftime("%Y-%m-%d"),
                    "description": f"Camera group: {group_name}",
                },
                "message": f"Camera group '{group_name}' created with ID {group_id}",
                "timestamp": time.time(),
            }

        if group_action in ["add", "remove"]:
            if not camera_id:
                return {
                    "success": False,
                    "error": "Camera ID is required for add/remove actions",
                    "timestamp": time.time(),
                }

            return {
                "success": True,
                "operation": "groups",
                "group_action": group_action,
                "camera_id": camera_id,
                "message": f"Camera {camera_id} {group_action}ed to group successfully",
                "timestamp": time.time(),
            }

        return {
            "success": False,
            "error": f"Invalid group action: {group_action}. Must be 'list', 'create', 'add', or 'remove'",
            "timestamp": time.time(),
        }
