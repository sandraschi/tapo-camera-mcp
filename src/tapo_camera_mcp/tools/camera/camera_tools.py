"""
Camera tools for Tapo Camera MCP.

This module contains tools for managing and controlling Tapo cameras.
"""

from typing import Dict, Any, Optional, Literal
from enum import Enum
import logging
from pydantic import Field, ConfigDict

from tapo_camera_mcp.tools.base_tool import tool, ToolCategory, BaseTool, register_tool
from tapo_camera_mcp.validation import (
    validate_camera_name,
    validate_ip_address,
    validate_credentials,
    ToolValidationError,
)
from tapo_camera_mcp.exceptions import ConnectionError, AuthenticationError

logger = logging.getLogger(__name__)


class CameraStatus(str, Enum):
    """Camera status values."""

    ONLINE = "online"
    OFFLINE = "offline"
    CONNECTING = "connecting"
    ERROR = "error"

    model_config = ConfigDict(use_enum_values=True)


@tool("list_cameras")
class ListCamerasTool(BaseTool):
    """
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
    """

    class Meta:
        name = "list_cameras"
        description = "List all registered cameras and their status"
        category = ToolCategory.CAMERA

        class Parameters:
            pass

    # Config is no longer needed as we use Meta class for metadata
    async def execute(self) -> Dict[str, Any]:
        """List all configured cameras with their current status and information.

        Retrieves a comprehensive list of all cameras registered in the system,
        including their connection status, configuration details, and availability.

        Returns:
            Dictionary containing:
                - success: Boolean indicating if the operation succeeded
                - cameras: List of camera dictionaries with details (only present on success)
                    - name: Camera name/identifier
                    - type: Camera type (tapo, webcam, ring, etc.)
                    - status: Connection status ("online", "offline", "error")
                    - model: Camera model information
                    - firmware: Camera firmware version
                    - streaming: Boolean indicating if camera is currently streaming
                    - error: Error message (only present when status is "error")
                - total: Total number of cameras found

        Usage:
            Use this tool to get an overview of all configured cameras before
            performing operations. This is typically the first tool called to
            understand what cameras are available in the system.

            Common scenarios:
                - Initial setup verification
                - Camera management dashboard
                - Troubleshooting connection issues
                - Inventory and status monitoring

        Examples:
            Basic usage:
                result = await list_cameras_tool.execute()
                if result['success']:
                    for camera in result['cameras']:
                        print(f"Camera: {camera['name']} - {camera['status']}")
                # Returns: {
                #     'success': True,
                #     'cameras': [
                #         {'name': 'front_door', 'type': 'tapo', 'status': 'online', 'model': 'C100', ...},
                #         {'name': 'backyard', 'type': 'webcam', 'status': 'offline', 'model': 'Unknown', ...}
                #     ],
                #     'total': 2
                # }

            Error handling:
                result = await list_cameras_tool.execute()
                if not result['success']:
                    print("Failed to list cameras")
                # Returns: {'success': False, 'cameras': [], 'total': 0}

        Raises:
            Exception: Propagated from camera operations (connection failures, authentication errors)

        Notes:
            - Cameras are listed regardless of connection status
            - Status is determined by last known connection state
            - Network connectivity is tested during status checks
            - Results include cameras that failed to connect with error details

        See Also:
            - add_camera_tool: For adding new cameras to the system
            - remove_camera_tool: For removing cameras from the system
            - get_camera_status_tool: For detailed status of specific cameras
        """
        from tapo_camera_mcp.core.server import (
            TapoCameraServer,
        )  # Lazy import to avoid circular imports

        server = await TapoCameraServer.get_instance()

        try:
            # Get real camera manager and list all cameras
            if hasattr(server, "camera_manager") and server.camera_manager:
                cameras = []
                for camera_name, camera in server.camera_manager.cameras.items():
                    try:
                        status = await camera.get_status()
                        cameras.append(
                            {
                                "name": camera_name,
                                "type": camera.config.type.value
                                if hasattr(camera.config, "type")
                                else "unknown",
                                "status": "online"
                                if status.get("connected", False)
                                else "offline",
                                "model": status.get("model", "Unknown"),
                                "firmware": status.get("firmware", "Unknown"),
                                "streaming": status.get("streaming", False),
                            }
                        )
                    except Exception as e:
                        logger.warning(
                            f"Failed to get status for camera {camera_name}: {e}"
                        )
                        cameras.append(
                            {
                                "name": camera_name,
                                "type": "unknown",
                                "status": "error",
                                "error": str(e),
                            }
                        )

                return {"success": True, "cameras": cameras, "total": len(cameras)}
            else:
                return {
                    "success": True,
                    "cameras": [],
                    "total": 0,
                    "message": "No camera manager initialized",
                }
        except Exception as e:
            logger.error(f"Failed to list cameras: {e}")
            return {
                "success": False,
                "error": f"Failed to list cameras: {str(e)}",
                "cameras": [],
            }


@tool("add_camera")
class AddCameraTool(BaseTool):
    """
    Add a new camera to the system.

    Supports multiple camera types: Tapo IP cameras, Ring doorbells,
    and USB webcams. Each camera type requires different connection parameters.

    Parameters:
        camera_id (str): Unique identifier for the camera
        camera_type (str): Type - 'Tapo', 'Ring', or 'Webcam'
        host (str, optional): IP address for Tapo cameras
        username (str, optional): Username for authentication
        password (str, optional): Password for authentication
        device_id (int, optional): Device ID for webcams (default: 0)

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
    """

    class Meta:
        name = "add_camera"
        description = "Add a new camera to the system"
        category = ToolCategory.CAMERA

        class Parameters:
            camera_name: str = Field(..., description="A friendly name for the camera")
            ip_address: str = Field(..., description="IP address of the camera")
            username: str = Field(..., description="Username for camera authentication")
            password: str = Field(..., description="Password for camera authentication")
            stream_url: Optional[str] = Field(
                None, description="Optional custom RTSP stream URL"
            )

    camera_name: str
    ip_address: str
    username: str
    password: str
    stream_url: Optional[str] = None

    async def execute(self) -> Dict[str, Any]:
        """Add a new camera to the system with full configuration support.

        Registers and connects to a new camera device using the provided configuration
        parameters. The camera will be added to the system's camera registry and made
        available for streaming, recording, and control operations. Supports Tapo IP cameras
        with comprehensive validation and connection testing.

        Parameters:
            camera_name: Friendly name for the camera (required)
                - Must be unique and contain only alphanumeric characters and underscores
                - Used as the primary identifier for camera operations
                - Maximum 50 characters
            ip_address: IP address of the camera (required)
                - Must be a valid IPv4 address
                - Camera must be accessible on the network
                - Format: xxx.xxx.xxx.xxx
            username: Camera authentication username (required)
                - Login credential for camera access
                - Typically "admin" for Tapo cameras
            password: Camera authentication password (required)
                - Password credential for camera access
                - Stored securely in the configuration
            stream_url: Optional custom RTSP stream URL
                - If provided, overrides automatic stream URL detection
                - Must be a valid RTSP URL if specified

        Returns:
            Dictionary containing:
                - success: Boolean indicating if camera was added successfully
                - camera_name: Name of the added camera
                - camera_type: Type of camera added ("tapo")
                - ip_address: IP address of the camera
                - message: Success confirmation or error description
                - stream_url: Detected or provided stream URL (on success)

        Usage:
            Use this tool to register new Tapo IP cameras in the system. Ensure the camera
            is powered on, connected to the network, and accessible before adding. The tool
            performs comprehensive validation and connection testing.

            Common scenarios:
                - Initial system setup with multiple cameras
                - Adding replacement cameras
                - Expanding camera coverage
                - Testing new camera installations

        Examples:
            Add a camera successfully:
                result = await add_camera_tool.execute(
                    camera_name='front_door',
                    ip_address='192.168.1.100',
                    username='admin',
                    password='secure_password_123'
                )
                if result['success']:
                    print(f"Camera {result['camera_name']} added successfully")
                # Returns: {
                #     'success': True,
                #     'camera_name': 'front_door',
                #     'camera_type': 'tapo',
                #     'ip_address': '192.168.1.100',
                #     'message': 'Camera front_door added successfully',
                #     'stream_url': 'rtsp://192.168.1.100:554/stream1'
                # }

            Error handling - invalid IP:
                result = await add_camera_tool.execute(
                    camera_name='test_cam',
                    ip_address='999.999.999.999',
                    username='admin',
                    password='password'
                )
                # Returns: {
                #     'success': False,
                #     'message': 'Invalid IP address format: 999.999.999.999'
                # }

            Error handling - camera unreachable:
                result = await add_camera_tool.execute(
                    camera_name='offline_cam',
                    ip_address='192.168.1.200',
                    username='admin',
                    password='password'
                )
                # Returns: {
                #     'success': False,
                #     'message': 'Failed to connect to camera at 192.168.1.200: Connection timeout'
                # }

            With custom stream URL:
                result = await add_camera_tool.execute(
                    camera_name='custom_cam',
                    ip_address='192.168.1.150',
                    username='admin',
                    password='password',
                    stream_url='rtsp://192.168.1.150:554/custom_stream'
                )
                # Uses the provided stream_url instead of auto-detecting

        Raises:
            Exception: Propagated from camera operations (network connectivity, authentication failures)

        Notes:
            - Camera names must be unique within the system
            - Authentication credentials are validated during addition
            - Camera connectivity is tested before final registration
            - Failed additions don't leave partial configurations
            - Stream URL is automatically detected if not provided
            - Supports only Tapo cameras in current implementation

        See Also:
            - list_cameras_tool: To verify camera was added successfully
            - remove_camera_tool: To remove cameras from the system
            - get_camera_status_tool: To check camera connection status
        """
        try:
            # Validate inputs
            camera_name = validate_camera_name(self.camera_name, "camera_name")
            ip_address = validate_ip_address(self.ip_address, "ip_address")
            username, password = validate_credentials(self.username, self.password)

            logger.info(f"Adding camera: {camera_name} at {ip_address}")

            from tapo_camera_mcp.core.server import (
                TapoCameraServer,
            )  # Lazy import to avoid circular imports

            server = await TapoCameraServer.get_instance()

            result = await server.add_camera(
                camera_name=camera_name,
                camera_type="tapo",  # Assuming Tapo camera for now
                host=ip_address,
                username=username,
                password=password,
                stream_url=self.stream_url,
            )

            logger.info(f"Successfully added camera: {camera_name}")
            return result

        except ToolValidationError as e:
            logger.warning(
                f"Validation error adding camera {self.camera_name}: {e.message}"
            )
            return {
                "success": False,
                "error": f"Validation error: {e.message}",
                "field": e.field,
            }
        except Exception as e:
            logger.error(f"Failed to add camera {self.camera_name}: {e}")
            return {"success": False, "error": f"Failed to add camera: {str(e)}"}


@tool("remove_camera")
class RemoveCameraTool(BaseTool):
    """
    Remove a camera from the system.

    Disconnects and removes a camera from the managed camera list.

    Parameters:
        camera_name (str): Name of the camera to remove

    Returns:
        Dict with success status and confirmation message

    Example:
        result = await remove_camera_tool.execute(camera_name='webcam1')
    """

    class Meta:
        name = "remove_camera"
        description = "Remove a camera from the system"
        category = ToolCategory.CAMERA

        class Parameters:
            camera_id: str = Field(..., description="ID of the camera to remove")

    camera_id: str

    async def execute(self) -> Dict[str, Any]:
        """Remove a camera from the system."""
        from tapo_camera_mcp.core.server import (
            TapoCameraServer,
        )  # Lazy import to avoid circular imports

        server = await TapoCameraServer.get_instance()
        return await server.remove_camera(camera_id=self.camera_id)


@tool("set_active_camera")
class SetActiveCameraTool(BaseTool):
    """
    Set the active camera for subsequent operations.

    Designates which camera will be used for commands that don't
    specify a camera explicitly.

    Parameters:
        camera_name (str): Name of the camera to set as active

    Returns:
        Dict with success status and active camera name

    Example:
        result = await set_active_camera_tool.execute(camera_name='tapo_front')
    """

    class Meta:
        name = "set_active_camera"
        description = "Set the active camera for operations"
        category = ToolCategory.CAMERA

        class Parameters:
            name: str = Field(
                ..., description="Name or ID of the camera to set as active"
            )

    name: str

    async def execute(self) -> Dict[str, Any]:
        """Set the active camera for operations."""
        from tapo_camera_mcp.core.server import (
            TapoCameraServer,
        )  # Lazy import to avoid circular imports

        server = await TapoCameraServer.get_instance()
        return await server.set_active_camera(name=self.name)


@tool("get_camera_status")
class GetCameraStatusTool(BaseTool):
    """
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
    """

    class Meta:
        name = "get_camera_status"
        description = "Get the status of a specific camera"
        category = ToolCategory.CAMERA

        class Parameters:
            camera_id: str = Field(
                None,
                description="ID of the camera to get status for. If not provided, returns status of active camera.",
            )

    camera_id: Optional[str] = None

    async def execute(self) -> Dict[str, Any]:
        """Get the status of a specific camera."""
        from tapo_camera_mcp.core.server import (
            TapoCameraServer,
        )  # Lazy import to avoid circular imports

        server = await TapoCameraServer.get_instance()
        return (
            await server.get_camera_status(name=self.camera_id)
            if self.camera_id
            else await server.get_active_camera_status()
        )


@tool("connect_camera")
class ConnectCameraTool(BaseTool):
    """
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
    """

    class Meta:
        name = "connect_camera"
        description = "Connect to a Tapo camera"
        category = ToolCategory.CAMERA

        class Parameters:
            host: str = Field(..., description="IP address or hostname of the camera")
            username: str = Field(..., description="Username for camera authentication")
            password: str = Field(..., description="Password for camera authentication")
            verify_ssl: bool = Field(
                True, description="Whether to verify SSL certificates (default: True)"
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

            from tapo_camera_mcp.core.server import (
                TapoCameraServer,
            )  # Lazy import to avoid circular imports

            server = await TapoCameraServer.get_instance()

            result = await server.connect_camera(
                host=host,
                username=username,
                password=password,
                verify_ssl=self.verify_ssl,
            )

            logger.info(f"Successfully connected to camera at {host}")
            return result

        except ToolValidationError as e:
            logger.warning(
                f"Validation error connecting to camera {self.host}: {e.message}"
            )
            return {
                "success": False,
                "error": f"Validation error: {e.message}",
                "field": e.field,
            }
        except ConnectionError as e:
            logger.error(f"Connection failed to camera {self.host}: {e}")
            return {"success": False, "error": f"Connection failed: {str(e)}"}
        except AuthenticationError as e:
            logger.error(f"Authentication failed for camera {self.host}: {e}")
            return {"success": False, "error": f"Authentication failed: {str(e)}"}
        except Exception as e:
            logger.error(f"Unexpected error connecting to camera {self.host}: {e}")
            return {"success": False, "error": f"Connection error: {str(e)}"}


@tool("disconnect_camera")
class DisconnectCameraTool(BaseTool):
    """
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
    """

    class Meta:
        name = "disconnect_camera"
        description = "Disconnect from the current camera"
        category = ToolCategory.CAMERA

        class Parameters:
            pass

    async def execute(self) -> Dict[str, Any]:
        """Disconnect from the current camera."""
        from tapo_camera_mcp.core.server import (
            TapoCameraServer,
        )  # Lazy import to avoid circular imports

        server = await TapoCameraServer.get_instance()
        return await server.disconnect_camera()


@tool("get_camera_info")
class GetCameraInfoTool(BaseTool):
    """
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
    """

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
        from tapo_camera_mcp.core.server import (
            TapoCameraServer,
        )  # Lazy import to avoid circular imports

        server = await TapoCameraServer.get_instance()
        return await server.get_camera_info()


@tool("manage_camera_groups")
class ManageCameraGroupsTool(BaseTool):
    """
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
    """

    class Meta:
        name = "manage_camera_groups"
        description = "Manage camera groups"
        category = ToolCategory.CAMERA

        class Parameters:
            action: Literal["list", "add", "remove", "list_group"] = Field(
                ..., description="Action to perform"
            )
            group: Optional[str] = Field(
                None, description="Group name (required for add/remove/list_group)"
            )
            camera: Optional[str] = Field(
                None, description="Camera name (required for add/remove)"
            )

    action: str
    group: Optional[str] = None
    camera: Optional[str] = None

    async def execute(self) -> Dict[str, Any]:
        """Manage camera groups."""
        from tapo_camera_mcp.core.server import (
            TapoCameraServer,
        )  # Lazy import to avoid circular imports

        server = await TapoCameraServer.get_instance()

        if self.action == "list":
            return await server.list_camera_groups()
        elif self.action == "list_group":
            if not self.group:
                raise ValueError("Group name is required for list_group action")
            return await server.list_cameras_in_group(self.group)
        elif self.action == "add":
            if not self.group or not self.camera:
                raise ValueError(
                    "Both group name and camera name are required for add action"
                )
            return await server.add_camera_to_group(self.camera, self.group)
        elif self.action == "remove":
            if not self.group or not self.camera:
                raise ValueError(
                    "Both group name and camera name are required for remove action"
                )
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
    ListCamerasTool,
    AddCameraTool,
    RemoveCameraTool,
    SetActiveCameraTool,
    GetCameraStatusTool,
    ConnectCameraTool,
    DisconnectCameraTool,
    GetCameraInfoTool,
    ManageCameraGroupsTool,
]
logger.debug(
    f"Registered camera tools: {[tool.Meta.name for tool in camera_tool_classes]}"
)
