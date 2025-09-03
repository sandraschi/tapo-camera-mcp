"""
System tools for Tapo Camera MCP.

This module contains tools for system-level operations and configuration.
"""

from typing import Dict, Any, Optional
import logging

from fastmcp import ToolParameter, Field
from ..base_tool import BaseTool, ToolCategory, tool, parameter

logger = logging.getLogger(__name__)

__all__ = [
    'GetSystemInfoTool',
    'RebootCameraTool',
    'GetLogsTool',
    'GetHelpTool',
    'SetMotionDetectionTool',
    'SetLEDEnabledTool',
    'SetPrivacyModeTool',
    'HelpTool'
]

@tool(
    name="get_system_info",
    description="Get system information and status",
    category=ToolCategory.SYSTEM
)
class GetSystemInfoTool(BaseTool):
    """Tool to get system information and status."""
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Get system information and status."""
        from ...server_v3 import TapoCameraServer  # Lazy import to avoid circular imports
        server = TapoCameraServer.get_instance()
        return await server.get_system_info()

@tool(
    name="reboot_camera",
    description="Reboot the camera",
    category=ToolCategory.SYSTEM
)
class RebootCameraTool(BaseTool):
    """Tool to reboot the camera."""
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Reboot the camera."""
        from ...server_v3 import TapoCameraServer  # Lazy import to avoid circular imports
        server = TapoCameraServer.get_instance()
        return await server.reboot_camera()

@tool(
    name="get_logs",
    description="Get system logs",
    category=ToolCategory.SYSTEM
)
class GetLogsTool(BaseTool):
    """Tool to get system logs."""
    
    parameters = [
        parameter("level", str, "Log level (debug, info, warning, error, critical)", 
                 required=False, default="info"),
        parameter("limit", int, "Maximum number of log entries to return", 
                 required=False, default=100)
    ]
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Get system logs."""
        from ...server_v3 import TapoCameraServer  # Lazy import to avoid circular imports
        server = TapoCameraServer.get_instance()
        return await server.get_logs(
            level=kwargs.get("level", "info"),
            limit=kwargs.get("limit", 100)
        )

@tool(
    name="get_help",
    description="Get help about available tools and their usage",
    category=ToolCategory.UTILITY
)
class GetHelpTool(BaseTool):
    """Tool to get help about available tools and their usage."""
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Get help about available tools and their usage."""
        from ...server_v3 import TapoCameraServer  # Lazy import to avoid circular imports
        server = TapoCameraServer.get_instance()
        return await server.help()

@tool(
    name="set_motion_detection",
    description="Enable or disable motion detection",
    category=ToolCategory.SYSTEM
)
class SetMotionDetectionTool(BaseTool):
    """Tool to control motion detection settings."""
    
    parameters = [
        parameter("enabled", bool, "Enable or disable motion detection", required=True),
        parameter("sensitivity", int, "Motion detection sensitivity (1-100)", required=False),
        parameter("zones", list, "Motion detection zones (list of coordinates)", required=False)
    ]
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Enable or disable motion detection."""
        from ...server_v2 import TapoCameraServer  # Lazy import to avoid circular imports
        server = TapoCameraServer.get_instance()
        try:
            result = await server.set_motion_detection(
                enabled=kwargs["enabled"],
                sensitivity=kwargs.get("sensitivity"),
                zones=kwargs.get("zones")
            )
            return result
        except Exception as e:
            logger.error(f"Failed to set motion detection: {str(e)}")
            return {"status": "error", "message": f"Failed to set motion detection: {str(e)}"}

@tool(
    name="set_led_enabled",
    description="Enable or disable the camera LED",
    category=ToolCategory.SYSTEM
)
class SetLEDEnabledTool(BaseTool):
    """Tool to control the camera LED."""
    
    parameters = [
        parameter("enabled", bool, "Enable or disable the LED", required=True)
    ]
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Enable or disable the camera LED."""
        from ...server_v2 import TapoCameraServer  # Lazy import to avoid circular imports
        server = TapoCameraServer.get_instance()
        try:
            result = await server.set_led_enabled(enabled=kwargs["enabled"])
            return {"status": "success", "message": f"LED {'enabled' if kwargs['enabled'] else 'disabled'}"}
        except Exception as e:
            logger.error(f"Failed to set LED state: {str(e)}")
            return {"status": "error", "message": f"Failed to set LED state: {str(e)}"}

@tool(
    name="set_privacy_mode",
    description="Enable or disable privacy mode",
    category=ToolCategory.SYSTEM
)
class SetPrivacyModeTool(BaseTool):
    """Tool to control privacy mode."""
    
    parameters = [
        parameter("enabled", bool, "Enable or disable privacy mode", required=True)
    ]
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Enable or disable privacy mode."""
        from ...server_v2 import TapoCameraServer  # Lazy import to avoid circular imports
        server = TapoCameraServer.get_instance()
        try:
            result = await server.set_privacy_mode(enabled=kwargs["enabled"])
            return {"status": "success", "message": f"Privacy mode {'enabled' if kwargs['enabled'] else 'disabled'}"}
        except Exception as e:
            logger.error(f"Failed to set privacy mode: {str(e)}")
            return {"status": "error", "message": f"Failed to set privacy mode: {str(e)}"}

@tool(
    name="help",
    description="Get comprehensive help about available tools and their usage",
    category=ToolCategory.UTILITY
)
class HelpTool(BaseTool):
    """Tool to get comprehensive help about available tools and their usage."""
    
    parameters = [
        parameter("tool_name", str, "Name of the tool to get help for", required=False),
        parameter("category", str, "Filter tools by category", required=False)
    ]
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Get comprehensive help about available tools and their usage."""
        from ...server_v2 import TapoCameraServer  # Lazy import to avoid circular imports
        server = TapoCameraServer.get_instance()
        try:
            return await server.help(params=kwargs)
        except Exception as e:
            logger.error(f"Failed to get help: {str(e)}")
            return {"status": "error", "message": f"Failed to get help: {str(e)}"}
