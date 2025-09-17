"""
PTZ (Pan-Tilt-Zoom) tools for Tapo Camera MCP.

This module contains tools for controlling camera movements and presets.
"""

from typing import Dict, Any, List, Optional, Union
import logging
from pydantic import Field, BaseModel

from tapo_camera_mcp.tools.base_tool import tool, ToolCategory, BaseTool, ToolResult

logger = logging.getLogger(__name__)

@tool(
    name="move_ptz",
    category=ToolCategory.PTZ
)
class MovePTZTool(BaseTool):
    """Tool to control camera PTZ movements."""
    
    class Config:
        schema_extra = {
            "category": ToolCategory.PTZ,
            "description": "Control camera PTZ movements"
        }
    
    pan: float = Field(
        default=0.0,
        ge=-1.0,
        le=1.0,
        description="Pan position (-1.0 to 1.0)"
    )
    
    tilt: float = Field(
        default=0.0,
        ge=-1.0,
        le=1.0,
        description="Tilt position (-1.0 to 1.0)"
    )
    
    zoom: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Zoom level (0.0 to 1.0)"
    )
    
    speed: int = Field(
        default=5,
        ge=1,
        le=8,
        description="Movement speed (1-8)"
    )
    
    relative: bool = Field(
        default=True,
        description="Whether the movement is relative"
    )
    
    async def execute(self) -> Dict[str, Any]:
        """Execute PTZ movement."""
        from tapo_camera_mcp.core.server import TapoCameraServer  # Lazy import to avoid circular imports
        server = TapoCameraServer.get_instance()
        return await server.move_ptz({
            'pan': self.pan,
            'tilt': self.tilt,
            'zoom': self.zoom,
            'speed': self.speed,
            'relative': self.relative
        })

@tool(
    name="save_ptz_preset",
    category=ToolCategory.PTZ
)
class SavePTZPresetTool(BaseTool):
    """Tool to save the current PTZ position as a preset."""
    
    class Config:
        schema_extra = {
            "category": ToolCategory.PTZ,
            "description": "Save the current PTZ position as a preset"
        }
    
    preset_id: int = Field(
        ...,
        ge=1,
        le=16
    )
    
    name: Optional[str] = Field(
        None
    )
    
    async def execute(self) -> Dict[str, Any]:
        """Save the current PTZ position as a preset."""
        from ...core.server import TapoCameraServer
        server = TapoCameraServer.get_instance()
        return await server.save_ptz_preset({
            'name': self.name,
            'preset_id': self.preset_id
        })

@tool(
    name="recall_ptz_preset",
    category=ToolCategory.PTZ
)
class RecallPTZPresetTool(BaseTool):
    """Tool to recall a saved PTZ preset."""
    
    class Config:
        schema_extra = {
            "category": ToolCategory.PTZ,
            "description": "Recall a saved PTZ preset"
        }
    
    preset_id: int = Field(
        ...,
        ge=1,
        le=16
    )
    
    async def execute(self) -> Dict[str, Any]:
        """Recall a saved PTZ preset."""
        from ...core.server import TapoCameraServer
        server = TapoCameraServer.get_instance()
        return await server.recall_ptz_preset(self.preset_id)

@tool(
    name="get_ptz_presets",
    category=ToolCategory.PTZ
)
class GetPTZPresetsTool(BaseTool):
    """Tool to get all saved PTZ presets."""
    
    class Config:
        schema_extra = {
            "category": ToolCategory.PTZ,
            "description": "Get all saved PTZ presets"
        }
    
    async def execute(self) -> Dict[str, Any]:
        """Get all saved PTZ presets."""
        from ...core.server import TapoCameraServer
        server = TapoCameraServer.get_instance()
        return await server.get_ptz_presets()

@tool(
    name="go_to_home_ptz",
    category=ToolCategory.PTZ
)
class GoToHomePTZTool(BaseTool):
    """Tool to move the PTZ to the home position."""
    
    class Config:
        schema_extra = {
            "category": ToolCategory.PTZ,
            "description": "Move the PTZ to the home position"
        }
    
    async def execute(self) -> Dict[str, Any]:
        """Move the PTZ to the home position."""
        from ...core.server import TapoCameraServer
        server = TapoCameraServer.get_instance()
        try:
            return await server.go_to_home_ptz()
        except Exception as e:
            logger.error(f"Failed to move PTZ to home position: {str(e)}")
            return {"status": "error", "message": f"Failed to move PTZ to home position: {str(e)}"}

@tool(
    name="stop_ptz",
    category=ToolCategory.PTZ
)
class StopPTZTool(BaseTool):
    """Tool to stop all PTZ movement."""
    
    class Config:
        schema_extra = {
            "category": ToolCategory.PTZ,
            "description": "Stop all PTZ movement"
        }
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Stop all PTZ movement."""
        from tapo_camera_mcp.core.server import TapoCameraServer  # Lazy import to avoid circular imports
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
    name="get_ptz_position",
    category=ToolCategory.PTZ
)
class GetPTZPositionTool(BaseTool):
    """Tool to get the current PTZ position."""
    
    class Config:
        schema_extra = {
            "category": ToolCategory.PTZ,
            "description": "Get the current PTZ position"
        }
    
    async def execute(self, **kwargs) -> ToolResult:
        """Get the current PTZ position."""
        from tapo_camera_mcp.core.server import TapoCameraServer  # Lazy import to avoid circular imports
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
