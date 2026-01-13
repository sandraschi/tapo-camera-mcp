"""
Lighting API endpoints for Philips Hue and other smart lighting systems.
"""

from __future__ import annotations

import logging
from typing import Any

import yaml
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ...config import ConfigManager, get_config
from ...tools.lighting.hue_tools import get_hue_manager
from ...tools.lighting.tapo_lighting_tools import tapo_lighting_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/lighting", tags=["lighting"])

# Get config path from ConfigManager
_config_manager = ConfigManager()
CONFIG_PATH = _config_manager.config_path


class LightControlRequest(BaseModel):
    """Request model for controlling lights."""
    on: bool | None = None
    brightness_percent: int | None = None
    color_temp_kelvin: int | None = None
    hue: int | None = None
    saturation: int | None = None
    rgb: list[int] | None = None
    effect: str | None = None


class GroupControlRequest(BaseModel):
    """Request model for controlling groups."""
    on: bool | None = None
    brightness: int | None = None


def _model_dump(model: Any) -> dict[str, Any]:
    """Serialize Pydantic models across v1/v2."""
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()  # type: ignore[attr-defined]


@router.get("/hue/lights", summary="List all Philips Hue lights")
async def list_hue_lights(refresh: bool = False) -> dict[str, Any]:
    """Return all Philips Hue lights with current state.
    
    Args:
        refresh: If True, queries bridge for fresh state before returning.
    """
    hue_manager = get_hue_manager()
    try:
        import asyncio
        # Refresh from bridge if requested
        if refresh and hue_manager._initialized:
            await asyncio.wait_for(
                hue_manager._discover_devices(),
                timeout=10.0  # 10 second timeout for refresh
            )

        lights = await asyncio.wait_for(
            hue_manager.get_all_lights(),
            timeout=10.0  # 10 second timeout for getting lights
        )
        return {
            "lights": [_model_dump(light) for light in lights],
            "count": len(lights),
            "status": "connected" if hue_manager._initialized else "disconnected",
        }
    except Exception as e:
        logger.exception("Failed to list Hue lights")
        raise HTTPException(status_code=500, detail=f"Failed to list lights: {e!s}")


@router.get("/hue/lights/{light_id}", summary="Get specific Hue light")
async def get_hue_light(light_id: str) -> dict[str, Any]:
    """Get a specific Hue light by ID."""
    try:
        light = await asyncio.wait_for(
            hue_manager.get_light(light_id),
            timeout=10.0
        )
        if not light:
            raise HTTPException(status_code=404, detail=f"Light {light_id} not found")
        return _model_dump(light)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to get light {light_id}")
        raise HTTPException(status_code=500, detail=f"Failed to get light: {e!s}")


@router.post("/hue/lights/{light_id}/control", summary="Control a Hue light")
async def control_hue_light(light_id: str, request: LightControlRequest) -> dict[str, Any]:
    """Control a Hue light (on/off, brightness, color). Returns immediately for speed."""
    try:
        success = await hue_manager.set_light_state(
            light_id,
            on=request.on,
            brightness_percent=request.brightness_percent,
            color_temp=request.color_temp_kelvin,
            hue=request.hue,
            saturation=request.saturation,
            rgb=request.rgb,
        )
        if not success:
            raise HTTPException(status_code=500, detail="Failed to control light")

        # Return immediately - don't wait for bridge or refetch state
        return {"success": True}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Failed to control light {light_id}")
        raise HTTPException(status_code=500, detail=f"Failed to control light: {e!s}")


@router.get("/hue/groups", summary="List all Hue groups/rooms")
async def list_hue_groups() -> dict[str, Any]:
    """Return all Hue groups/rooms."""
    try:
        groups = await hue_manager.get_all_groups()
        return {
            "groups": [_model_dump(group) for group in groups],
            "count": len(groups),
        }
    except Exception as e:
        logger.exception("Failed to list Hue groups")
        raise HTTPException(status_code=500, detail=f"Failed to list groups: {e!s}")


@router.post("/hue/groups/{group_id}/control", summary="Control a Hue group/room")
async def control_hue_group(group_id: str, request: GroupControlRequest) -> dict[str, Any]:
    """Control all lights in a group/room."""
    try:
        success = await hue_manager.set_group_state(
            group_id,
            on=request.on,
            brightness=request.brightness,
        )
        if not success:
            raise HTTPException(status_code=500, detail="Failed to control group")

        return {"success": True}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Failed to control group {group_id}")
        raise HTTPException(status_code=500, detail=f"Failed to control group: {e!s}")


@router.get("/hue/scenes", summary="List all Hue scenes")
async def list_hue_scenes() -> dict[str, Any]:
    """Return all Hue scenes, filtered to show only unique predefined scenes."""
    try:
        scenes = await hue_manager.get_all_scenes()

        # Filter to only predefined/unique scenes (not room-specific duplicates)
        # Predefined scene names that are worth showing
        predefined_scenes = {
            "Arctic aurora", "Bright", "Concentrate", "Dimmed", "Energize",
            "Nightlight", "Read", "Relax", "Savanna sunset", "Spring blossom",
            "Tropical twilight"
        }

        # Get unique scenes by name (prefer scenes with groups, but show all unique names)
        seen_names = set()
        filtered_scenes = []

        for scene in scenes:
            scene_name = scene.name
            # Only include predefined scenes or unique scene names
            if scene_name in predefined_scenes:
                if scene_name not in seen_names:
                    seen_names.add(scene_name)
                    filtered_scenes.append(scene)
            elif scene_name not in seen_names and scene_name not in predefined_scenes:
                # Include other unique scenes too (in case there are custom ones)
                seen_names.add(scene_name)
                filtered_scenes.append(scene)

        return {
            "scenes": [_model_dump(scene) for scene in filtered_scenes],
            "count": len(filtered_scenes),
        }
    except Exception as e:
        logger.exception("Failed to list Hue scenes")
        raise HTTPException(status_code=500, detail=f"Failed to list scenes: {e!s}")


@router.post("/hue/scenes/{scene_id}/activate", summary="Activate a Hue scene")
async def activate_hue_scene(scene_id: str, group_id: str | None = None) -> dict[str, Any]:
    """Activate a Hue scene."""
    try:
        success = await hue_manager.activate_scene(scene_id, group_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to activate scene")

        return {"success": True, "scene_id": scene_id}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Failed to activate scene {scene_id}")
        raise HTTPException(status_code=500, detail=f"Failed to activate scene: {e!s}")


@router.get("/hue/status", summary="Get Hue Bridge connection status")
async def get_hue_status() -> dict[str, Any]:
    """Get Hue Bridge connection status."""
    # Auto-initialize on first status check
    if not hue_manager._initialized and not hue_manager._connection_error:
        await hue_manager.initialize()

    return {
        "connected": hue_manager._initialized,
        "bridge_ip": hue_manager._bridge_ip,
        "lights_count": len(hue_manager.lights),
        "groups_count": len(hue_manager.groups),
        "scenes_count": len(hue_manager.scenes),
        "last_scan": hue_manager._last_scan_time.isoformat() if hue_manager._last_scan_time else None,
        "error": hue_manager._connection_error,
    }


@router.post("/hue/rescan", summary="Rescan all Hue devices")
async def rescan_hue_devices() -> dict[str, Any]:
    """Force rescan of all lights, groups, and scenes from the Hue Bridge.
    
    Use this when:
    - You've added/removed lights
    - Light states seem out of sync
    - You want to refresh the cached data
    """
    try:
        if not hue_manager._initialized:
            await hue_manager.initialize()

        result = await hue_manager.rescan()
        return {
            "success": True,
            "message": f"Rescanned {result['lights']} lights, {result['groups']} groups, {result['scenes']} scenes",
            **result,
        }
    except Exception as e:
        logger.exception("Failed to rescan Hue devices")
        raise HTTPException(status_code=500, detail=f"Failed to rescan: {e!s}")


class HueConfigRequest(BaseModel):
    """Request model for Hue Bridge configuration."""
    bridge_ip: str
    username: str | None = None


@router.get("/hue/config", summary="Get Hue Bridge configuration")
async def get_hue_config() -> dict[str, Any]:
    """Get current Hue Bridge configuration from config.yaml."""
    try:
        config = get_config() or {}
        hue_cfg = config.get("lighting", {}).get("philips_hue", {})

        return {
            "bridge_ip": hue_cfg.get("bridge_ip", ""),
            "username": hue_cfg.get("username", ""),
            "connected": hue_manager._initialized,
            "error": hue_manager._connection_error,
        }
    except Exception as e:
        logger.exception("Failed to get Hue config")
        raise HTTPException(status_code=500, detail=f"Failed to get config: {e!s}")


@router.post("/hue/config", summary="Save Hue Bridge configuration")
async def save_hue_config(request: HueConfigRequest) -> dict[str, Any]:
    """Save Hue Bridge configuration to config.yaml."""
    try:
        # Read current config
        if not CONFIG_PATH.exists():
            raise HTTPException(status_code=404, detail="config.yaml not found")

        with open(CONFIG_PATH, encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}

        # Update Hue config
        if "lighting" not in config:
            config["lighting"] = {}
        if "philips_hue" not in config["lighting"]:
            config["lighting"]["philips_hue"] = {}

        config["lighting"]["philips_hue"]["bridge_ip"] = request.bridge_ip
        if request.username:
            config["lighting"]["philips_hue"]["username"] = request.username
        elif "username" in config["lighting"]["philips_hue"]:
            # Keep existing username if not provided
            pass

        # Write back to file
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

        logger.info(f"Hue Bridge configuration saved: bridge_ip={request.bridge_ip}")

        return {
            "success": True,
            "message": "Configuration saved successfully. Please restart the server for changes to take effect.",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to save Hue config")
        raise HTTPException(status_code=500, detail=f"Failed to save config: {e!s}")


@router.post("/hue/test-connection", summary="Test Hue Bridge connection")
async def test_hue_connection(request: HueConfigRequest) -> dict[str, Any]:
    """Test connection to Hue Bridge without saving configuration."""
    try:
        from phue import Bridge

        if not request.bridge_ip:
            raise HTTPException(status_code=400, detail="Bridge IP is required")

        # Try to connect
        try:
            if request.username:
                bridge = Bridge(request.bridge_ip, username=request.username)
            else:
                # Try without username (will fail but gives us error message)
                bridge = Bridge(request.bridge_ip)
                username = bridge.username
        except Exception as e:
            error_msg = str(e)
            if "link button not pressed" in error_msg.lower():
                return {
                    "success": False,
                    "error": "Please press the button on your Hue Bridge and try again",
                }
            return {
                "success": False,
                "error": error_msg,
            }

        # Get light count
        lights = bridge.lights
        groups = bridge.groups

        return {
            "success": True,
            "lights_count": len(lights),
            "groups_count": len(groups),
            "username": bridge.username if hasattr(bridge, "username") else request.username,
        }
    except ImportError:
        raise HTTPException(status_code=500, detail="phue library not installed")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to test Hue connection")
        raise HTTPException(status_code=500, detail=f"Failed to test connection: {e!s}")


@router.post("/hue/connect", summary="Connect to Hue Bridge and generate username")
async def connect_hue_bridge(request: HueConfigRequest) -> dict[str, Any]:
    """Connect to Hue Bridge and generate API username (requires button press)."""
    try:
        from phue import Bridge

        if not request.bridge_ip:
            raise HTTPException(status_code=400, detail="Bridge IP is required")

        logger.info(f"Attempting to connect to Hue Bridge at {request.bridge_ip}")

        # Connect without username - this will prompt for button press
        try:
            # phue Bridge constructor connects immediately and prompts for button if needed
            # The button must be pressed BEFORE calling Bridge() - user has ~30 seconds
            logger.info(f"Attempting to connect to Bridge at {request.bridge_ip} (button should be pressed now)")
            bridge = Bridge(request.bridge_ip)
            username = bridge.username

            logger.info(f"Successfully connected to Hue Bridge. Username: {username}")

            return {
                "success": True,
                "username": username,
                "message": "Connection successful! Username generated.",
            }
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Hue Bridge connection error: {error_msg}")

            # Check for common error messages
            error_lower = error_msg.lower()
            if "link button not pressed" in error_lower or "unauthorized user" in error_lower:
                return {
                    "success": False,
                    "error": "Please press the button on your Hue Bridge and try again within 30 seconds",
                }
            if "connection" in error_lower or "refused" in error_lower or "timeout" in error_lower:
                return {
                    "success": False,
                    "error": f"Cannot reach Bridge at {request.bridge_ip}. Check IP address and network connection.",
                }
            if "not found" in error_lower or "404" in error_msg:
                return {
                    "success": False,
                    "error": f"Bridge not found at {request.bridge_ip}. Verify the IP address is correct.",
                }
            return {
                "success": False,
                "error": f"Connection error: {error_msg}",
            }
    except ImportError:
        raise HTTPException(status_code=500, detail="phue library not installed. Install with: pip install phue")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to connect to Hue Bridge")
        raise HTTPException(status_code=500, detail=f"Failed to connect: {e!s}")


# Tapo Lighting API Endpoints

@router.get("/tapo/lights", summary="List all Tapo smart lights")
async def list_tapo_lights(refresh: bool = False) -> dict[str, Any]:
    """List all configured Tapo lights."""
    try:
        if not tapo_lighting_manager._initialized:
            success = await tapo_lighting_manager.initialize()
            if not success:
                raise HTTPException(status_code=500, detail="Failed to initialize Tapo lighting")

        if refresh:
            await tapo_lighting_manager.rescan_devices()

        lights = await tapo_lighting_manager.get_all_lights()
        return {
            "success": True,
            "lights": [_model_dump(light) for light in lights],
            "count": len(lights)
        }
    except Exception as e:
        logger.exception("Failed to list Tapo lights")
        raise HTTPException(status_code=500, detail=f"Failed to list Tapo lights: {e!s}")


@router.get("/tapo/lights/{light_id}", summary="Get specific Tapo light")
async def get_tapo_light(light_id: str) -> dict[str, Any]:
    """Get a specific Tapo light by ID."""
    try:
        if not tapo_lighting_manager._initialized:
            success = await tapo_lighting_manager.initialize()
            if not success:
                raise HTTPException(status_code=500, detail="Failed to initialize Tapo lighting")

        light = await tapo_lighting_manager.get_light(light_id)
        if not light:
            raise HTTPException(status_code=404, detail=f"Tapo light {light_id} not found")

        return {
            "success": True,
            "light": _model_dump(light)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to get Tapo light {light_id}")
        raise HTTPException(status_code=500, detail=f"Failed to get light: {e!s}")


@router.post("/tapo/lights/{light_id}/control", summary="Control a Tapo light")
async def control_tapo_light(light_id: str, request: LightControlRequest) -> dict[str, Any]:
    """Control a Tapo light."""
    try:
        if not tapo_lighting_manager._initialized:
            success = await tapo_lighting_manager.initialize()
            if not success:
                raise HTTPException(status_code=500, detail="Failed to initialize Tapo lighting")

        success = await tapo_lighting_manager.set_light_state(
            light_id=light_id,
            on=request.on,
            brightness_percent=request.brightness_percent,
            hue=request.hue,
            saturation=request.saturation,
            rgb=request.rgb,
            effect=request.effect
        )

        if not success:
            raise HTTPException(status_code=500, detail=f"Failed to control Tapo light {light_id}")

        # Get updated light info
        light = await tapo_lighting_manager.get_light(light_id)

        return {
            "success": True,
            "light": _model_dump(light) if light else None
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to control Tapo light {light_id}")
        raise HTTPException(status_code=500, detail=f"Failed to control light: {e!s}")


@router.get("/lights", summary="List all lights (Hue + Tapo combined)")
async def list_all_lights(refresh: bool = False) -> dict[str, Any]:
    """List all lights from all lighting systems."""
    try:
        all_lights = []
        hue_count = 0
        tapo_count = 0

        # Get Hue lights
        try:
            if not hue_manager._initialized:
                await hue_manager.initialize()

            if refresh:
                await hue_manager.rescan_devices()

            hue_lights = await hue_manager.get_all_lights()
            all_lights.extend([_model_dump(light) for light in hue_lights])
            hue_count = len(hue_lights)
        except Exception as e:
            logger.warning(f"Failed to get Hue lights: {e}")

        # Get Tapo lights
        try:
            if not tapo_lighting_manager._initialized:
                await tapo_lighting_manager.initialize()

            if refresh:
                await tapo_lighting_manager.rescan_devices()

            tapo_lights = await tapo_lighting_manager.get_all_lights()
            all_lights.extend([_model_dump(light) for light in tapo_lights])
            tapo_count = len(tapo_lights)
        except Exception as e:
            logger.warning(f"Failed to get Tapo lights: {e}")

        return {
            "success": True,
            "lights": all_lights,
            "count": len(all_lights),
            "hue_count": hue_count,
            "tapo_count": tapo_count
        }
    except Exception as e:
        logger.exception("Failed to list all lights")
        raise HTTPException(status_code=500, detail=f"Failed to list lights: {e!s}")

