"""
Camera tools for Tapo Camera MCP.

This module contains tools for managing and controlling Tapo cameras.
"""

from typing import Dict, Any, Optional, List
from enum import Enum
import logging

from fastmcp.tools.types import ToolParameter
from ..base_tool import BaseTool, ToolCategory, tool, parameter

logger = logging.getLogger(__name__)

class CameraStatus(str, Enum):
    """Camera status values."""
    ONLINE = "online"
    OFFLINE = "offline"
    CONNECTING = "connecting"
    ERROR = "error"

@tool(
    name="list_cameras",
    description="List all registered cameras and their status",
    category=ToolCategory.CAMERA
)
class ListCamerasTool(BaseTool):
    """Tool to list all registered cameras and their status."""
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """List all registered cameras and their status."""
        from ...server_v3 import TapoCameraServer  # Lazy import to avoid circular imports
        server = TapoCameraServer.get_instance()
        return await server.list_cameras()

@tool(
    name="add_camera",
    description="Add a new camera to the system",
    category=ToolCategory.CAMERA
)
class AddCameraTool(BaseTool):
    """Tool to add a new camera to the system."""
    
    parameters = [
        parameter("name", str, "Name to identify the camera", required=True),
        parameter("host", str, "Camera IP address or hostname", required=True),
        parameter("username", str, "Camera username", required=True),
        parameter("password", str, "Camera password", required=True, secret=True),
        parameter("stream_quality", str, "Stream quality (hd/sd)", default="hd"),
        parameter("verify_ssl", bool, "Verify SSL certificate", default=True)
    ]
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Add a new camera to the system."""
        from ...server_v3 import TapoCameraServer  # Lazy import to avoid circular imports
        server = TapoCameraServer.get_instance()
        return await server.add_camera(kwargs)

@tool(
    name="remove_camera",
    description="Remove a camera from the system",
    category=ToolCategory.CAMERA
)
class RemoveCameraTool(BaseTool):
    """Tool to remove a camera from the system."""
    
    parameters = [
        parameter("name", str, "Name of the camera to remove", required=True)
    ]
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Remove a camera from the system."""
        from ...server_v3 import TapoCameraServer  # Lazy import to avoid circular imports
        server = TapoCameraServer.get_instance()
        return await server.remove_camera(kwargs["name"])

@tool(
    name="set_active_camera",
    description="Set the active camera for operations",
    category=ToolCategory.CAMERA
)
class SetActiveCameraTool(BaseTool):
    """Tool to set the active camera for operations."""
    
    parameters = [
        parameter("name", str, "Name of the camera to set as active", required=True)
    ]
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Set the active camera for operations."""
        from ...server_v3 import TapoCameraServer  # Lazy import to avoid circular imports
        server = TapoCameraServer.get_instance()
        return await server.set_active_camera(kwargs["name"])

@tool(
    name="get_camera_status",
    description="Get the status of a specific camera or all cameras",
    category=ToolCategory.CAMERA
)
class GetCameraStatusTool(BaseTool):
    """Tool to get the status of a specific camera or all cameras."""
    
    parameters = [
        parameter("name", str, "Name of the camera to get status for (leave empty for all)", required=False)
    ]
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Get the status of a specific camera or all cameras."""
        from ...server_v3 import TapoCameraServer  # Lazy import to avoid circular imports
        server = TapoCameraServer.get_instance()
        name = kwargs.get("name")
        return await server.get_camera_status(name)

@tool(
    name="connect_camera",
    description="Connect to a Tapo camera",
    category=ToolCategory.CAMERA
)
class ConnectCameraTool(BaseTool):
    """Tool to connect to a Tapo camera."""
    
    parameters = [
        parameter("host", str, "Camera IP address or hostname", required=True),
        parameter("username", str, "Camera username", required=True),
        parameter("password", str, "Camera password", required=True, secret=True),
        parameter("verify_ssl", bool, "Verify SSL certificate", default=True)
    ]
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Connect to a Tapo camera."""
        from ...server_v2 import TapoCameraServer  # Lazy import to avoid circular imports
        server = TapoCameraServer.get_instance()
        try:
            # Convert to the format expected by the server
            params = {
                'host': kwargs['host'],
                'username': kwargs['username'],
                'password': kwargs['password'],
                'verify_ssl': kwargs.get('verify_ssl', True)
            }
            return await server.connect_camera(params)
        except Exception as e:
            logger.error(f"Error connecting to camera: {str(e)}")
            return {"status": "error", "message": f"Failed to connect to camera: {str(e)}"}

@tool(
    name="disconnect_camera",
    description="Disconnect from the current camera",
    category=ToolCategory.CAMERA
)
class DisconnectCameraTool(BaseTool):
    """Tool to disconnect from the current camera."""
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Disconnect from the current camera."""
        from ...server_v2 import TapoCameraServer  # Lazy import to avoid circular imports
        server = TapoCameraServer.get_instance()
        try:
            return await server.disconnect_camera()
        except Exception as e:
            logger.error(f"Error disconnecting from camera: {str(e)}")
            return {"status": "error", "message": f"Failed to disconnect from camera: {str(e)}"}

@tool(
    name="get_camera_info",
    description="Get detailed information about the connected camera",
    category=ToolCategory.CAMERA
)
class GetCameraInfoTool(BaseTool):
    """Tool to get detailed information about the connected camera."""
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Get detailed information about the connected camera."""
        from ...server_v2 import TapoCameraServer  # Lazy import to avoid circular imports
        server = TapoCameraServer.get_instance()
        try:
            return await server.get_camera_info()
        except Exception as e:
            logger.error(f"Error getting camera info: {str(e)}")
            return {"status": "error", "message": f"Failed to get camera info: {str(e)}"}

@tool(
    name="manage_camera_groups",
    description="Manage camera groups (add, remove, list)",
    category=ToolCategory.CAMERA
)
class ManageCameraGroupsTool(BaseTool):
    """Tool to manage camera groups."""
    
    parameters = [
        parameter("action", str, "Action to perform (list, add, remove, list_group)", required=True),
        parameter("group", str, "Group name (required for add/remove/list_group)", required=False),
        parameter("camera", str, "Camera name (required for add/remove)", required=False)
    ]
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Manage camera groups."""
        from ...server_v2 import TapoCameraServer  # Lazy import to avoid circular imports
        server = TapoCameraServer.get_instance()
        try:
            return await server.camera_groups(kwargs)
        except Exception as e:
            logger.error(f"Error managing camera groups: {str(e)}")
            return {"status": "error", "message": f"Failed to manage camera groups: {str(e)}"}
