"""
Lighting Management Portmanteau Tool

Consolidates all lighting-related operations into a single tool with action-based interface.
"""

import asyncio
import contextlib
import logging
import random
from typing import Any, Literal

from fastmcp import FastMCP

from tapo_camera_mcp.tools.lighting.hue_tools import hue_manager

logger = logging.getLogger(__name__)


async def _prank_chaos(duration: float) -> dict[str, Any]:
    """Chaos mode - random on/off for all lights."""
    end_time = asyncio.get_event_loop().time() + duration
    original_states: dict[str, bool] = {}

    # Save original states
    for light_id, light in hue_manager.lights.items():
        original_states[light_id] = light.on

    light_ids = list(hue_manager.lights.keys())
    cycles = 0

    while asyncio.get_event_loop().time() < end_time:
        # Random subset of lights
        targets = random.sample(light_ids, k=random.randint(1, len(light_ids)))
        for lid in targets:
            with contextlib.suppress(Exception):
                await hue_manager.set_light_state(lid, on=random.choice([True, False]))
        cycles += 1
        await asyncio.sleep(0.15)

    # Restore original states
    for lid, was_on in original_states.items():
        with contextlib.suppress(Exception):
            await hue_manager.set_light_state(lid, on=was_on)

    return {"mode": "chaos", "cycles": cycles, "lights": len(light_ids)}


async def _prank_wave(duration: float) -> dict[str, Any]:
    """Wave mode - sequential room-to-room pattern."""
    end_time = asyncio.get_event_loop().time() + duration
    original_states: dict[str, bool] = {}

    # Save original states
    for gid, group in hue_manager.groups.items():
        original_states[gid] = group.on

    group_ids = list(hue_manager.groups.keys())
    cycles = 0

    while asyncio.get_event_loop().time() < end_time:
        for i, _gid in enumerate(group_ids):
            if asyncio.get_event_loop().time() >= end_time:
                break
            try:
                # Turn this group on, others off
                for j, other_gid in enumerate(group_ids):
                    await hue_manager.set_group_state(other_gid, on=(i == j))
            except Exception:  # noqa: S110 - best effort for prank mode
                pass
            await asyncio.sleep(0.3)
        cycles += 1

    # Restore original states
    for gid, was_on in original_states.items():
        with contextlib.suppress(Exception):
            await hue_manager.set_group_state(gid, on=was_on)

    return {"mode": "wave", "cycles": cycles, "groups": len(group_ids)}


async def _prank_disco(duration: float) -> dict[str, Any]:
    """Disco mode - rapid brightness changes."""
    end_time = asyncio.get_event_loop().time() + duration
    cycles = 0

    group_ids = list(hue_manager.groups.keys())

    while asyncio.get_event_loop().time() < end_time:
        for gid in group_ids:
            try:
                brightness = random.randint(20, 254)
                await hue_manager.set_group_state(gid, on=True, brightness=brightness)
            except Exception:  # noqa: S110 - best effort for prank mode
                pass
        cycles += 1
        await asyncio.sleep(0.2)

    return {"mode": "disco", "cycles": cycles}


async def _prank_sos(duration: float) -> dict[str, Any]:
    """SOS mode - morse code pattern (... --- ...)."""
    # S = ... (3 short), O = --- (3 long), S = ... (3 short)
    morse_sos = [0.1, 0.1, 0.1, 0.3, 0.3, 0.3, 0.1, 0.1, 0.1]  # durations
    group_ids = list(hue_manager.groups.keys())
    cycles = 0
    end_time = asyncio.get_event_loop().time() + duration

    while asyncio.get_event_loop().time() < end_time:
        for flash_dur in morse_sos:
            if asyncio.get_event_loop().time() >= end_time:
                break
            # All on
            for gid in group_ids:
                with contextlib.suppress(Exception):
                    await hue_manager.set_group_state(gid, on=True, brightness=254)
            await asyncio.sleep(flash_dur)
            # All off
            for gid in group_ids:
                with contextlib.suppress(Exception):
                    await hue_manager.set_group_state(gid, on=False)
            await asyncio.sleep(0.1)
        cycles += 1
        await asyncio.sleep(0.5)

    return {"mode": "sos", "cycles": cycles}


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
    "rescan": "Rescan all lights/groups/scenes from bridge (fixes stale state)",
    "prank": "Fun light show modes: chaos, wave, disco, sos (max 10 sec)",
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
            "rescan",
            "prank",
        ],
        light_id: str | None = None,
        group_id: str | None = None,
        scene_id: str | None = None,
        on: bool | None = None,
        brightness_percent: int | None = None,
        color_temp_kelvin: int | None = None,
        prank_mode: Literal["chaos", "wave", "disco", "sos"] | None = None,
        duration: int = 5,
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
                - "rescan": Force rescan of all lights/groups/scenes from bridge (fixes stale state on startup)
                - "prank": Fun light show modes (requires: prank_mode, optional: duration)

            light_id (str | None): Light ID. Required for: get_light, control_light operations.

            group_id (str | None): Group ID. Required for: control_group operation.
                Optional for: activate_scene operation (uses scene's default group if not provided).

            scene_id (str | None): Scene ID. Required for: activate_scene operation.

            on (bool | None): Turn light/group on (True) or off (False). Used by: control_light, control_group operations.

            brightness_percent (int | None): Brightness percentage (0-100). Used by: control_light, control_group operations.

            color_temp_kelvin (int | None): Color temperature in Kelvin. Used by: control_light operation.

            prank_mode (Literal["chaos", "wave", "disco", "sos"] | None): Prank mode for fun light shows:
                - "chaos": Random on/off for all lights
                - "wave": Sequential room-to-room pattern
                - "disco": Rapid brightness changes
                - "sos": Morse code SOS pattern (... --- ...)

            duration (int): Duration in seconds for prank mode (1-10, default 5). Max 10 sec for safety.

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

            if action == "rescan":
                result = await hue_manager.rescan()
                return {
                    "success": True,
                    "action": action,
                    "data": result,
                }

            if action == "prank":
                if not prank_mode:
                    return {"success": False, "error": "prank_mode is required (chaos, wave, disco, sos)"}

                # Cap duration at 10 seconds for safety
                safe_duration = min(max(1, duration), 10)

                logger.info(f"Starting prank mode '{prank_mode}' for {safe_duration} seconds")

                if prank_mode == "chaos":
                    result = await _prank_chaos(safe_duration)
                elif prank_mode == "wave":
                    result = await _prank_wave(safe_duration)
                elif prank_mode == "disco":
                    result = await _prank_disco(safe_duration)
                elif prank_mode == "sos":
                    result = await _prank_sos(safe_duration)
                else:
                    return {"success": False, "error": f"Unknown prank mode: {prank_mode}"}

                return {
                    "success": True,
                    "action": action,
                    "data": {"duration": safe_duration, **result},
                }

            return {"success": False, "error": f"Action '{action}' not implemented"}

        except Exception as e:
            logger.error(f"Error in lighting management action '{action}': {e}", exc_info=True)
            return {"success": False, "error": f"Failed to execute action '{action}': {e!s}"}

