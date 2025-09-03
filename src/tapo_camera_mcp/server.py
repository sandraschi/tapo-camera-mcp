"""
Tapo Camera MCP Server

A FastMCP 2.12+ server for managing TP-Link Tapo cameras with a modular architecture.
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List

from fastmcp import FastMCP
from pydantic import BaseModel, Field

# Import tool modules
from .tools.camera import (
    ListCamerasTool, AddCameraTool, RemoveCameraTool,
    SetActiveCameraTool, ConnectCameraTool, DisconnectCameraTool,
    GetCameraInfoTool, ManageCameraGroupsTool
)

from .tools.ptz import (
    MovePTZTool, SavePTZPresetTool, RecallPTZPresetTool,
    GetPTZPresetsTool, GoToHomePTZTool, StopPTZTool, GetPTZPositionTool
)

from .tools.media import (
    CaptureImageTool, FindSimilarImagesTool, GetStreamURLTool,
    StartRecordingTool, StopRecordingTool, AnalyzeImageTool,
    SecurityScanTool, CaptureStillTool
)

from .tools.system import (
    GetSystemInfoTool, RebootCameraTool, GetLogsTool, GetHelpTool,
    SetMotionDetectionTool, SetLEDEnabledTool, SetPrivacyModeTool, HelpTool
)

from .metrics_service import MetricsCollector, MetricsServer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TapoCameraConfig(BaseModel):
    """Configuration model for the Tapo Camera MCP server."""
    host: Optional[str] = Field(None, description="Camera IP address or hostname")
    username: Optional[str] = Field(None, description="Camera username")
    password: Optional[str] = Field(None, description="Camera password")
    
    # Metrics service configuration
    enable_metrics: bool = Field(True, description="Enable metrics collection service")
    metrics_host: str = Field("0.0.0.0", description="Host to bind metrics server to")
    metrics_port: int = Field(8080, description="Port to bind metrics server to")
    stream_quality: str = Field("hd", description="Stream quality (hd/sd)")
    verify_ssl: bool = Field(True, description="Verify SSL certificate")
    web_enabled: bool = Field(True, description="Enable web interface")
    web_host: str = Field("0.0.0.0", description="Web interface host")
    web_port: int = Field(7777, description="Web interface port")
    cache_size_mb: int = Field(100, description="Image cache size in MB")
    max_cache_items: int = Field(100, description="Maximum number of cached items")
    temp_dir: str = Field("C:/temp", description="Directory for temporary files")
    request_timeout: int = Field(30, description="HTTP request timeout in seconds")
    max_retries: int = Field(3, description="Maximum retry attempts for operations")

class TapoCameraServer:
    """Main Tapo Camera MCP server class."""
    
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """Get the singleton instance of the server."""
        if cls._instance is None:
            raise RuntimeError("Server not initialized. Call create() first.")
        return cls._instance
    
    @classmethod
    async def create(cls, config: Optional[Dict[str, Any]] = None):
        """Create a new instance of the server.
        
        Args:
            config: Optional configuration dictionary
            
        Returns:
            TapoCameraServer: The server instance
        """
        if cls._instance is not None:
            return cls._instance
            
        cls._instance = cls(config)
        await cls._instance.initialize()
        return cls._instance
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the server with the given configuration."""
        if self._instance is not None:
            raise RuntimeError("Use create() method to create a server instance")
            
        # Load configuration
        self.config = TapoCameraConfig(**(config or {})).dict()
        
        # Initialize FastMCP
        self.mcp = FastMCP(
            name="Tapo-Camera-MCP",
            version="0.4.0",
            description="MCP server for TP-Link Tapo cameras"
        )
        
        # Initialize components
        self.camera = None
        self.web_server = None
        self.metrics_collector = None
        self.metrics_server = None
        
    async def initialize(self):
        """Initialize server components."""
        # Create necessary directories
        temp_dir = Path(self.config["temp_dir"])
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Register tools
        self._register_tools()
        
        # Initialize metrics service if enabled
        if self.config["enable_metrics"]:
            try:
                self.metrics_collector = MetricsCollector(tapo_client=None)  # Pass actual client when available
                await self.metrics_collector.start()
                
                self.metrics_server = MetricsServer(
                    self.metrics_collector,
                    host=self.config["metrics_host"],
                    port=self.config["metrics_port"]
                )
                # Start metrics server in the background
                asyncio.create_task(self.metrics_server.start())
                logger.info(f"Metrics service started on {self.config['metrics_host']}:{self.config['metrics_port']}")
            except Exception as e:
                logger.error(f"Failed to start metrics service: {e}")
        
        # Start web server if enabled
        if self.config["web_enabled"]:
            await self._start_web_server()
    
    def _register_tools(self):
        """Register all available tools with the MCP server."""
        # Camera management tools
        self.mcp.register_tool(ListCamerasTool())
        self.mcp.register_tool(AddCameraTool())
        self.mcp.register_tool(RemoveCameraTool())
        self.mcp.register_tool(SetActiveCameraTool())
        self.mcp.register_tool(ConnectCameraTool())
        self.mcp.register_tool(DisconnectCameraTool())
        self.mcp.register_tool(GetCameraInfoTool())
        self.mcp.register_tool(ManageCameraGroupsTool())
        
        # PTZ control tools
        self.mcp.register_tool(MovePTZTool())
        self.mcp.register_tool(SavePTZPresetTool())
        self.mcp.register_tool(RecallPTZPresetTool())
        self.mcp.register_tool(GetPTZPresetsTool())
        self.mcp.register_tool(GoToHomePTZTool())
        self.mcp.register_tool(StopPTZTool())
        self.mcp.register_tool(GetPTZPositionTool())
        
        # Media tools
        self.mcp.register_tool(CaptureImageTool())
        self.mcp.register_tool(FindSimilarImagesTool())
        self.mcp.register_tool(GetStreamURLTool())
        self.mcp.register_tool(StartRecordingTool())
        self.mcp.register_tool(StopRecordingTool())
        self.mcp.register_tool(AnalyzeImageTool())
        self.mcp.register_tool(SecurityScanTool())
        self.mcp.register_tool(CaptureStillTool())
        
        # System tools
        self.mcp.register_tool(GetSystemInfoTool())
        self.mcp.register_tool(RebootCameraTool())
        self.mcp.register_tool(GetLogsTool())
        self.mcp.register_tool(GetHelpTool())
        self.mcp.register_tool(SetMotionDetectionTool())
        self.mcp.register_tool(SetLEDEnabledTool())
        self.mcp.register_tool(SetPrivacyModeTool())
        self.mcp.register_tool(HelpTool())
    
    async def _start_web_server(self):
        """Start the web interface server."""
        from .web_server import TapoWebServer
        
        try:
            self.web_server = TapoWebServer(
                host=self.config["web_host"],
                port=self.config["web_port"],
                mcp=self.mcp
            )
            await self.web_server.start()
            logger.info(f"Web server started on http://{self.config['web_host']}:{self.config['web_port']}")
        except Exception as e:
            logger.error(f"Failed to start web server: {e}")
    
    async def run(self, host: str = "0.0.0.0", port: int = 8000, stdio: bool = True):
        """Run the MCP server.
        
        Args:
            host: Host to bind the HTTP server to
            port: Port to bind the HTTP server to
            stdio: Enable stdio transport
        """
        try:
            # Start the MCP server
            await self.mcp.start(host=host, port=port, stdio=stdio)
            logger.info(f"MCP server started on http://{host}:{port}")
            
            # Keep the server running
            while True:
                await asyncio.sleep(3600)  # Sleep for 1 hour
                
        except asyncio.CancelledError:
            logger.info("Shutting down server...")
        except Exception as e:
            logger.error(f"Server error: {e}", exc_info=True)
        finally:
            await self.shutdown()
    
    async def shutdown(self):
        """Shut down the server and clean up resources."""
        # Shutdown web server if running
        if self.web_server:
            await self.web_server.stop()
        
        # Shutdown metrics service if running
        if self.metrics_collector:
            await self.metrics_collector.stop()
        
        if self.metrics_server:
            await self.metrics_server.stop()
        
        logger.info("Server shutdown complete")


async def main():
    """Main entry point for the Tapo Camera MCP server."""
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Tapo Camera MCP Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind the server to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind the server to")
    parser.add_argument("--no-stdio", action="store_false", dest="stdio", 
                       help="Disable stdio transport")
    parser.add_argument("--config", help="Path to configuration file (JSON)")
    
    args = parser.parse_args()
    
    # Load configuration
    config = {}
    if args.config:
        import json
        with open(args.config) as f:
            config = json.load(f)
    
    try:
        # Create and run the server
        server = await TapoCameraServer.create(config)
        await server.run(host=args.host, port=args.port, stdio=args.stdio)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
