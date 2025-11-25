"""
PTZ Management Portmanteau Tool

Consolidates all PTZ-related operations into a single tool with action-based interface.
"""

import logging
from typing import Any, Literal

from fastmcp import FastMCP

from tapo_camera_mcp.tools.ptz.ptz_control_tool import PTZControlTool
from tapo_camera_mcp.tools.ptz.ptz_preset_tool import PTZPresetTool

logger = logging.getLogger(__name__)

PTZ_ACTIONS = {
    "move": "Move PTZ camera",
    "position": "Get PTZ position",
    "stop": "Stop PTZ movement",
    "save_preset": "Save PTZ preset",
    "recall_preset": "Recall PTZ preset",
    "list_presets": "List all PTZ presets",
    "delete_preset": "Delete PTZ preset",
    "home": "Move to home position",
}


def register_ptz_management_tool(mcp: FastMCP) -> None:
    """Register the PTZ management portmanteau tool."""

    @mcp.tool()
    async def ptz_management(
        action: Literal[
            "move", "position", "stop", "save_preset", "recall_preset", "list_presets", "delete_preset", "home"
        ],
        camera_name: str | None = None,
        pan: float | None = None,
        tilt: float | None = None,
        zoom: float | None = None,
        speed: int | None = None,
        preset_name: str | None = None,
        preset_id: int | None = None,
    ) -> dict[str, Any]:
        """
        Comprehensive PTZ (Pan-Tilt-Zoom) management portmanteau tool.

        PORTMANTEAU PATTERN RATIONALE:
        Instead of creating 8+ separate tools (one per operation), this tool consolidates related
        PTZ operations into a single interface. Prevents tool explosion (8+ tools → 1 tool) while maintaining
        full functionality and improving discoverability. Follows FastMCP 2.12+ best practices.

        Args:
            action (Literal, required): The operation to perform. Must be one of: "move", "position", "stop",
                "save_preset", "recall_preset", "list_presets", "delete_preset", "home".
                - "move": Move PTZ camera (requires: camera_name, pan/tilt/zoom, speed)
                - "position": Get current PTZ position (requires: camera_name)
                - "stop": Stop PTZ movement (requires: camera_name)
                - "save_preset": Save current position as preset (requires: camera_name, preset_name)
                - "recall_preset": Move to saved preset (requires: camera_name, preset_name or preset_id)
                - "list_presets": List all saved presets (requires: camera_name)
                - "delete_preset": Delete a preset (requires: camera_name, preset_name or preset_id)
                - "home": Move to home position (requires: camera_name)
            
            camera_name (str | None): Camera name/ID. Required for: all operations.
            
            pan (float | None): Pan value (-1.0 to 1.0, left to right). Required for: move operation. Default: 0.0
            
            tilt (float | None): Tilt value (-1.0 to 1.0, down to up). Required for: move operation. Default: 0.0
            
            zoom (float | None): Zoom value (0.0 to 1.0, wide to telephoto). Required for: move operation. Default: 0.0
            
            speed (int | None): Movement speed (1-8, slow to fast). Required for: move operation. Default: 5
            
            preset_name (str | None): Preset name. Required for: save_preset operation.
                Optional for: recall_preset, delete_preset operations.
            
            preset_id (int | None): Preset ID. Required for: recall_preset, delete_preset operations when
                preset_name not provided.

        Returns:
            dict[str, Any]: Dictionary containing:
                - success (bool): Boolean indicating if operation succeeded
                - action (str): The action that was performed
                - data (dict): Operation-specific result data
                - error (str | None): Error message if success is False

        Examples:
            # Move PTZ camera
            result = await ptz_management(action="move", camera_name="Front Door", pan=0.5, tilt=0.3, zoom=0.7, speed=5)

            # Get current position
            result = await ptz_management(action="position", camera_name="Front Door")

            # Save preset
            result = await ptz_management(action="save_preset", camera_name="Front Door", preset_name="Front View")

            # Recall preset
            result = await ptz_management(action="recall_preset", camera_name="Front Door", preset_name="Front View")
        """
        try:
            if action not in PTZ_ACTIONS:
                return {
                    "success": False,
                    "error": f"Invalid action '{action}'. Available: {list(PTZ_ACTIONS.keys())}",
                }

            logger.info(f"Executing PTZ management action: {action}")

            if action in ["move", "position", "stop"]:
                tool = PTZControlTool()
                operation_map = {"move": "move", "position": "position", "stop": "stop"}
                result = await tool.execute(
                    operation=operation_map[action],
                    camera_id=camera_name or "",
                    pan=pan or 0.0,
                    tilt=tilt or 0.0,
                    zoom=zoom or 0.0,
                    speed=speed or 5,
                )
                return {"success": True, "action": action, "data": result}

            elif action in ["save_preset", "recall_preset", "list_presets", "delete_preset", "home"]:
                tool = PTZPresetTool()
                operation_map = {
                    "save_preset": "save",
                    "recall_preset": "recall",
                    "list_presets": "list",
                    "delete_preset": "delete",
                    "home": "home",
                }
                result = await tool.execute(
                    operation=operation_map[action],
                    camera_id=camera_name or "",
                    preset_name=preset_name,
                    preset_id=preset_id,
                )
                return {"success": True, "action": action, "data": result}

            return {"success": False, "error": f"Action '{action}' not implemented"}

        except Exception as e:
            logger.error(f"Error in PTZ management action '{action}': {e}", exc_info=True)
            return {"success": False, "error": f"Failed to execute action '{action}': {str(e)}"}

