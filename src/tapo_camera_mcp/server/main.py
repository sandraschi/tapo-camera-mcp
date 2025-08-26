"""Main server module for Tapo Camera MCP."""
import asyncio
import logging
from typing import Dict, Any, Optional, List

from fastmcp import FastMCP
from ..camera.manager import camera_manager, CameraManager
from .config import ServerConfig
from . import api

logger = logging.getLogger(__name__)

class TapoCameraServer:
    """Main server class for Tapo Camera MCP."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the server with configuration."""
        self.config = ServerConfig.from_dict(config or {})
        self.mcp = FastMCP()
        self.camera_manager = camera_manager
        self._api_router = None
        
    async def start(self):
        """Start the server."""
        try:
            # Initialize camera manager
            await self._init_cameras()
            
            # Register API routes
            self._api_router = api.setup_api_routes(self)
            
            # Start web server if enabled
            if self.config.web_enabled:
                await self._start_web_server()
                
            logger.info(f"Server started on {self.config.host}:{self.config.port}")
            
        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            await self.stop()
            raise
    
    async def stop(self):
        """Stop the server and clean up resources."""
        try:
            await self.camera_manager.close()
            logger.info("Server stopped")
        except Exception as e:
            logger.error(f"Error during server shutdown: {e}")
    
    async def _init_cameras(self):
        """Initialize cameras from config."""
        # Add default camera if configured
        if self.config.default_camera:
            await self.camera_manager.add_camera(self.config.default_camera)
        
        # Initialize camera groups
        for group, cameras in self.config.groups.items():
            for camera_name in cameras:
                await self.camera_manager.add_camera_to_group(camera_name, group)
    
    async def _start_web_server(self):
        """Start the web interface."""
        from ..web_server import TapoWebServer
        
        self.web_server = TapoWebServer(
            mcp_server=self,
            host=self.config.web_host,
            port=self.config.web_port
        )
        
        # Run in background
        import threading
        web_thread = threading.Thread(
            target=self.web_server.run,
            daemon=True
        )
        web_thread.start()
        logger.info(f"Web interface started at http://{self.config.web_host}:{self.config.web_port}")

    def run(self):
        """Run the server (blocking)."""
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(self.start())
            loop.run_forever()
        except KeyboardInterrupt:
            logger.info("Shutting down...")
        finally:
            loop.run_until_complete(self.stop())
            loop.close()
