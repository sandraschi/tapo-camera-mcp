"""
PTZ (Pan-Tilt-Zoom) tools for Tapo Camera MCP.

This module contains tools for controlling camera movements and presets.
"""

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*Support for class-based.*")

from typing import Dict, Any, List, Optional, Union
import logging
from pydantic import Field, BaseModel, ConfigDict

from tapo_camera_mcp.tools.base_tool import tool, ToolCategory, BaseTool, ToolResult

logger = logging.getLogger(__name__)

@tool(
    name="move_ptz",
    category=ToolCategory.PTZ
)
class MovePTZTool(BaseTool):
    '''
    Control camera PTZ (Pan-Tilt-Zoom) movements.
    
    Move the camera to a new position with adjustable pan, tilt, zoom,
    and speed. Supports both absolute and relative positioning.
    
    Parameters:
        pan (float): Pan position, range -1.0 to 1.0 (left to right)
        tilt (float): Tilt position, range -1.0 to 1.0 (down to up)
        zoom (float): Zoom level, range 0.0 to 1.0 (wide to telephoto)
        speed (int): Movement speed, range 1-8 (slow to fast)
        relative (bool): True for relative movement, False for absolute
    
    Returns:
        Dict with movement status and final position
    
    Example:
        # Pan right slowly
        result = await move_ptz_tool.execute(pan=0.5, speed=3)
        
        # Tilt up and zoom in
        result = await move_ptz_tool.execute(tilt=0.3, zoom=0.7, speed=5)
    '''
    
    model_config = ConfigDict(
        json_schema_extra={
            "category": ToolCategory.PTZ,
            "description": "Control camera PTZ movements"
        }
    )
    
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
        server = await TapoCameraServer.get_instance()
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
    '''
    Save the current PTZ position as a preset.
    
    Stores the camera's current pan, tilt, and zoom position
    with a custom name for quick recall later.
    
    Parameters:
        preset_name (str): Name for the preset (e.g., 'front_door', 'driveway')
    
    Returns:
        Dict with save status and preset details
    
    Example:
        # Save current position
        result = await save_ptz_preset_tool.execute(preset_name='front_door')
        print(f"Saved preset: {result['preset_name']}")
    '''
    
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
        server = await TapoCameraServer.get_instance()
        return await server.save_ptz_preset({
            'name': self.name,
            'preset_id': self.preset_id
        })

@tool(
    name="recall_ptz_preset",
    category=ToolCategory.PTZ
)
class RecallPTZPresetTool(BaseTool):
    '''
    Recall a saved PTZ preset position.
    
    Moves the camera to a previously saved preset position
    by ID, restoring the pan, tilt, and zoom settings.
    
    Parameters:
        preset_id (int): ID of the preset to recall
    
    Returns:
        Dict with recall status and new position
    
    Example:
        # Move to saved position
        result = await recall_ptz_preset_tool.execute(preset_id=1)
        if result['success']:
            print(f"Camera moved to preset {result['preset_id']}")
    '''
    
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
        server = await TapoCameraServer.get_instance()
        return await server.recall_ptz_preset(self.preset_id)

@tool(
    name="get_ptz_presets",
    category=ToolCategory.PTZ
)
class GetPTZPresetsTool(BaseTool):
    '''
    Get all saved PTZ presets.
    
    Returns a list of all saved preset positions with their
    IDs, names, and position details.
    
    Parameters:
        None
    
    Returns:
        Dict with list of presets:
        - presets (List[Dict]): List of preset dictionaries
        - total (int): Total number of presets
    
    Example:
        result = await get_ptz_presets_tool.execute()
        for preset in result['presets']:
            print(f"{preset['id']}: {preset['name']}")
    '''
    
    class Config:
        schema_extra = {
            "category": ToolCategory.PTZ,
            "description": "Get all saved PTZ presets"
        }
    
    async def execute(self) -> Dict[str, Any]:
        """Get all saved PTZ presets."""
        from ...core.server import TapoCameraServer
        server = await TapoCameraServer.get_instance()
        return await server.get_ptz_presets()

@tool(
    name="go_to_home_ptz",
    category=ToolCategory.PTZ
)
class GoToHomePTZTool(BaseTool):
    '''
    Move the camera to its home position.
    
    Returns the camera to its default/home position, typically
    pointing straight ahead at zero pan and tilt.
    
    Parameters:
        None
    
    Returns:
        Dict with movement status
    
    Example:
        result = await go_to_home_ptz_tool.execute()
        print("Camera returned to home position")
    '''
    
    class Config:
        schema_extra = {
            "category": ToolCategory.PTZ,
            "description": "Move the PTZ to the home position"
        }
    
    async def execute(self) -> Dict[str, Any]:
        """Move the PTZ to the home position."""
        from ...core.server import TapoCameraServer
        server = await TapoCameraServer.get_instance()
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
    '''
    Stop PTZ movement immediately.
    
    Halts any ongoing pan, tilt, or zoom movement and holds
    the camera at its current position.
    
    Parameters:
        None
    
    Returns:
        Dict with stop status
    
    Example:
        result = await stop_ptz_tool.execute()
        print("Camera movement stopped")
    '''
    
    class Config:
        schema_extra = {
            "category": ToolCategory.PTZ,
            "description": "Stop all PTZ movement"
        }
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Stop all PTZ movement."""
        from tapo_camera_mcp.core.server import TapoCameraServer  # Lazy import to avoid circular imports
        server = await TapoCameraServer.get_instance()
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
    '''
    Get the current PTZ position and capabilities.
    
    Returns the camera's current pan, tilt, and zoom values along
    with movement capabilities and ranges.
    
    Parameters:
        None
    
    Returns:
        Dict with position information:
        - pan (float): Current pan position
        - tilt (float): Current tilt position
        - zoom (float): Current zoom level
        - capabilities (Dict): Movement ranges and limits
    
    Example:
        result = await get_ptz_position_tool.execute()
        print(f"Pan: {result['position']['pan']}")
        print(f"Tilt: {result['position']['tilt']}")
        print(f"Zoom: {result['position']['zoom']}")
    '''
    
    class Config:
        schema_extra = {
            "category": ToolCategory.PTZ,
            "description": "Get the current PTZ position"
        }
    
    async def execute(self, **kwargs) -> ToolResult:
        """Get the current PTZ position."""
        from tapo_camera_mcp.core.server import TapoCameraServer  # Lazy import to avoid circular imports
        server = await TapoCameraServer.get_instance()
        try:
            if not server.camera or not server._connected:
                return {
                    "status": "error", 
                    "message": "No camera connected. Please connect to a camera first."
                }
            
            # Get real PTZ position from camera
            if hasattr(server.camera, '_camera') and server.camera._camera:
                # Use pytapo to get actual PTZ position
                position_data = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: server.camera._camera.getMotorCapability()
                )
                
                # Extract position from camera response
                pan = position_data.get('pan', {}).get('current_position', 0.0)
                tilt = position_data.get('tilt', {}).get('current_position', 0.0)
                zoom = position_data.get('zoom', {}).get('current_position', 0.0)
                
                return {
                    "status": "success",
                    "position": {
                        "pan": float(pan),
                        "tilt": float(tilt),
                        "zoom": float(zoom)
                    },
                    "message": "Current PTZ position retrieved successfully"
                }
            else:
                return {
                    "status": "error",
                    "message": "Camera not properly initialized for PTZ operations"
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
