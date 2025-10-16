import asyncio
import logging
import sys
from pathlib import Path

# Add the src directory to the Python path
src_path = Path(__file__).parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from fastmcp.server import FastMCP

from tapo_camera_mcp.camera.manager import CameraManager
from tapo_camera_mcp.tools.base_tool import ToolResult
from tapo_camera_mcp.tools.discovery import discover_tools

# Optional camera imports - handle missing dependencies gracefully
try:
    from tapo_camera_mcp.camera.ring import RingCamera
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.warning(f"Ring camera support unavailable: {e}")
    RingCamera = None

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

        # Load cameras from config
        from ..config import get_config

        config = get_config()
        camera_configs = config.get("cameras", {})

        # Convert config format to camera configs
        if camera_configs:
            logger.info(f"Loading {len(camera_configs)} cameras from configuration...")
            for camera_name, camera_config in camera_configs.items():
                try:
                    # Add name to config if not present
                    if "name" not in camera_config:
                        camera_config["name"] = camera_name

                    success = await self.camera_manager.add_camera(camera_config)
                    if success:
                        logger.info(f"Loaded camera: {camera_name}")
                    else:
                        logger.warning(f"Failed to load camera: {camera_name}")
                except Exception as e:
                    logger.exception(f"Error loading camera {camera_name}: {e}")

        # Register all tools
        await self._register_tools()

        self._initialized = True
        logger.info("Tapo Camera MCP Server initialized successfully")

    async def _register_tools(self):
        """Register all tools with the MCP server using FastMCP 2.12 patterns."""
        # Discover and register all tools from the tools package
        tools = discover_tools("tapo_camera_mcp.tools")

        # Deduplicate tools by name to avoid registering the same tool twice
        seen_tools = set()
        unique_tools = []
        for tool_cls in tools:
            tool_meta = getattr(tool_cls, "Meta", None)
            if tool_meta:
                tool_name = getattr(
                    tool_meta, "name", tool_cls.__name__.replace("Tool", "").lower()
                )
                if tool_name not in seen_tools:
                    seen_tools.add(tool_name)
                    unique_tools.append(tool_cls)

        logger.info(f"Discovered {len(tools)} tools, registering {len(unique_tools)} unique tools")

        for tool_cls in unique_tools:
            # Get tool metadata from the class
            tool_meta = getattr(tool_cls, "Meta", None)
            if not tool_meta:
                logger.warning(f"Tool {tool_cls.__name__} is missing Meta class, skipping")
                continue

            tool_name = getattr(tool_meta, "name", tool_cls.__name__.replace("Tool", "").lower())
            tool_description = getattr(tool_meta, "description", "")

            logger.debug(f"Registering tool: {tool_name}")

            # Create a simple wrapper function using closures

            # Extract parameter names from the tool class
            param_names = []
            if hasattr(tool_meta, "Parameters"):
                # Extract parameter names from the Parameters class
                params_class = tool_meta.Parameters
                for attr_name in dir(params_class):
                    if not attr_name.startswith("_") and not callable(
                        getattr(params_class, attr_name)
                    ):
                        param_names.append(attr_name)
            elif hasattr(tool_cls, "model_fields"):
                # Extract from Pydantic V2 model_fields
                param_names = list(tool_cls.model_fields.keys())
            elif hasattr(tool_cls, "__fields__"):
                # Fallback for Pydantic V1 __fields__
                param_names = list(tool_cls.__fields__.keys())

            # Create wrapper function with explicit parameters
            if param_names:
                # Create parameter signature
                param_list = [f"{name}" for name in param_names]
                param_signature = ", ".join(param_list)

                # Get the docstring
                docstring = (
                    tool_cls.execute.__doc__
                    if hasattr(tool_cls, "execute") and tool_cls.execute.__doc__
                    else "Tool execution"
                )

                # Create kwargs assignments
                kwargs_lines = "\n".join(
                    [f"        kwargs['{name}'] = {name}" for name in param_names]
                )

                # Create the function code using string formatting
                func_code = (
                    """
async def tool_wrapper("""
                    + param_signature
                    + '''):
    """'''
                    + docstring
                    + '''"""
    try:
        # Create kwargs dict from parameters
        kwargs = {}
'''
                    + kwargs_lines
                    + """

        # Create tool instance with parameters
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
            raise ValueError("Tool """
                    + tool_name
                    + """ has no execute method")

    except Exception as e:
        error_msg = "Error executing tool """
                    + tool_name
                    + """: {}".format(e)
        logger.error(error_msg)
        logger.exception("Full traceback:")
        return {
            "content": error_msg,
            "is_error": True
        }
"""
                )

                # Execute the function code
                local_vars = {
                    "tool_cls": tool_cls,
                    "tool_name": tool_name,
                    "asyncio": asyncio,
                    "ToolResult": ToolResult,
                    "logger": logger,
                }
                exec(func_code, local_vars)
                wrapper_func = local_vars["tool_wrapper"]
            else:
                # No parameters - simple wrapper
                async def wrapper_func():
                    """{tool_cls.execute.__doc__ if hasattr(tool_cls, 'execute') and tool_cls.execute.__doc__ else 'Tool execution'}"""
                    try:
                        # Create tool instance
                        tool_instance = tool_cls()

                        # If the tool has an async initialize method, call it
                        if hasattr(tool_instance, "initialize") and callable(
                            tool_instance.initialize
                        ):
                            if asyncio.iscoroutinefunction(tool_instance.initialize):
                                await tool_instance.initialize()
                            else:
                                tool_instance.initialize()

                        # Call the tool's execute method
                        if hasattr(tool_instance, "execute"):
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
                                    "is_error": result.is_error,
                                }
                            if isinstance(result, dict):
                                return result
                            return {"content": str(result), "is_error": False}
                        raise ValueError(f"Tool {tool_name} has no execute method")

                    except Exception as e:
                        error_msg = f"Error executing tool {tool_name}: {e}"
                        logger.exception(error_msg)
                        logger.exception("Full traceback:")
                        return {"content": error_msg, "is_error": True}

                wrapper_func = wrapper_func

            # Register the tool
            self.mcp.tool(tool_name, description=tool_description)(wrapper_func)
            logger.debug(f"Successfully registered tool: {tool_name}")

    async def run(
        self,
        host: str = "0.0.0.0",  # nosec B104
        port: int = 8000,
        stdio: bool = False,
        direct: bool = False,
    ):
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
            # Note: HTTP mode would need additional implementation
            await self.mcp.run_stdio_async()  # Fallback to stdio for now


# Convenience function for getting server instance
async def get_server():
    """Get the TapoCameraServer instance."""
    return await TapoCameraServer.get_instance()
