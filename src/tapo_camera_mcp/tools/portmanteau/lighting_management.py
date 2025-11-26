"""
Lighting Management Portmanteau Tool

Consolidates all lighting-related operations into a single tool with action-based interface.
"""

import logging
from typing import Any, Literal

from fastmcp import FastMCP

from tapo_camera_mcp.tools.lighting.hue_tools import hue_manager

logger = logging.getLogger(__name__)


def _model_dump(model: Any) -> dict[str, Any]:
    """Serialize Pydantic models across v1/v2."""
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()  # type: ignore[attr-defined]

LIGHTING_ACTIONS = {
    "list_lights": "List all Philips Hue lights",
    "get_light": "Get specific light status",
    "control_light": "Control a light (on/off, brightness, color)",
    "list_groups": "List all Hue groups/rooms",
    "control_group": "Control all lights in a group/room",
    "list_scenes": "List all available scenes",
    "activate_scene": "Activate a lighting scene",
    "status": "Get Hue Bridge connection status",
}


def register_lighting_management_tool(mcp: FastMCP) -> None:
    """Register the lighting management portmanteau tool."""

    @mcp.tool()
    async def lighting_management(
        action: Literal[
            "list_lights",
            "get_light",
            "control_light",
            "list_groups",
            "control_group",
            "list_scenes",
            "activate_scene",
            "status",
        ],
        light_id: str | None = None,
        group_id: str | None = None,
        scene_id: str | None = None,
        on: bool | None = None,
        brightness_percent: int | None = None,
        color_temp_kelvin: int | None = None,
    ) -> dict[str, Any]:
        """
        Comprehensive lighting management portmanteau tool.

        PORTMANTEAU PATTERN RATIONALE:
        Instead of creating 8+ separate tools (one per operation), this tool consolidates related
        lighting operations into a single interface. Prevents tool explosion (8+ tools → 1 tool) while maintaining
        full functionality and improving discoverability. Follows FastMCP 2.12+ best practices.

        Args:
            action (Literal, required): The operation to perform. Must be one of:
                - "list_lights": List all Philips Hue lights
                - "get_light": Get specific light status (requires: light_id)
                - "control_light": Control a light (requires: light_id, optional: on, brightness_percent, color_temp_kelvin)
                - "list_groups": List all Hue groups/rooms
                - "control_group": Control all lights in a group (requires: group_id, optional: on, brightness_percent)
                - "list_scenes": List all available scenes
                - "activate_scene": Activate a lighting scene (requires: scene_id, optional: group_id)
                - "status": Get Hue Bridge connection status
            
            light_id (str | None): Light ID. Required for: get_light, control_light operations.
            
            group_id (str | None): Group ID. Required for: control_group operation.
                Optional for: activate_scene operation (uses scene's default group if not provided).
            
            scene_id (str | None): Scene ID. Required for: activate_scene operation.
            
            on (bool | None): Turn light/group on (True) or off (False). Used by: control_light, control_group operations.
            
            brightness_percent (int | None): Brightness percentage (0-100). Used by: control_light, control_group operations.
            
            color_temp_kelvin (int | None): Color temperature in Kelvin. Used by: control_light operation.

        Returns:
            dict[str, Any]: Dictionary containing:
                - success (bool): Boolean indicating if operation succeeded
                - action (str): The action that was performed
                - data (dict): Operation-specific result data
                - error (str | None): Error message if success is False

        Examples:
            # List all lights
            result = await lighting_management(action="list_lights")

            # Get specific light status
            result = await lighting_management(action="get_light", light_id="1")

            # Turn on a light at 80% brightness
            result = await lighting_management(action="control_light", light_id="1", on=True, brightness_percent=80)

            # List all groups
            result = await lighting_management(action="list_groups")

            # Turn on all lights in a room
            result = await lighting_management(action="control_group", group_id="1", on=True)

            # List all scenes
            result = await lighting_management(action="list_scenes")

            # Activate a scene
            result = await lighting_management(action="activate_scene", scene_id="abc123")

            # Check bridge status
            result = await lighting_management(action="status")
        """
        try:
            if action not in LIGHTING_ACTIONS:
                return {
                    "success": False,
                    "error": f"Invalid action '{action}'. Available: {list(LIGHTING_ACTIONS.keys())}",
                }

            logger.info(f"Executing lighting management action: {action}")

            # Initialize if needed
            if not hue_manager._initialized:
                await hue_manager.initialize()

            if action == "list_lights":
                lights = await hue_manager.get_all_lights()
                return {
                    "success": True,
                    "action": action,
                    "data": {
                        "lights": [_model_dump(light) for light in lights],
                        "count": len(lights),
                    },
                }

            if action == "get_light":
                if not light_id:
                    return {"success": False, "error": "light_id is required for get_light action"}
                light = await hue_manager.get_light(light_id)
                if not light:
                    return {"success": False, "error": f"Light {light_id} not found"}
                return {
                    "success": True,
                    "action": action,
                    "data": {"light": _model_dump(light)},
                }

            if action == "control_light":
                if not light_id:
                    return {"success": False, "error": "light_id is required for control_light action"}
                success = await hue_manager.set_light_state(
                    light_id,
                    on=on,
                    brightness_percent=brightness_percent,
                    color_temp=color_temp_kelvin,
                )
                if success:
                    # Get updated light state
                    light = await hue_manager.get_light(light_id)
                    return {
                        "success": True,
                        "action": action,
                        "data": {"light": _model_dump(light) if light else None},
                    }
                return {"success": False, "error": "Failed to control light"}

            if action == "list_groups":
                groups = await hue_manager.get_all_groups()
                return {
                    "success": True,
                    "action": action,
                    "data": {
                        "groups": [_model_dump(group) for group in groups],
                        "count": len(groups),
                    },
                }

            if action == "control_group":
                if not group_id:
                    return {"success": False, "error": "group_id is required for control_group action"}
                brightness = int((brightness_percent / 100) * 254) if brightness_percent is not None else None
                success = await hue_manager.set_group_state(
                    group_id,
                    on=on,
                    brightness=brightness,
                )
                return {"success": success, "action": action, "data": {}}

            if action == "list_scenes":
                scenes = await hue_manager.get_all_scenes()
                # Filter to unique predefined scenes (same as web API)
                predefined_scenes = {
                    "Arctic aurora",
                    "Bright",
                    "Concentrate",
                    "Dimmed",
                    "Energize",
                    "Nightlight",
                    "Read",
                    "Relax",
                    "Savanna sunset",
                    "Spring blossom",
                    "Tropical twilight",
                }
                seen_names = set()
                filtered_scenes = []
                for scene in scenes:
                    scene_name = scene.name
                    if scene_name in predefined_scenes:
                        if scene_name not in seen_names:
                            seen_names.add(scene_name)
                            filtered_scenes.append(scene)
                    elif scene_name not in seen_names and scene_name not in predefined_scenes:
                        seen_names.add(scene_name)
                        filtered_scenes.append(scene)
                return {
                    "success": True,
                    "action": action,
                    "data": {
                        "scenes": [_model_dump(scene) for scene in filtered_scenes],
                        "count": len(filtered_scenes),
                    },
                }

            if action == "activate_scene":
                if not scene_id:
                    return {"success": False, "error": "scene_id is required for activate_scene action"}
                success = await hue_manager.activate_scene(scene_id, group_id)
                return {"success": success, "action": action, "data": {"scene_id": scene_id}}

            if action == "status":
                return {
                    "success": True,
                    "action": action,
                    "data": {
                        "connected": hue_manager._initialized,
                        "bridge_ip": hue_manager._bridge_ip,
                        "lights_count": len(hue_manager.lights),
                        "groups_count": len(hue_manager.groups),
                        "scenes_count": len(hue_manager.scenes),
                        "error": hue_manager._connection_error,
                    },
                }

            return {"success": False, "error": f"Action '{action}' not implemented"}

        except Exception as e:
            logger.error(f"Error in lighting management action '{action}': {e}", exc_info=True)
            return {"success": False, "error": f"Failed to execute action '{action}': {e!s}"}

