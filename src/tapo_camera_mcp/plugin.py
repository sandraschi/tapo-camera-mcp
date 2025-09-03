"""
Plugin module for Tapo Camera MCP.

This module provides the necessary hooks for FastMCP to discover and load the Tapo Camera MCP plugin.
"""
from typing import Dict, Any, Optional, Type

from fastmcp import FastMCP, McpMessage
from pydantic import BaseModel

from .server_v3 import TapoCameraServer as TapoCameraMCP
from .models import CameraConfig

class TapoCameraPluginConfig(BaseModel):
    """Configuration model for the Tapo Camera MCP plugin."""
    enabled: bool = True
    config: Optional[Dict[str, Any]] = None

class TapoCameraPlugin:
    """Tapo Camera MCP plugin for FastMCP."""
    
    def __init__(self, mcp: FastMCP, config: Optional[Dict[str, Any]] = None):
        """Initialize the plugin.
        
        Args:
            mcp: The FastMCP instance.
            config: Plugin configuration.
        """
        self.mcp = mcp
        self.config = TapoCameraPluginConfig(**(config or {}))
        self.tapo_camera: Optional[TapoCameraMCP] = None
    
    async def on_startup(self):
        """Called when the FastMCP server starts up."""
        if not self.config.enabled:
            self.mcp.logger.info("Tapo Camera MCP plugin is disabled")
            return
        
        self.mcp.logger.info("Starting Tapo Camera MCP plugin")
        
        # Initialize the Tapo Camera MCP
        self.tapo_camera = TapoCameraMCP(
            config=self.config.config or {},
            logger=self.mcp.logger.getChild("tapo_camera")
        )
        
        # Register message handlers
        await self._register_handlers()
        
        # Connect to the camera
        try:
            await self.tapo_camera.connect()
            self.mcp.logger.info("Connected to Tapo camera")
        except Exception as e:
            self.mcp.logger.error(f"Failed to connect to Tapo camera: {str(e)}")
    
    async def on_shutdown(self):
        """Called when the FastMCP server shuts down."""
        if not self.config.enabled or not self.tapo_camera:
            return
        
        self.mcp.logger.info("Shutting down Tapo Camera MCP plugin")
        await self.tapo_camera.disconnect()
    
    async def _register_handlers(self):
        """Register message handlers with the FastMCP instance."""
        if not self.tapo_camera:
            return
        
        # Register all message handlers from the TapoCameraMCP class
        for msg_type, handler in self.tapo_camera.message_handlers.items():
            self.mcp.register_message_handler(msg_type, handler)
            
        # Add a custom handler for plugin-specific messages
        self.mcp.register_message_handler("tapo_camera_plugin_status", self._handle_plugin_status)
    
    async def _handle_plugin_status(self, message: McpMessage) -> Dict[str, Any]:
        """Handle plugin status requests."""
        return {
            "status": "enabled" if self.config.enabled else "disabled",
            "connected": self.tapo_camera.is_connected if self.tapo_camera else False,
            "version": "0.1.0"
        }

def register_plugin(mcp: FastMCP, config: Optional[Dict[str, Any]] = None) -> TapoCameraPlugin:
    """Register the Tapo Camera MCP plugin with FastMCP.
    
    This is the entry point that FastMCP uses to load the plugin.
    
    Args:
        mcp: The FastMCP instance.
        config: Plugin configuration.
        
    Returns:
        An instance of the TapoCameraPlugin.
    """
    return TapoCameraPlugin(mcp, config)

# For backward compatibility
TapoCameraMCPPlugin = TapoCameraPlugin
