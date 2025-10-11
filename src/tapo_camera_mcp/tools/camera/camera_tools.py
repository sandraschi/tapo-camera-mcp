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
    '''
    List all registered cameras and their current status.
    
    Returns information about all cameras managed by the system including
    their connection status, type, model, and firmware version.
    
    Parameters:
        None
    
    Returns:
        Dict with:
        - success (bool): Whether the operation succeeded
        - cameras (List[Dict]): List of camera information dictionaries
        - total (int): Total number of cameras
    
    Example:
        result = await list_cameras_tool.execute()
        for camera in result['cameras']:
            print(f"{camera['name']}: {camera['status']}")
    '''
    
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
    '''
    Add a new camera to the system.
    
    Supports multiple camera types: Tapo IP cameras, Ring doorbells,
    Furbo pet cameras, and USB webcams. Each camera type requires
    different connection parameters.
    
    Parameters:
        camera_id (str): Unique identifier for the camera
        camera_type (str): Type - 'Tapo', 'Ring', 'Furbo', or 'Webcam'
        host (str, optional): IP address for Tapo cameras
        username (str, optional): Username for authentication
        password (str, optional): Password for authentication
        device_id (int, optional): Device ID for webcams (default: 0)
        token (str, optional): API token for Furbo cameras
    
    Returns:
        Dict with success status and camera details
    
    Example:
        # Add USB webcam
        result = await add_camera_tool.execute(
            camera_id='webcam1', camera_type='Webcam', device_id=0
        )
        
        # Add Tapo camera
        result = await add_camera_tool.execute(
            camera_id='tapo_front',
            camera_type='Tapo',
            host='192.168.1.100',
            username='user@example.com',
            password='secret'
        )
    '''
    
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
                camera_name=camera_name,
                camera_type='tapo',  # Assuming Tapo camera for now
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
    '''
    Remove a camera from the system.
    
    Disconnects and removes a camera from the managed camera list.
    
    Parameters:
        camera_name (str): Name of the camera to remove
    
    Returns:
        Dict with success status and confirmation message
    
    Example:
        result = await remove_camera_tool.execute(camera_name='webcam1')
    '''
    
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
    '''
    Set the active camera for subsequent operations.
    
    Designates which camera will be used for commands that don't
    specify a camera explicitly.
    
    Parameters:
        camera_name (str): Name of the camera to set as active
    
    Returns:
        Dict with success status and active camera name
    
    Example:
        result = await set_active_camera_tool.execute(camera_name='tapo_front')
    '''
    
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
    '''
    Get the current status of a camera.
    
    Returns detailed status information including connection state,
    streaming status, and hardware information.
    
    Parameters:
        camera_id (str, optional): Name of the camera to query (uses active camera if not specified)
    
    Returns:
        Dict with camera status details:
        - connected (bool): Connection status
        - streaming (bool): Whether camera is streaming
        - model (str): Camera model
        - firmware (str): Firmware version
    
    Example:
        result = await get_camera_status_tool.execute(camera_id='webcam1')
        if result['status']['connected']:
            print(f"Camera online: {result['status']['model']}")
    '''
    
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
    '''
    Connect to a Tapo camera.
    
    Establishes a connection to a TP-Link Tapo IP camera using
    the provided credentials and IP address.
    
    Parameters:
        host (str): IP address of the Tapo camera
        username (str): TP-Link account email
        password (str): TP-Link account password
    
    Returns:
        Dict with connection status and camera information
    
    Example:
        result = await connect_camera_tool.execute(
            host='192.168.1.100',
            username='user@example.com',
            password='secret123'
        )
        if result['success']:
            print(f"Connected to {result['camera']['model']}")
    '''

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
    '''
    Disconnect from the current camera.
    
    Closes the connection to the currently active camera and
    releases resources.
    
    Parameters:
        None
    
    Returns:
        Dict with disconnection status
    
    Example:
        result = await disconnect_camera_tool.execute()
        print(result['message'])
    '''
    
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
    '''
    Get detailed information about a camera.
    
    Returns comprehensive camera information including model, firmware,
    hardware capabilities, network settings, and features.
    
    Parameters:
        camera_id (str, optional): Camera name (uses active camera if not specified)
    
    Returns:
        Dict with detailed camera information:
        - model (str): Camera model
        - firmware (str): Firmware version
        - mac_address (str): MAC address
        - ip_address (str): IP address
        - capabilities (Dict): Hardware capabilities
    
    Example:
        result = await get_camera_info_tool.execute(camera_id='tapo_front')
        print(f"Model: {result['info']['model']}")
        print(f"Firmware: {result['info']['firmware']}")
    '''
    
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
    '''
    Manage camera groups for organizing multiple cameras.
    
    Create, update, or delete camera groups to logically organize
    cameras by location, function, or any other criteria.
    
    Parameters:
        action (str): Action to perform - 'create', 'update', 'delete', 'list'
        group_name (str, optional): Name of the group
        camera_ids (List[str], optional): List of camera IDs for the group
    
    Returns:
        Dict with operation result and group information
    
    Example:
        # Create a group
        result = await manage_camera_groups_tool.execute(
            action='create',
            group_name='front_yard',
            camera_ids=['tapo_front', 'webcam1']
        )
        
        # List all groups
        result = await manage_camera_groups_tool.execute(action='list')
    '''
    
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
camera_tool_classes = [
    ListCamerasTool, AddCameraTool, RemoveCameraTool, SetActiveCameraTool,
    GetCameraStatusTool, ConnectCameraTool, DisconnectCameraTool,
    GetCameraInfoTool, ManageCameraGroupsTool
]
logger.debug(f"Registered camera tools: {[tool.Meta.name for tool in camera_tool_classes]}")
