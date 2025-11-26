"""
Tapo Control Portmanteau Tool

Unified tool for controlling all hardware via natural commands.
When you say "tapo list lights", this tool handles it.
"""

import logging
from typing import Any

from fastmcp import FastMCP

from tapo_camera_mcp.tools.energy.tapo_plug_tools import tapo_plug_manager
from tapo_camera_mcp.tools.lighting.hue_tools import hue_manager

logger = logging.getLogger(__name__)


def _model_dump(model: Any) -> dict[str, Any]:
    """Serialize Pydantic models across v1/v2."""
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()  # type: ignore[attr-defined]


TAPO_ACTIONS = {
    # Lighting
    "list_lights": "List all Philips Hue lights",
    "list_light": "List all Philips Hue lights (alias for list_lights)",
    "turn_on_light": "Turn on a light",
    "turn_off_light": "Turn off a light",
    "set_brightness": "Set light brightness",
    "list_groups": "List all Hue groups/rooms",
    "list_scenes": "List all available scenes",
    "activate_scene": "Activate a lighting scene",
    # Energy
    "list_plugs": "List all Tapo P115 smart plugs",
    "list_plug": "List all Tapo P115 smart plugs (alias for list_plugs)",
    "turn_on_plug": "Turn on a smart plug",
    "turn_off_plug": "Turn off a smart plug",
    # Kitchen
    "list_kitchen": "List all kitchen appliances",
    "turn_on_kettle": "Turn on Zojirushi kettle",
    "turn_off_kettle": "Turn off Zojirushi kettle",
    # Status
    "status": "Get overall system status",
}


def register_tapo_control_tool(mcp: FastMCP) -> None:
    """Register the unified Tapo control tool."""

    @mcp.tool()
    async def tapo(
        action: str,
        device_id: str | None = None,
        light_id: str | None = None,
        group_id: str | None = None,
        scene_id: str | None = None,
        brightness_percent: int | None = None,
        power_state: str | None = None,
    ) -> dict[str, Any]:
        """
        Unified Tapo control tool for all hardware operations.

        This tool provides a natural interface for controlling all hardware.
        Use intuitive commands like "list lights", "turn on light", etc.

        Args:
            action (str, required): The action to perform. Examples:
                - "list lights" or "list_lights" - List all Hue lights
                - "list plugs" or "list_plugs" - List all smart plugs
                - "turn on light" or "turn_on_light" - Turn on a light (requires: light_id)
                - "turn off light" or "turn_off_light" - Turn off a light (requires: light_id)
                - "set brightness" or "set_brightness" - Set light brightness (requires: light_id, brightness_percent)
                - "list groups" or "list_groups" - List all Hue groups
                - "list scenes" or "list_scenes" - List all scenes
                - "activate scene" or "activate_scene" - Activate a scene (requires: scene_id)
                - "turn on plug" or "turn_on_plug" - Turn on a smart plug (requires: device_id)
                - "turn off plug" or "turn_off_plug" - Turn off a smart plug (requires: device_id)
                - "list kitchen" - List kitchen appliances
                - "turn on kettle" - Turn on Zojirushi kettle
                - "turn off kettle" - Turn off Zojirushi kettle
                - "status" - Get system status
            
            device_id (str | None): Device ID for plugs/appliances
            light_id (str | None): Light ID for light operations
            group_id (str | None): Group ID for group operations
            scene_id (str | None): Scene ID for scene operations
            brightness_percent (int | None): Brightness percentage (0-100)
            power_state (str | None): Power state ("on"/"off"/"toggle")

        Returns:
            dict[str, Any]: Operation result

        Examples:
            # List all lights
            tapo(action="list lights")

            # Turn on bathroom light
            tapo(action="turn on light", light_id="3")

            # Set brightness
            tapo(action="set brightness", light_id="3", brightness_percent=80)

            # List all smart plugs
            tapo(action="list plugs")

            # Turn on kettle
            tapo(action="turn on kettle")
        """
        try:
            # Normalize action (handle spaces and case)
            action_lower = action.lower().replace(" ", "_").strip()

            logger.info(f"Executing tapo action: {action} (normalized: {action_lower})")

            # Lighting actions
            if action_lower in ["list_lights", "list_light", "list lights", "list light"]:
                if not hue_manager._initialized:
                    await hue_manager.initialize()
                lights = await hue_manager.get_all_lights()
                return {
                    "success": True,
                    "action": "list_lights",
                    "data": {
                        "lights": [_model_dump(light) for light in lights],
                        "count": len(lights),
                    },
                }

            if action_lower in ["turn_on_light", "turn on light", "on light"]:
                if not light_id:
                    return {"success": False, "error": "light_id is required to turn on a light"}
                if not hue_manager._initialized:
                    await hue_manager.initialize()
                success = await hue_manager.set_light_state(light_id, on=True, brightness_percent=brightness_percent)
                if success:
                    light = await hue_manager.get_light(light_id)
                    return {
                        "success": True,
                        "action": "turn_on_light",
                        "data": {"light": _model_dump(light) if light else None},
                    }
                return {"success": False, "error": "Failed to turn on light"}

            if action_lower in ["turn_off_light", "turn off light", "off light"]:
                if not light_id:
                    return {"success": False, "error": "light_id is required to turn off a light"}
                if not hue_manager._initialized:
                    await hue_manager.initialize()
                success = await hue_manager.set_light_state(light_id, on=False)
                if success:
                    light = await hue_manager.get_light(light_id)
                    return {
                        "success": True,
                        "action": "turn_off_light",
                        "data": {"light": _model_dump(light) if light else None},
                    }
                return {"success": False, "error": "Failed to turn off light"}

            if action_lower in ["set_brightness", "set brightness"]:
                if not light_id:
                    return {"success": False, "error": "light_id is required to set brightness"}
                if brightness_percent is None:
                    return {"success": False, "error": "brightness_percent is required"}
                if not hue_manager._initialized:
                    await hue_manager.initialize()
                success = await hue_manager.set_light_state(
                    light_id, on=True, brightness_percent=brightness_percent
                )
                if success:
                    light = await hue_manager.get_light(light_id)
                    return {
                        "success": True,
                        "action": "set_brightness",
                        "data": {"light": _model_dump(light) if light else None},
                    }
                return {"success": False, "error": "Failed to set brightness"}

            if action_lower in ["list_groups", "list groups"]:
                if not hue_manager._initialized:
                    await hue_manager.initialize()
                groups = await hue_manager.get_all_groups()
                return {
                    "success": True,
                    "action": "list_groups",
                    "data": {
                        "groups": [_model_dump(group) for group in groups],
                        "count": len(groups),
                    },
                }

            if action_lower in ["list_scenes", "list scenes"]:
                if not hue_manager._initialized:
                    await hue_manager.initialize()
                scenes = await hue_manager.get_all_scenes()
                # Filter to unique predefined scenes
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
                    "action": "list_scenes",
                    "data": {
                        "scenes": [_model_dump(scene) for scene in filtered_scenes],
                        "count": len(filtered_scenes),
                    },
                }

            if action_lower in ["activate_scene", "activate scene"]:
                if not scene_id:
                    return {"success": False, "error": "scene_id is required to activate a scene"}
                if not hue_manager._initialized:
                    await hue_manager.initialize()
                success = await hue_manager.activate_scene(scene_id, group_id)
                return {"success": success, "action": "activate_scene", "data": {"scene_id": scene_id}}

            # Energy/Plug actions
            if action_lower in ["list_plugs", "list_plug", "list plugs", "list plug"]:
                devices = await tapo_plug_manager.get_all_devices()
                return {
                    "success": True,
                    "action": "list_plugs",
                    "data": {
                        "devices": [
                            {
                                "device_id": device.device_id,
                                "name": device.name,
                                "power_state": device.power_state,
                                "power_watt": device.power_watt,
                                "voltage": device.voltage,
                                "current": device.current,
                            }
                            for device in devices
                        ],
                        "count": len(devices),
                    },
                }

            if action_lower in ["turn_on_plug", "turn on plug", "on plug"]:
                if not device_id:
                    return {"success": False, "error": "device_id is required to turn on a plug"}
                success = await tapo_plug_manager.toggle_device(device_id, True)
                if success:
                    device = await tapo_plug_manager.get_device_status(device_id)
                    return {
                        "success": True,
                        "action": "turn_on_plug",
                        "data": {
                            "device_id": device_id,
                            "power_state": device.power_state if device else True,
                        },
                    }
                return {"success": False, "error": "Failed to turn on plug"}

            if action_lower in ["turn_off_plug", "turn off plug", "off plug"]:
                if not device_id:
                    return {"success": False, "error": "device_id is required to turn off a plug"}
                success = await tapo_plug_manager.toggle_device(device_id, False)
                if success:
                    device = await tapo_plug_manager.get_device_status(device_id)
                    return {
                        "success": True,
                        "action": "turn_off_plug",
                        "data": {
                            "device_id": device_id,
                            "power_state": device.power_state if device else False,
                        },
                    }
                return {"success": False, "error": "Failed to turn off plug"}

            # Kitchen actions
            if action_lower in ["list_kitchen", "list kitchen"]:
                all_devices = await tapo_plug_manager.get_all_devices()
                kitchen_keywords = ["kitchen", "zojirushi", "kettle", "optigrill", "grill"]
                kitchen_devices = [
                    device
                    for device in all_devices
                    if any(keyword.lower() in device.name.lower() for keyword in kitchen_keywords)
                ]
                return {
                    "success": True,
                    "action": "list_kitchen",
                    "data": {
                        "appliances": [
                            {
                                "device_id": device.device_id,
                                "name": device.name,
                                "power_state": device.power_state,
                                "power_watt": device.power_watt,
                            }
                            for device in kitchen_devices
                        ],
                        "count": len(kitchen_devices),
                    },
                }

            if action_lower in ["turn_on_kettle", "turn on kettle", "on kettle"]:
                # Find Zojirushi kettle
                all_devices = await tapo_plug_manager.get_all_devices()
                kettle = next(
                    (d for d in all_devices if "zojirushi" in d.name.lower() or "kettle" in d.name.lower()), None
                )
                if not kettle:
                    return {"success": False, "error": "Zojirushi kettle not found"}
                success = await tapo_plug_manager.toggle_device(kettle.device_id, True)
                return {
                    "success": success,
                    "action": "turn_on_kettle",
                    "data": {"device_id": kettle.device_id, "name": kettle.name},
                }

            if action_lower in ["turn_off_kettle", "turn off kettle", "off kettle"]:
                # Find Zojirushi kettle
                all_devices = await tapo_plug_manager.get_all_devices()
                kettle = next(
                    (d for d in all_devices if "zojirushi" in d.name.lower() or "kettle" in d.name.lower()), None
                )
                if not kettle:
                    return {"success": False, "error": "Zojirushi kettle not found"}
                success = await tapo_plug_manager.toggle_device(kettle.device_id, False)
                return {
                    "success": success,
                    "action": "turn_off_kettle",
                    "data": {"device_id": kettle.device_id, "name": kettle.name},
                }

            # Status
            if action_lower == "status":
                lights_count = 0
                plugs_count = 0
                if hue_manager._initialized:
                    lights_count = len(hue_manager.lights)
                devices = await tapo_plug_manager.get_all_devices()
                plugs_count = len(devices)
                return {
                    "success": True,
                    "action": "status",
                    "data": {
                        "lights": lights_count,
                        "smart_plugs": plugs_count,
                        "hue_connected": hue_manager._initialized,
                    },
                }

            return {
                "success": False,
                "error": f"Unknown action '{action}'. Available actions: {', '.join(TAPO_ACTIONS.keys())}",
            }

        except Exception as e:
            logger.error(f"Error in tapo action '{action}': {e}", exc_info=True)
            return {"success": False, "error": f"Failed to execute action '{action}': {e!s}"}



