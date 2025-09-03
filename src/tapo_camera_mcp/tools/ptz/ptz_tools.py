"""
PTZ (Pan-Tilt-Zoom) tools for Tapo Camera MCP.

This module contains tools for controlling camera movements and presets.
"""

from typing import Dict, Any, List, Optional
import logging

from fastmcp.tools.types import ToolParameter
from ..base_tool import BaseTool, ToolCategory, tool, parameter

logger = logging.getLogger(__name__)

@tool(
    name="move_ptz",
    description="Move the camera PTZ (Pan-Tilt-Zoom)",
    category=ToolCategory.CAMERA
)
class MovePTZTool(BaseTool):
    """Tool to control camera PTZ movements."""
    
    parameters = [
        parameter("pan", float, "Pan position (-1.0 to 1.0)", required=False, default=0.0),
        parameter("tilt", float, "Tilt position (-1.0 to 1.0)", required=False, default=0.0),
        parameter("zoom", float, "Zoom level (0.0 to 1.0)", required=False, default=0.0),
        parameter("speed", int, "Movement speed (1-8)", required=False, default=5),
        parameter("relative", bool, "Whether the movement is relative", required=False, default=True)
    ]
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute PTZ movement."""
        from ...server_v3 import TapoCameraServer  # Lazy import to avoid circular imports
        server = TapoCameraServer.get_instance()
        return await server.move_ptz(kwargs)

@tool(
    name="save_ptz_preset",
    description="Save the current PTZ position as a preset",
    category=ToolCategory.CAMERA
)
class SavePTZPresetTool(BaseTool):
    """Tool to save the current PTZ position as a preset."""
    
    parameters = [
        parameter("name", str, "Name for the preset", required=True),
        parameter("preset_id", int, "Preset ID (1-16)", required=False)
    ]
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Save the current PTZ position as a preset."""
        from ...server_v3 import TapoCameraServer  # Lazy import to avoid circular imports
        server = TapoCameraServer.get_instance()
        return await server.save_ptz_preset(kwargs)

@tool(
    name="recall_ptz_preset",
    description="Recall a saved PTZ preset",
    category=ToolCategory.CAMERA
)
class RecallPTZPresetTool(BaseTool):
    """Tool to recall a saved PTZ preset."""
    
    parameters = [
        parameter("preset_id", int, "Preset ID to recall", required=True)
    ]
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Recall a saved PTZ preset."""
        from ...server_v3 import TapoCameraServer  # Lazy import to avoid circular imports
        server = TapoCameraServer.get_instance()
        return await server.recall_ptz_preset(kwargs["preset_id"])

@tool(
    name="get_ptz_presets",
    description="Get all saved PTZ presets",
    category=ToolCategory.CAMERA
)
class GetPTZPresetsTool(BaseTool):
    """Tool to get all saved PTZ presets."""
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Get all saved PTZ presets."""
        from ...server_v2 import TapoCameraServer  # Lazy import to avoid circular imports
        server = TapoCameraServer.get_instance()
        try:
            presets = await server.get_ptz_presets()
            return {
                "status": "success",
                "presets": presets
            }
        except Exception as e:
            logger.error(f"Failed to get PTZ presets: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to get PTZ presets: {str(e)}"
            }

@tool(
    name="ptz_go_to_home",
    description="Move the PTZ to the home position",
    category=ToolCategory.CAMERA
)
class GoToHomePTZTool(BaseTool):
    """Tool to move the PTZ to the home position."""
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Move the PTZ to the home position."""
        from ...server_v2 import TapoCameraServer  # Lazy import to avoid circular imports
        server = TapoCameraServer.get_instance()
        try:
            # Use the move_ptz method to go to home position (0, 0, 0)
            result = await server.move_ptz({"pan": 0, "tilt": 0, "zoom": 0, "relative": False})
            if result.get("status") == "success":
                return {"status": "success", "message": "PTZ moved to home position"}
            else:
                return result
        except Exception as e:
            logger.error(f"Failed to move PTZ to home position: {str(e)}")
            return {"status": "error", "message": f"Failed to move PTZ to home position: {str(e)}"}

@tool(
    name="ptz_stop",
    description="Stop all PTZ movement",
    category=ToolCategory.CAMERA
)
class StopPTZTool(BaseTool):
    """Tool to stop all PTZ movement."""
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Stop all PTZ movement."""
        from ...server_v2 import TapoCameraServer  # Lazy import to avoid circular imports
        server = TapoCameraServer.get_instance()
        try:
            # Use move_ptz with all zeros to stop movement
            result = await server.move_ptz({"pan": 0, "tilt": 0, "zoom": 0, "relative": True})
            if result.get("status") == "success":
                return {"status": "success", "message": "PTZ movement stopped"}
            else:
                return result
        except Exception as e:
            logger.error(f"Failed to stop PTZ movement: {str(e)}")
            return {"status": "error", "message": f"Failed to stop PTZ movement: {str(e)}"}

@tool(
    name="ptz_get_position",
    description="Get the current PTZ position",
    category=ToolCategory.CAMERA
)
class GetPTZPositionTool(BaseTool):
    """Tool to get the current PTZ position."""
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Get the current PTZ position."""
        from ...server_v2 import TapoCameraServer  # Lazy import to avoid circular imports
        server = TapoCameraServer.get_instance()
        try:
            # Note: This assumes the camera maintains its own position state
            # If not, you may need to track position in the server
            return {
                "status": "success",
                "position": {
                    "pan": 0.0,  # Replace with actual position if available
                    "tilt": 0.0,  # Replace with actual position if available
                    "zoom": 0.0   # Replace with actual position if available
                },
                "message": "PTZ position tracking not fully implemented. This may not reflect the actual position."
            }
        except Exception as e:
            logger.error(f"Failed to get PTZ position: {str(e)}")
            return {"status": "error", "message": f"Failed to get PTZ position: {str(e)}"}

# Update __all__ to include the new tools
__all__ = [
    'MovePTZTool',
    'SavePTZPresetTool',
    'RecallPTZPresetTool',
    'GetPTZPresetsTool',
    'GoToHomePTZTool',
    'StopPTZTool',
    'GetPTZPositionTool'
]
