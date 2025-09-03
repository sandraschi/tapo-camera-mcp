"""
Tapo-Camera-MCP - FastMCP 2.12 server for controlling TP-Link Tapo cameras.

This is a refactored version with a modular tools architecture.
"""
import asyncio
import logging
import sys
import threading
from pathlib import Path
from typing import Any, Dict, Optional, Union, List, Type

from fastmcp import FastMCP
from pydantic import BaseModel, Field, HttpUrl

# Import web server
from ..web.server import WebServer

# Import tool modules to register them
from ..tools import discover_tools
from ..tools.camera import *
from ..tools.ptz import *
from ..tools.media import *
from ..tools.system import *
from .models import (CameraModel, StreamType, VideoQuality, PTZDirection,
                    MotionDetectionSensitivity, CameraStatus, PTZPosition,
                    MotionEvent, CameraInfo)

# Configure logging
logger = logging.getLogger(__name__)

class TapoCameraConfig(BaseModel):
    """Camera configuration model."""
    host: str = Field(..., description="Camera IP address or hostname")
    username: str = Field(..., description="Camera username")
    password: str = Field(..., description="Camera password")
    stream_quality: str = Field("hd", description="Stream quality (hd/sd)")
    verify_ssl: bool = Field(True, description="Verify SSL certificate")

class PTZPosition(BaseModel):
    """PTZ position model."""
    pan: float = Field(0.0, ge=-1.0, le=1.0, description="Pan position (-1.0 to 1.0)")
    tilt: float = Field(0.0, ge=-1.0, le=1.0, description="Tilt position (-1.0 to 1.0)")
    zoom: float = Field(0.0, ge=0.0, le=1.0, description="Zoom level (0.0 to 1.0)")

class CameraInfo(BaseModel):
    """Camera information model."""
    model: str = Field(..., description="Camera model name")
    serial_number: str = Field(..., description="Camera serial number")
    firmware: str = Field(..., description="Firmware version")
    wifi_signal: int = Field(..., description="WiFi signal strength (0-100)")
    wifi_ssid: str = Field(..., description="Connected WiFi SSID")

class CameraStatus(BaseModel):
    """Camera status model."""
    online: bool = Field(..., description="Camera online status")
    recording: bool = Field(..., description="Recording status")
    motion_detected: bool = Field(..., description="Motion detection status")
    privacy_mode: bool = Field(..., description="Privacy mode status")
    led_enabled: bool = Field(..., description="LED status")
    uptime: int = Field(..., description="Uptime in seconds")
    storage: Dict[str, int] = Field(..., description="Storage information")

class StreamInfo(BaseModel):
    """Stream information model."""
    url: HttpUrl = Field(..., description="Stream URL")
    type: str = Field(..., description="Stream type (rtsp/rtmp)")
    quality: str = Field(..., description="Stream quality (hd/sd)")

class TapoCameraServer:
    """Tapo Camera MCP server implementation using FastMCP 2.12 with modular tools."""
    
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """Get the singleton instance of the server."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the Tapo Camera MCP server.
        
        Args:
            config: Optional configuration dictionary with keys:
                - cache_size_mb: Maximum cache size in MB (default: 100)
                - temp_dir: Directory for temporary files (default: system temp dir)
                - request_timeout: HTTP request timeout in seconds (default: 30)
                - web: Web server configuration (see WebUISettings)
        """
        # Store configuration
        self.config = config or {}
        
        # Initialize FastMCP
        self.mcp = FastMCP(
            name="Tapo-Camera-MCP",
            version="0.4.0"  # Bumped version for refactored architecture
        )
        
        # Camera management
        self.cameras = {}
        self._active_camera = None
        self.camera_groups = {}
        
        # Web server
        self.web_server = None
        self._web_thread = None
        
        # Register all tools
        self._register_tools()
    
    def _register_tools(self):
        """Register all tools with the MCP server."""
        # Discover and register all tools from the tools package
        tools = discover_tools()
        
        for tool_cls in tools:
            # Create an instance of the tool
            tool_instance = tool_cls()
            
            # Register the tool with MCP
            self.mcp.register_tool(
                tool_instance,
                name=tool_cls.name,
                description=tool_cls.description,
                parameters=tool_cls.parameters if hasattr(tool_cls, 'parameters') else []
            )
    
    async def initialize(self):
        """Initialize the camera manager and any required resources."""
        logger.info("Initializing Tapo Camera MCP server")
        
        # Create temp directory if it doesn't exist
        temp_dir = Path(self.config.get('temp_dir', '/tmp/tapo-mcp'))
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Tapo Camera MCP server initialized with temp directory: {temp_dir}")
    
    async def _start_web_server(self):
        """Start the web server in a separate thread."""
        try:
            self.web_server = WebServer()
            web_config = self.config.get('web', {})
            host = web_config.get('host', '0.0.0.0')
            port = web_config.get('port', 7777)
            
            # Start the web server in a separate thread
            def run_web_server():
                self.web_server.run(host=host, port=port)
            
            self._web_thread = threading.Thread(target=run_web_server, daemon=True)
            self._web_thread.start()
            logger.info(f"Web server started on http://{host}:{port}")
            
        except Exception as e:
            logger.error(f"Failed to start web server: {e}", exc_info=True)
    
    def run(self, host: str = "0.0.0.0", port: int = 8000, stdio: bool = True, direct: bool = False):
        """Run the MCP server with both HTTP and stdio transports.
        
        Args:
            host: Host to bind the MCP HTTP server to
            port: Port to bind the MCP HTTP server to
            stdio: Enable stdio transport
            direct: If True, runs in direct mode (no event loop management, for Claude Desktop)
        """
        # Initialize resources
        asyncio.run(self.initialize())
        
        # Start the web server if enabled
        web_enabled = self.config.get('web', {}).get('enabled', True)
        if web_enabled:
            asyncio.run(self._start_web_server())
        
        # Start the MCP server
        if direct:
            # Direct mode for Claude Desktop
            self.mcp.run_http(host=host, port=port)
            if stdio:
                self.mcp.run_stdio()
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
                loop.run_until_complete(asyncio.gather(*tasks))
            except KeyboardInterrupt:
                logger.info("Shutting down...")
                for task in asyncio.all_tasks(loop):
                    task.cancel()
                loop.run_until_complete(loop.shutdown_asyncgens())
                loop.close()         # Keep the server running
            async def run_server():
                try:
                    while True:
                        await asyncio.sleep(3600)  # Sleep for an hour
                except asyncio.CancelledError:
                    logger.info("Shutting down MCP server")
            
            # Run the async function
            loop.run_until_complete(run_server())
    

# Backward compatibility
def get_server() -> TapoCameraServer:
    """Get the singleton instance of the TapoCameraServer."""
    return TapoCameraServer.get_instance()

def main():
    """Main entry point for the Tapo Camera MCP server."""
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Tapo Camera MCP Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind the server to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind the server to")
    parser.add_argument("--no-stdio", action="store_false", dest="stdio", 
                       help="Disable stdio transport")
    parser.add_argument("--direct", action="store_true", 
                       help="Run in direct mode (for Claude Desktop integration)")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()
    
    # Configure logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Create and run the server
    server = TapoCameraServer.get_instance()
    
    try:
        asyncio.run(server.run(
            host=args.host,
            port=args.port,
            stdio=args.stdio,
            direct=args.direct
        ))
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.exception("Server error:")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
