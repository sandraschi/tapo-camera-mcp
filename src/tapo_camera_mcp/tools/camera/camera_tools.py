"""
Camera tools for Tapo Camera MCP.

This module contains tools for managing and controlling Tapo cameras.
"""

from typing import Dict, Any, Optional, List, Type, Union, Literal
from enum import Enum
import logging
from pydantic import Field, BaseModel, ConfigDict, validator

from tapo_camera_mcp.tools.base_tool import tool, ToolCategory, BaseTool, ToolResult, register_tool
from tapo_camera_mcp.validation import safe_execute, validate_camera_name, validate_ip_address, validate_port, validate_credentials, ToolValidationError
from tapo_camera_mcp.exceptions import TapoCameraError, ConnectionError, AuthenticationError

logger = logging.getLogger(__name__)

class CameraStatus(str, Enum):
    """Camera status values."""
    ONLINE = "online"
    OFFLINE = "offline"
    CONNECTING = "connecting"
    ERROR = "error"

    model_config = ConfigDict(
        use_enum_values=True
    )

@tool("list_cameras")
class ListCamerasTool(BaseTool):
    """Tool to list all registered cameras and their status."""
    
    class Meta:
        name = "list_cameras"
        description = "List all registered cameras and their status"
        category = ToolCategory.CAMERA
        
        class Parameters:
            pass
    
    # Config is no longer needed as we use Meta class for metadata
    async def execute(self) -> Dict[str, Any]:
        """List all registered cameras and their status."""
        from tapo_camera_mcp.core.server import TapoCameraServer  # Lazy import to avoid circular imports
        server = await TapoCameraServer.get_instance()
        
        try:
            # Get real camera manager and list all cameras
            if hasattr(server, 'camera_manager') and server.camera_manager:
                cameras = []
                for camera_name, camera in server.camera_manager.cameras.items():
                    try:
                        status = await camera.get_status()
                        cameras.append({
                            "name": camera_name,
                            "type": camera.config.type.value if hasattr(camera.config, 'type') else "unknown",
                            "status": "online" if status.get('connected', False) else "offline",
                            "model": status.get('model', 'Unknown'),
                            "firmware": status.get('firmware', 'Unknown'),
                            "streaming": status.get('streaming', False)
                        })
                    except Exception as e:
                        logger.warning(f"Failed to get status for camera {camera_name}: {e}")
                        cameras.append({
                            "name": camera_name,
                            "type": "unknown",
                            "status": "error",
                            "error": str(e)
                        })
                
                return {
                    "success": True,
                    "cameras": cameras,
                    "total": len(cameras)
                }
            else:
                return {
                    "success": True,
                    "cameras": [],
                    "total": 0,
                    "message": "No camera manager initialized"
                }
        except Exception as e:
            logger.error(f"Failed to list cameras: {e}")
            return {
                "success": False,
                "error": f"Failed to list cameras: {str(e)}",
                "cameras": []
            }

@tool("add_camera")
class AddCameraTool(BaseTool):
    """Tool to add a new camera to the system."""
    
    class Meta:
        name = "add_camera"
        description = "Add a new camera to the system"
        category = ToolCategory.CAMERA
        
        class Parameters:
            camera_name: str = Field(
                ...,
                description="A friendly name for the camera"
            )
            ip_address: str = Field(
                ...,
                description="IP address of the camera"
            )
            username: str = Field(
                ...,
                description="Username for camera authentication"
            )
            password: str = Field(
                ...,
                description="Password for camera authentication"
            )
            stream_url: Optional[str] = Field(
                None,
                description="Optional custom RTSP stream URL"
            )
    
    camera_name: str
    ip_address: str
    username: str
    password: str
    stream_url: Optional[str] = None
    
    async def execute(self) -> Dict[str, Any]:
        """Add a new camera to the system with comprehensive validation and error handling."""
        try:
            # Validate inputs
            camera_name = validate_camera_name(self.camera_name, "camera_name")
            ip_address = validate_ip_address(self.ip_address, "ip_address")
            username, password = validate_credentials(self.username, self.password)

            logger.info(f"Adding camera: {camera_name} at {ip_address}")

            from tapo_camera_mcp.core.server import TapoCameraServer  # Lazy import to avoid circular imports
            server = await TapoCameraServer.get_instance()

            result = await server.add_camera(
                name=camera_name,
                host=ip_address,
                username=username,
                password=password,
                stream_url=self.stream_url
            )

            logger.info(f"Successfully added camera: {camera_name}")
            return result

        except ToolValidationError as e:
            logger.warning(f"Validation error adding camera {self.camera_name}: {e.message}")
            return {
                "success": False,
                "error": f"Validation error: {e.message}",
                "field": e.field
            }
        except Exception as e:
            logger.error(f"Failed to add camera {self.camera_name}: {e}")
            return {
                "success": False,
                "error": f"Failed to add camera: {str(e)}"
            }

@tool("remove_camera")
class RemoveCameraTool(BaseTool):
    """Tool to remove a camera from the system."""
    
    class Meta:
        name = "remove_camera"
        description = "Remove a camera from the system"
        category = ToolCategory.CAMERA
        
        class Parameters:
            camera_id: str = Field(
                ...,
                description="ID of the camera to remove"
            )
    
    camera_id: str
    
    async def execute(self) -> Dict[str, Any]:
        """Remove a camera from the system."""
        from tapo_camera_mcp.core.server import TapoCameraServer  # Lazy import to avoid circular imports
        server = await TapoCameraServer.get_instance()
        return await server.remove_camera(camera_id=self.camera_id)

@tool("set_active_camera")
class SetActiveCameraTool(BaseTool):
    """Tool to set the active camera for operations."""
    
    class Meta:
        name = "set_active_camera"
        description = "Set the active camera for operations"
        category = ToolCategory.CAMERA
        
        class Parameters:
            name: str = Field(
                ...,
                description="Name or ID of the camera to set as active"
            )
    
    name: str
    
    async def execute(self) -> Dict[str, Any]:
        """Set the active camera for operations."""
        from tapo_camera_mcp.core.server import TapoCameraServer  # Lazy import to avoid circular imports
        server = await TapoCameraServer.get_instance()
        return await server.set_active_camera(name=self.name)

@tool("get_camera_status")
class GetCameraStatusTool(BaseTool):
    """Tool to get the status of a specific camera."""
    
    class Meta:
        name = "get_camera_status"
        description = "Get the status of a specific camera"
        category = ToolCategory.CAMERA
        
        class Parameters:
            camera_id: str = Field(
                None,
                description="ID of the camera to get status for. If not provided, returns status of active camera."
            )
    
    camera_id: Optional[str] = None
    
    async def execute(self) -> Dict[str, Any]:
        """Get the status of a specific camera."""
        from tapo_camera_mcp.core.server import TapoCameraServer  # Lazy import to avoid circular imports
        server = await TapoCameraServer.get_instance()
        return await server.get_camera_status(name=self.camera_id) if self.camera_id else await server.get_active_camera_status()

@tool("connect_camera")
class ConnectCameraTool(BaseTool):
    """Tool to connect to a Tapo camera."""
    
    class Meta:
        name = "connect_camera"
        description = "Connect to a Tapo camera"
        category = ToolCategory.CAMERA
        
        class Parameters:
            host: str = Field(
                ...,
                description="IP address or hostname of the camera"
            )
            username: str = Field(
                ...,
                description="Username for camera authentication"
            )
            password: str = Field(
                ...,
                description="Password for camera authentication"
            )
            verify_ssl: bool = Field(
                True,
                description="Whether to verify SSL certificates (default: True)"
            )
    
    host: str
    username: str
    password: str
    verify_ssl: bool = True
    
    async def execute(self) -> Dict[str, Any]:
        """Connect to a Tapo camera with comprehensive validation and error handling."""
        try:
            # Validate inputs
            host = validate_ip_address(self.host, "host")
            username, password = validate_credentials(self.username, self.password)

            logger.info(f"Connecting to camera at {host}")

            from tapo_camera_mcp.core.server import TapoCameraServer  # Lazy import to avoid circular imports
            server = await TapoCameraServer.get_instance()

            result = await server.connect_camera(
                host=host,
                username=username,
                password=password,
                verify_ssl=self.verify_ssl
            )

            logger.info(f"Successfully connected to camera at {host}")
            return result

        except ToolValidationError as e:
            logger.warning(f"Validation error connecting to camera {self.host}: {e.message}")
            return {
                "success": False,
                "error": f"Validation error: {e.message}",
                "field": e.field
            }
        except ConnectionError as e:
            logger.error(f"Connection failed to camera {self.host}: {e}")
            return {
                "success": False,
                "error": f"Connection failed: {str(e)}"
            }
        except AuthenticationError as e:
            logger.error(f"Authentication failed for camera {self.host}: {e}")
            return {
                "success": False,
                "error": f"Authentication failed: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Unexpected error connecting to camera {self.host}: {e}")
            return {
                "success": False,
                "error": f"Connection error: {str(e)}"
            }

@tool("disconnect_camera")
class DisconnectCameraTool(BaseTool):
    """Tool to disconnect from the current camera."""
    
    class Meta:
        name = "disconnect_camera"
        description = "Disconnect from the current camera"
        category = ToolCategory.CAMERA
        
        class Parameters:
            pass
    
    async def execute(self) -> Dict[str, Any]:
        """Disconnect from the current camera."""
        from tapo_camera_mcp.core.server import TapoCameraServer  # Lazy import to avoid circular imports
        server = await TapoCameraServer.get_instance()
        return await server.disconnect_camera()

@tool("get_camera_info")
class GetCameraInfoTool(BaseTool):
    """Tool to get detailed information about the connected camera."""
    
    class Meta:
        name = "get_camera_info"
        description = "Get detailed information about the connected camera"
        category = ToolCategory.CAMERA
        
        class Parameters:
            pass
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Get detailed information about the connected camera.
        
        Args:
            **kwargs: Additional arguments (ignored)
            
        Returns:
            Dict containing camera information
        """
        from tapo_camera_mcp.core.server import TapoCameraServer  # Lazy import to avoid circular imports
        server = await TapoCameraServer.get_instance()
        return await server.get_camera_info()

@tool("manage_camera_groups")
class ManageCameraGroupsTool(BaseTool):
    """Tool to manage camera groups."""
    
    class Meta:
        name = "manage_camera_groups"
        description = "Manage camera groups"
        category = ToolCategory.CAMERA
        
        class Parameters:
            action: Literal["list", "add", "remove", "list_group"] = Field(
                ...,
                description="Action to perform"
            )
            group: Optional[str] = Field(
                None,
                description="Group name (required for add/remove/list_group)"
            )
            camera: Optional[str] = Field(
                None,
                description="Camera name (required for add/remove)"
            )
    
    action: str
    group: Optional[str] = None
    camera: Optional[str] = None
    
    async def execute(self) -> Dict[str, Any]:
        """Manage camera groups."""
        from tapo_camera_mcp.core.server import TapoCameraServer  # Lazy import to avoid circular imports
        server = await TapoCameraServer.get_instance()
        
        if self.action == "list":
            return await server.list_camera_groups()
        elif self.action == "list_group":
            if not self.group:
                raise ValueError("Group name is required for list_group action")
            return await server.list_cameras_in_group(self.group)
        elif self.action == "add":
            if not self.group or not self.camera:
                raise ValueError("Both group name and camera name are required for add action")
            return await server.add_camera_to_group(self.camera, self.group)
        elif self.action == "remove":
            if not self.group or not self.camera:
                raise ValueError("Both group name and camera name are required for remove action")
            return await server.remove_camera_from_group(self.camera, self.group)
        else:
            raise ValueError(f"Unknown action: {self.action}")

# Register all tools
ListCamerasTool = register_tool(ListCamerasTool)
AddCameraTool = register_tool(AddCameraTool)
RemoveCameraTool = register_tool(RemoveCameraTool)
SetActiveCameraTool = register_tool(SetActiveCameraTool)
GetCameraStatusTool = register_tool(GetCameraStatusTool)
ConnectCameraTool = register_tool(ConnectCameraTool)
DisconnectCameraTool = register_tool(DisconnectCameraTool)
GetCameraInfoTool = register_tool(GetCameraInfoTool)
ManageCameraGroupsTool = register_tool(ManageCameraGroupsTool)

# Debug: Print registered tools
logger.debug(f"Registered camera tools: {[tool.Meta.name for tool in [
    ListCamerasTool, AddCameraTool, RemoveCameraTool, SetActiveCameraTool,
    GetCameraStatusTool, ConnectCameraTool, DisconnectCameraTool,
    GetCameraInfoTool, ManageCameraGroupsTool
]]}")
