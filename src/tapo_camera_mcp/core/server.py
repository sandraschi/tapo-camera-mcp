import asyncio
import logging
import os
import sys
from typing import Dict, Any, Optional, List
from pathlib import Path

# Add the src directory to the Python path
src_path = Path(__file__).parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from fastmcp.server import FastMCP
from tapo_camera_mcp.tools.discovery import discover_tools
from tapo_camera_mcp.tools.base_tool import ToolResult
from tapo_camera_mcp.camera.manager import CameraManager
from tapo_camera_mcp.camera.webcam import WebCamera
from tapo_camera_mcp.camera.tapo import Tapo
from tapo_camera_mcp.camera.base import CameraType, CameraConfig

# Optional camera imports - handle missing dependencies gracefully
try:
    from tapo_camera_mcp.camera.ring import RingCamera
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.warning(f"Ring camera support unavailable: {e}")
    RingCamera = None

try:
    from tapo_camera_mcp.camera.furbo import FurboCamera
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.warning(f"Furbo camera support unavailable: {e}")
    FurboCamera = None

# Setup logging
logger = logging.getLogger(__name__)

class TapoCameraServer:
    """Main MCP server for Tapo Camera management."""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    async def get_instance(cls):
        """Get or create the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        if not cls._initialized:
            await cls._instance.initialize()
        return cls._instance
    
    async def initialize(self):
        """Initialize the server."""
        if self._initialized:
            return
            
        logger.info("Initializing Tapo Camera MCP Server...")
        
        # Initialize FastMCP server
        self.mcp = FastMCP("tapo-camera-mcp")
        
        # Initialize camera manager
        self.camera_manager = CameraManager()
        
        # Register all tools
        await self._register_tools()
        
        self._initialized = True
        logger.info("Tapo Camera MCP Server initialized successfully")
    
    async def _register_tools(self):
        """Register all tools with the MCP server using FastMCP 2.12 patterns."""
        # Discover and register all tools from the tools package
        tools = discover_tools('tapo_camera_mcp.tools')
        
        # Deduplicate tools by name to avoid registering the same tool twice
        seen_tools = set()
        unique_tools = []
        for tool_cls in tools:
            tool_meta = getattr(tool_cls, 'Meta', None)
            if tool_meta:
                tool_name = getattr(tool_meta, 'name', tool_cls.__name__.replace('Tool', '').lower())
                if tool_name not in seen_tools:
                    seen_tools.add(tool_name)
                    unique_tools.append(tool_cls)
        
        logger.info(f"Discovered {len(tools)} tools, registering {len(unique_tools)} unique tools")
        
        for tool_cls in unique_tools:
            # Get tool metadata from the class
            tool_meta = getattr(tool_cls, 'Meta', None)
            if not tool_meta:
                logger.warning(f"Tool {tool_cls.__name__} is missing Meta class, skipping")
                continue
                
            tool_name = getattr(tool_meta, 'name', tool_cls.__name__.replace('Tool', '').lower())
            tool_description = getattr(tool_meta, 'description', '')
            
            logger.debug(f"Registering tool: {tool_name}")
            
            # Get parameter names from the tool class
            param_names = []
            if hasattr(tool_meta, 'Parameters'):
                # Extract parameter names from the Parameters class
                params_class = tool_meta.Parameters
                for attr_name in dir(params_class):
                    if not attr_name.startswith('_') and not callable(getattr(params_class, attr_name)):
                        param_names.append(attr_name)
            elif hasattr(tool_cls, '__fields__'):
                # Extract from Pydantic fields
                param_names = list(tool_cls.__fields__.keys())
            
            # Create a wrapper function for FastMCP 2.12 with explicit parameters
            if param_names:
                # Create a function with explicit parameters using exec
                param_str = ', '.join(param_names)
                func_code = f"""
async def tool_wrapper({param_str}):
    \"\"\"Wrapper function for tool execution.\"\"\"
    try:
        # Create tool instance with provided parameters
        kwargs = {{{', '.join([f"'{name}': {name}" for name in param_names])}}}
        tool_instance = tool_cls(**kwargs)
        
        # If the tool has an async initialize method, call it
        if hasattr(tool_instance, 'initialize') and callable(tool_instance.initialize):
            if asyncio.iscoroutinefunction(tool_instance.initialize):
                await tool_instance.initialize()
            else:
                tool_instance.initialize()
        
        # Call the tool's execute method
        if hasattr(tool_instance, 'execute'):
            execute_method = tool_instance.execute
            
            # Handle both sync and async execute methods
            if asyncio.iscoroutinefunction(execute_method):
                result = await execute_method()
            else:
                result = execute_method()
                
            # Handle the result
            if isinstance(result, ToolResult):
                return {{
                    "content": result.content,
                    "is_error": result.is_error
                }}
            elif isinstance(result, dict):
                return result
            else:
                return {{
                    "content": str(result),
                    "is_error": False
                }}
        else:
            raise ValueError(f"Tool {{tool_name}} has no execute method")
            
    except Exception as e:
        error_msg = f"Error executing tool {{tool_name}}: {{e}}"
        logger.error(error_msg)
        logger.exception("Full traceback:")
        return {{
            "content": error_msg,
            "is_error": True
        }}
"""
                # Execute the function definition with proper variable capture
                local_vars = {
                    'tool_cls': tool_cls, 
                    'tool_name': tool_name, 
                    'asyncio': asyncio, 
                    'ToolResult': ToolResult, 
                    'logger': logger
                }
                exec(func_code, local_vars, local_vars)
                wrapper_func = local_vars['tool_wrapper']
            else:
                # No parameters - create wrapper directly
                async def wrapper_func():
                    """Wrapper function for tool execution."""
                    try:
                        # Create tool instance
                        tool_instance = tool_cls()
                        
                        # If the tool has an async initialize method, call it
                        if hasattr(tool_instance, 'initialize') and callable(tool_instance.initialize):
                            if asyncio.iscoroutinefunction(tool_instance.initialize):
                                await tool_instance.initialize()
                            else:
                                tool_instance.initialize()
                        
                        # Call the tool's execute method
                        if hasattr(tool_instance, 'execute'):
                            execute_method = tool_instance.execute
                            
                            # Handle both sync and async execute methods
                            if asyncio.iscoroutinefunction(execute_method):
                                result = await execute_method()
                            else:
                                result = execute_method()
                                
                            # Handle the result
                            if isinstance(result, ToolResult):
                                return {
                                    "content": result.content,
                                    "is_error": result.is_error
                                }
                            elif isinstance(result, dict):
                                return result
                            else:
                                return {
                                    "content": str(result),
                                    "is_error": False
                                }
                        else:
                            raise ValueError(f"Tool {tool_name} has no execute method")
                            
                    except Exception as e:
                        error_msg = f"Error executing tool {tool_name}: {e}"
                        logger.error(error_msg)
                        logger.exception("Full traceback:")
                        return {
                            "content": error_msg,
                            "is_error": True
                        }
            
            # Register the tool with FastMCP 2.12 using the decorator method
            self.mcp.tool(tool_name, description=tool_description)(wrapper_func)
            
            logger.debug(f"Successfully registered tool: {tool_name}")
    
    async def run(self, host: str = "0.0.0.0", port: int = 8000, stdio: bool = False, direct: bool = False):
        """Run the MCP server."""
        logger.info(f"Starting Tapo Camera MCP Server on {host}:{port}")
        
        if direct:
            # Direct mode for Claude Desktop
            logger.info("Running in direct mode for Claude Desktop")
            await self.mcp.run_stdio_async()
        elif stdio:
            # Standard stdio mode
            logger.info("Running in stdio mode")
            await self.mcp.run_stdio_async()
        else:
            # HTTP mode
            logger.info("Running in HTTP mode")
            await self.mcp.run_streamable_http_async(host=host, port=port)
    
    # Camera management methods
    async def add_camera(self, camera_name: str, camera_type: str, **kwargs) -> Dict[str, Any]:
        """Add a new camera to the manager."""
        try:
            # Map string type to enum
            type_map = {
                'tapo': CameraType.TAPO,
                'webcam': CameraType.WEBCAM,
                'ring': CameraType.RING,
                'furbo': CameraType.FURBO
            }
            
            if camera_type.lower() not in type_map:
                return {
                    "success": False,
                    "error": f"Unsupported camera type: {camera_type}. Supported types: {list(type_map.keys())}"
                }
            
            camera_type_enum = type_map[camera_type.lower()]
            
            # Create camera instance based on type
            if camera_type_enum == CameraType.WEBCAM:
                device_id = kwargs.get('device_id', 0)
                config = CameraConfig(
                    name=camera_name,
                    type=camera_type_enum,
                    params={'device_id': device_id}
                )
                camera = WebCamera(config)
            elif camera_type_enum == CameraType.TAPO:
                config = CameraConfig(
                    name=camera_name,
                    type=camera_type_enum,
                    params={
                        'host': kwargs.get('host', ''),
                        'username': kwargs.get('username', ''),
                        'password': kwargs.get('password', '')
                    }
                )
                camera = Tapo(config)
            elif camera_type_enum == CameraType.RING:
                config = CameraConfig(
                    name=camera_name,
                    type=camera_type_enum,
                    params=kwargs
                )
                camera = RingCamera(config)
            elif camera_type_enum == CameraType.FURBO:
                config = CameraConfig(
                    name=camera_name,
                    type=camera_type_enum,
                    params=kwargs
                )
                camera = FurboCamera(config)
            else:
                return {
                    "success": False,
                    "error": f"Camera type {camera_type} not implemented"
                }
            
            # Add to manager
            await self.camera_manager.add_camera(config)
            
            return {
                "success": True,
                "message": f"Camera '{camera_name}' added successfully",
                "camera_type": camera_type,
                "camera_name": camera_name
            }
            
        except Exception as e:
            logger.error(f"Error adding camera: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def list_cameras(self) -> Dict[str, Any]:
        """List all cameras."""
        try:
            cameras = await self.camera_manager.list_cameras()
            return {
                "success": True,
                "cameras": cameras,
                "total": len(cameras)
            }
        except Exception as e:
            logger.error(f"Error listing cameras: {e}")
            return {
                "success": False,
                "error": str(e),
                "cameras": [],
                "total": 0
            }
    
    async def connect_camera(self, camera_name: str) -> Dict[str, Any]:
        """Connect to a specific camera."""
        try:
            camera = await self.camera_manager.get_camera(camera_name)
            if not camera:
                return {
                    "success": False,
                    "error": f"Camera '{camera_name}' not found"
                }
            
            await camera.connect()
            return {
                "success": True,
                "message": f"Connected to camera '{camera_name}'"
            }
            
        except Exception as e:
            logger.error(f"Error connecting to camera: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def disconnect_camera(self, camera_name: str) -> Dict[str, Any]:
        """Disconnect from a specific camera."""
        try:
            camera = await self.camera_manager.get_camera(camera_name)
            if not camera:
                return {
                    "success": False,
                    "error": f"Camera '{camera_name}' not found"
                }
            
            await camera.disconnect()
            return {
                "success": True,
                "message": f"Disconnected from camera '{camera_name}'"
            }
            
        except Exception as e:
            logger.error(f"Error disconnecting from camera: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def capture_image(self, camera_name: str, **kwargs) -> Dict[str, Any]:
        """Capture an image from a specific camera."""
        try:
            camera = await self.camera_manager.get_camera(camera_name)
            if not camera:
                return {
                    "success": False,
                    "error": f"Camera '{camera_name}' not found"
                }
            
            # Ensure camera is connected
            if not await camera.is_connected():
                await camera.connect()
            
            # Capture image
            image_data = await camera.capture_still()
            
            return {
                "success": True,
                "image_data": image_data,
                "camera_name": camera_name
            }
            
        except Exception as e:
            logger.error(f"Error capturing image: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_camera_info(self, camera_name: str) -> Dict[str, Any]:
        """Get information about a specific camera."""
        try:
            camera = await self.camera_manager.get_camera(camera_name)
            if not camera:
                return {
                    "success": False,
                    "error": f"Camera '{camera_name}' not found"
                }
            
            info = await camera.get_info()
            return {
                "success": True,
                "info": info,
                "camera_name": camera_name
            }
            
        except Exception as e:
            logger.error(f"Error getting camera info: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_camera_status(self, camera_name: str) -> Dict[str, Any]:
        """Get status of a specific camera."""
        try:
            camera = await self.camera_manager.get_camera(camera_name)
            if not camera:
                return {
                    "success": False,
                    "error": f"Camera '{camera_name}' not found"
                }
            
            status = await camera.get_status()
            return {
                "success": True,
                "status": status,
                "camera_name": camera_name
            }
            
        except Exception as e:
            logger.error(f"Error getting camera status: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def remove_camera(self, camera_name: str) -> Dict[str, Any]:
        """Remove a camera from the manager."""
        try:
            await self.camera_manager.remove_camera(camera_name)
            return {
                "success": True,
                "message": f"Camera '{camera_name}' removed successfully"
            }
            
        except Exception as e:
            logger.error(f"Error removing camera: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_system_info(self) -> Dict[str, Any]:
        """Get system information."""
        try:
            import platform
            import psutil
            
            return {
                "success": True,
                "system_info": {
                    "platform": platform.platform(),
                    "python_version": platform.python_version(),
                    "cpu_count": psutil.cpu_count(),
                    "memory_total": psutil.virtual_memory().total,
                    "memory_available": psutil.virtual_memory().available,
                    "disk_usage": psutil.disk_usage('/').percent if os.name != 'nt' else psutil.disk_usage('C:').percent
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_help(self, tool_name: Optional[str] = None, category: Optional[str] = None) -> Dict[str, Any]:
        """Get help about available tools and their usage."""
        try:
            # Get all registered tools
            tools = await self.mcp.get_tools()
            
            help_data = {
                "success": True,
                "total_tools": len(tools),
                "tools": []
            }
            
            # Filter tools if requested
            filtered_tools = []
            for tool in tools:
                if isinstance(tool, str):
                    continue  # Skip string tool names
                    
                tool_info = {
                    "name": tool.name,
                    "description": tool.description,
                    "category": getattr(tool, 'category', 'Unknown')
                }
                
                # Add parameters if available
                if hasattr(tool, 'parameters') and tool.parameters:
                    tool_info["parameters"] = []
                    for param in tool.parameters:
                        if isinstance(param, dict):
                            tool_info["parameters"].append({
                                "name": param.get('name', 'unknown'),
                                "description": param.get('description', 'No description'),
                                "required": param.get('required', False),
                                "type": param.get('type', 'string')
                            })
                        else:
                            tool_info["parameters"].append({
                                "name": getattr(param, 'name', 'unknown'),
                                "description": getattr(param, 'description', 'No description'),
                                "required": getattr(param, 'required', False),
                                "type": getattr(param, 'type', 'string')
                            })
                
                # Apply filters
                if tool_name and tool.name != tool_name:
                    continue
                if category and tool_info["category"] != category:
                    continue
                    
                filtered_tools.append(tool_info)
            
            help_data["tools"] = filtered_tools
            help_data["filtered_count"] = len(filtered_tools)
            
            # Add comprehensive usage examples
            help_data["usage_examples"] = [
                {
                    "tool": "add_camera",
                    "example": "Add a USB webcam: camera_type=webcam, name=my_webcam, device_id=0",
                    "description": "Connect a USB webcam to the system"
                },
                {
                    "tool": "list_cameras", 
                    "example": "No parameters required",
                    "description": "List all connected cameras"
                },
                {
                    "tool": "connect_camera",
                    "example": "Connect to Tapo: host=192.168.1.100, username=admin, password=password",
                    "description": "Connect to a Tapo IP camera"
                },
                {
                    "tool": "capture_image",
                    "example": "camera_id=my_webcam, save_to_disk=true",
                    "description": "Capture an image from a camera"
                },
                {
                    "tool": "get_camera_stream",
                    "example": "camera_id=my_webcam",
                    "description": "Get live video stream URL from a camera"
                },
                {
                    "tool": "move_ptz",
                    "example": "direction=up, speed=5",
                    "description": "Move PTZ camera (up, down, left, right, zoom_in, zoom_out)"
                },
                {
                    "tool": "save_ptz_preset",
                    "example": "preset_name=home_position",
                    "description": "Save current PTZ position as a preset"
                },
                {
                    "tool": "recall_ptz_preset",
                    "example": "preset_name=home_position",
                    "description": "Move PTZ camera to a saved preset position"
                }
            ]
            
            # Add dashboard information
            help_data["dashboard_info"] = {
                "url": "http://localhost:7777",
                "description": "Web-based camera management dashboard",
                "features": [
                    "Live video streaming from all connected cameras",
                    "Camera management (add, remove, configure)",
                    "Real-time camera status and information",
                    "PTZ control interface (coming soon)",
                    "Motion detection settings",
                    "System monitoring and logs"
                ],
                "how_to_start": [
                    "Run: python start.py dashboard",
                    "Or: python -m tapo_camera_mcp.web.server",
                    "Open browser to: http://localhost:7777"
                ],
                "supported_cameras": [
                    "USB Webcams (OpenCV)",
                    "Tapo IP Cameras (pytapo)",
                    "Ring Doorbell Cameras (ring-doorbell)",
                    "Furbo Pet Cameras (custom API)"
                ]
            }
            
            # Add PTZ tools information
            help_data["ptz_tools"] = {
                "description": "Pan-Tilt-Zoom camera control tools",
                "available_tools": [
                    {
                        "name": "move_ptz",
                        "description": "Move PTZ camera in any direction",
                        "parameters": {
                            "direction": "up, down, left, right, zoom_in, zoom_out",
                            "speed": "1-10 (optional, default: 5)"
                        }
                    },
                    {
                        "name": "save_ptz_preset",
                        "description": "Save current PTZ position as preset",
                        "parameters": {
                            "preset_name": "Name for the preset position"
                        }
                    },
                    {
                        "name": "recall_ptz_preset",
                        "description": "Move to saved preset position",
                        "parameters": {
                            "preset_name": "Name of preset to recall"
                        }
                    },
                    {
                        "name": "get_ptz_presets",
                        "description": "List all saved PTZ presets",
                        "parameters": "None"
                    },
                    {
                        "name": "go_to_home_ptz",
                        "description": "Move PTZ camera to home position",
                        "parameters": "None"
                    },
                    {
                        "name": "stop_ptz",
                        "description": "Stop all PTZ movement",
                        "parameters": "None"
                    },
                    {
                        "name": "get_ptz_position",
                        "description": "Get current PTZ position",
                        "parameters": "None"
                    }
                ],
                "dashboard_integration": {
                    "status": "Planned",
                    "description": "PTZ controls will be added to the web dashboard",
                    "features": [
                        "Visual PTZ control pad",
                        "Preset management interface",
                        "Real-time position display",
                        "Speed control slider"
                    ]
                }
            }
            
            # Add camera setup guide
            help_data["camera_setup_guide"] = {
                "usb_webcam": {
                    "steps": [
                        "1. Connect USB webcam to computer",
                        "2. Use add_camera tool: camera_type=webcam, name=my_webcam, device_id=0",
                        "3. Test with capture_image tool",
                        "4. View live stream in dashboard"
                    ],
                    "troubleshooting": [
                        "If device_id=0 doesn't work, try device_id=1 or 2",
                        "Check camera permissions in Windows",
                        "Ensure camera is not used by other applications"
                    ]
                },
                "tapo_camera": {
                    "steps": [
                        "1. Connect Tapo camera to WiFi network",
                        "2. Find camera IP address (check router admin panel)",
                        "3. Use connect_camera tool: host=192.168.1.100, username=admin, password=your_password",
                        "4. Test PTZ controls with move_ptz tool",
                        "5. View live stream in dashboard"
                    ],
                    "troubleshooting": [
                        "Ensure camera firmware is up to date",
                        "Check username/password are correct",
                        "Verify camera is on same network",
                        "Try different IP address if connection fails"
                    ]
                },
                "ring_camera": {
                    "steps": [
                        "1. Install Ring app and set up camera",
                        "2. Get Ring credentials (username/password)",
                        "3. Use connect_camera tool: camera_type=ring, username=your_email, password=your_password",
                        "4. Test with capture_image tool"
                    ],
                    "troubleshooting": [
                        "Ensure 2FA is disabled or use app password",
                        "Check Ring account is active",
                        "Verify camera is online in Ring app"
                    ]
                },
                "furbo_camera": {
                    "steps": [
                        "1. Set up Furbo camera with Furbo app",
                        "2. Get camera credentials and device ID",
                        "3. Use connect_camera tool: camera_type=furbo, device_id=your_device_id",
                        "4. Test with capture_image tool"
                    ],
                    "troubleshooting": [
                        "Verify Furbo account credentials",
                        "Check camera is online in Furbo app",
                        "Ensure device ID is correct"
                    ]
                }
            }
            
            return help_data
            
        except Exception as e:
            logger.error(f"Error getting help: {e}")
            return {
                "success": False,
                "error": str(e),
                "tools": [],
                "total_tools": 0
            }

# Convenience function for getting server instance
async def get_server():
    """Get the TapoCameraServer instance."""
    return await TapoCameraServer.get_instance()
