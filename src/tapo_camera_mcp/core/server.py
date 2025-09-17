"""
Tapo Camera MCP Server implementation.
"""
import logging
import asyncio
from typing import Dict, Any, List, Optional, Type, TypeVar
from pathlib import Path
import inspect
import asyncio

from fastmcp.server import FastMCP
from ..tools.discovery import discover_tools
from ..tools.base_tool import ToolResult, BaseTool

logger = logging.getLogger(__name__)


class TapoCameraServer:
    """Tapo Camera MCP Server."""
    
    _instance = None
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the Tapo Camera MCP server.
        
        Args:
            config: Optional configuration dictionary
        """
        # Initialize FastMCP with only the required parameters
        self.mcp = FastMCP("tapo-camera-mcp")
        self._initialized = False
        self.config = config or {}
        self.camera = None
        self._connected = False
    
    @classmethod
    async def get_instance(cls, config: Optional[Dict[str, Any]] = None) -> 'TapoCameraServer':
        """Get or create the singleton instance of TapoCameraServer.
        
        Args:
            config: Optional configuration dictionary
            
        Returns:
            TapoCameraServer: The singleton instance
        """
        if cls._instance is None:
            cls._instance = TapoCameraServer(config)
            await cls._instance.initialize()
        return cls._instance
        
    async def initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the server and register all tools.
        
        Args:
            config: Optional configuration dictionary to override the one passed to __init__
        """
        if self._initialized:
            return
            
        try:
            if config is not None:
                self.config.update(config)
                
            await self._register_tools()
            self._initialized = True
            logger.info("Tapo Camera MCP Server initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize server: {e}")
            raise
            
    async def connect(self) -> bool:
        """Connect to the Tapo camera.
        
        Returns:
            bool: True if connection was successful, False otherwise
        """
        try:
            if self._connected and self.camera is not None:
                return True
                
            if not self.config:
                raise ValueError("No configuration provided")
                
            # Import here to avoid circular imports
            from tapo_camera_mcp.camera.tapo import TapoCamera
            from tapo_camera_mcp.core.models import CameraConfig, CameraParams
            
            # Create camera config with params
            params = CameraParams(
                host=self.config.get('host'),
                username=self.config.get('username'),
                password=self.config.get('password'),
                port=self.config.get('port', 443),
                use_https=self.config.get('use_https', True),
                verify_ssl=self.config.get('verify_ssl', False),
                timeout=self.config.get('timeout', 10)
            )
            
            camera_config = CameraConfig(
                name="tapo_camera",
                type="tapo",
                params=params
            )
            
            self.camera = TapoCamera(camera_config)
            await self.camera.connect()
            self._connected = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to camera: {e}")
            self._connected = False
            self.camera = None
            raise
    
    async def disconnect(self) -> None:
        """Disconnect from the Tapo camera."""
        if self.camera:
            try:
                await self.camera.close()
            except Exception as e:
                logger.error(f"Error disconnecting from camera: {e}")
            finally:
                self.camera = None
                self._connected = False
    
    async def run(self, host: str = "0.0.0.0", port: int = 8000, stdio: bool = True, direct: bool = False) -> None:
        """Run the MCP server.
        
        Args:
            host: Host to bind the server to
            port: Port to bind the server to
            stdio: Whether to enable stdio transport
            direct: Whether to run in direct mode (for Claude Desktop)
        """
        if not self._initialized:
            await self.initialize()
            
        logger.info(f"Starting Tapo Camera MCP Server on {host}:{port}")
        
        if direct:
            # Direct mode for Claude Desktop - use stdio transport
            if stdio:
                await self.mcp.run_stdio_async()
            else:
                # Use streamable-http for direct mode without stdio
                await self.mcp.run_streamable_http_async(host=host, port=port)
        else:
            # Standard async mode
            loop = asyncio.get_event_loop()
            
            # Start HTTP server
            http_task = loop.create_task(self.mcp.run_http_async(host=host, port=port))
            
            # Start stdio server if enabled
            stdio_task = None
            if stdio:
                stdio_task = loop.create_task(self.mcp.run_stdio_async())
            
            try:
                # Run both servers
                tasks = [http_task]
                if stdio_task:
                    tasks.append(stdio_task)
                await asyncio.gather(*tasks)
            except KeyboardInterrupt:
                logger.info("Shutting down...")
                for task in asyncio.all_tasks(loop):
                    task.cancel()
                await loop.shutdown_asyncgens()
                loop.close()
        
    async def get_camera_info(self) -> Dict[str, Any]:
        """Get information about the connected camera.
        
        Returns:
            Dict containing camera information
            
        Raises:
            RuntimeError: If not connected to a camera
        """
        if not self._connected or self.camera is None:
            raise RuntimeError("Not connected to a camera")
            
        try:
            # Get basic camera info
            info = {
                "host": self.camera.host,
                "port": self.camera.port,
                "connected": self._connected,
            }
            
            # Try to get additional info if available
            try:
                if hasattr(self.camera, 'get_device_info'):
                    device_info = await self.camera.get_device_info()
                    info.update({
                        "model": device_info.get("model"),
                        "firmware_version": device_info.get("firmware_version"),
                        "serial_number": device_info.get("serial_number"),
                    })
                
                if hasattr(self.camera, 'get_basic_info'):
                    basic_info = await self.camera.get_basic_info()
                    info.update({
                        "name": basic_info.get("device_alias"),
                        "mac_address": basic_info.get("mac"),
                        "ip_address": basic_info.get("ip"),
                    })
                    
            except Exception as e:
                logger.warning(f"Could not get detailed camera info: {e}")
                
            return info
            
        except Exception as e:
            logger.error(f"Error getting camera info: {e}")
            raise
    
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
            def create_tool_wrapper(tool_cls, tool_name, param_names):
                """Create a tool wrapper function with explicit parameters."""
                
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
                    # Execute the function definition
                    local_vars = {'tool_cls': tool_cls, 'tool_name': tool_name, 'asyncio': asyncio, 'ToolResult': ToolResult, 'logger': logger}
                    exec(func_code, globals(), local_vars)
                    return local_vars['tool_wrapper']
                else:
                    # No parameters
                    async def tool_wrapper():
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
                    
                    return tool_wrapper
            
            # Create the wrapper function
            tool_wrapper = create_tool_wrapper(tool_cls, tool_name, param_names)
            
            # Register the tool with FastMCP 2.12 using the tool decorator method
            try:
                # Use FastMCP 2.12 tool decorator method
                decorated_tool = self.mcp.tool(
                    name=tool_name,
                    description=tool_description
                )(tool_wrapper)
                
                logger.debug(f"Successfully registered tool: {tool_name}")
                
            except Exception as e:
                logger.warning(f"Failed to register tool {tool_name}: {e}")
                continue
        
        logger.info(f"Registered {len(unique_tools)} tools")
    
    def get_mcp_server(self) -> FastMCP:
        """Get the FastMCP server instance."""
        return self.mcp


def get_server() -> TapoCameraServer:
    """Get a configured Tapo Camera MCP server instance."""
    return TapoCameraServer()


# For direct execution
async def main():
    """Main entry point."""
    server = get_server()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
