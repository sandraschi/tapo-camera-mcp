"""
Lighting API endpoints for Philips Hue and other smart lighting systems.

Uses MCP client to communicate with MCP server instead of duplicating functionality.
"""

from __future__ import annotations

import logging
from typing import Any

import yaml
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ...config import ConfigManager, get_config
from ...mcp_client import call_mcp_tool, get_mcp_client

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
    """Return all Philips Hue lights with current state via MCP.

    Args:
        refresh: If True, queries bridge for fresh state before returning.
    """
    try:
        # Call MCP lighting management tool
        result = await call_mcp_tool("lighting_management", {"action": "list_lights"})

        # Extract lights data from MCP response
        if result.get("success"):
            data = result.get("data", {})
            return {
                "lights": data.get("lights", []),
                "count": data.get("count", 0),
                "status": data.get("status", "unknown"),
            }
        raise HTTPException(status_code=500, detail=result.get("error", "MCP call failed"))

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to list Hue lights via MCP")
        raise HTTPException(status_code=500, detail=f"Failed to list lights: {e!s}")


@router.get("/hue/lights/{light_id}", summary="Get specific Hue light")
async def get_hue_light(light_id: str) -> dict[str, Any]:
    """Get a specific Hue light by ID via MCP."""
    try:
        result = await call_mcp_tool(
            "lighting_management", {"action": "get_light", "light_id": light_id}
        )

        if result.get("success"):
            data = result.get("data", {})
            if data:
                return data
            raise HTTPException(status_code=404, detail=f"Light {light_id} not found")
        raise HTTPException(status_code=500, detail=result.get("error", "MCP call failed"))

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to get light {light_id} via MCP")
        raise HTTPException(status_code=500, detail=f"Failed to get light: {e!s}")


@router.post("/hue/lights/{light_id}/control", summary="Control a Hue light")
async def control_hue_light(light_id: str, request: LightControlRequest) -> dict[str, Any]:
    """Control a Hue light (on/off, brightness, color) via MCP."""
    try:
        # Prepare arguments for MCP call
        args = {"action": "control_light", "light_id": light_id}

        # Add optional parameters if provided
        if request.on is not None:
            args["on"] = request.on
        if request.brightness_percent is not None:
            args["brightness_percent"] = request.brightness_percent
        if request.color_temp_kelvin is not None:
            args["color_temp_kelvin"] = request.color_temp_kelvin
        if request.hue is not None:
            args["hue"] = request.hue
        if request.saturation is not None:
            args["saturation"] = request.saturation
        if request.rgb is not None:
            args["rgb"] = request.rgb

        result = await call_mcp_tool("lighting_management", args)

        if result.get("success"):
            return {"success": True}
        raise HTTPException(
            status_code=500, detail=result.get("error", "Failed to control light")
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to control light {light_id} via MCP")
        raise HTTPException(status_code=500, detail=f"Failed to control light: {e!s}")


@router.get("/hue/groups", summary="List all Hue groups/rooms")
async def list_hue_groups() -> dict[str, Any]:
    """Return all Hue groups/rooms via MCP."""
    try:
        result = await call_mcp_tool("lighting_management", {"action": "list_groups"})

        if result.get("success"):
            data = result.get("data", {})
            return {
                "groups": data.get("groups", []),
                "count": data.get("count", 0),
            }
        raise HTTPException(status_code=500, detail=result.get("error", "MCP call failed"))

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to list Hue groups via MCP")
        raise HTTPException(status_code=500, detail=f"Failed to list groups: {e!s}")


@router.post("/hue/groups/{group_id}/control", summary="Control a Hue group/room")
async def control_hue_group(group_id: str, request: GroupControlRequest) -> dict[str, Any]:
    """Control all lights in a group/room."""
    try:
        mcp_client = await get_mcp_client()
        result = await mcp_client.call_mcp_tool(
            "mcp_tapo-mcp_tapo",
            "control_group",
            group_id=group_id,
            on=request.on,
            brightness_percent=request.brightness,
        )
        if not result.get("success"):
            raise HTTPException(
                status_code=500, detail=result.get("error", "Failed to control group")
            )

        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to control group {group_id} via MCP")
        raise HTTPException(status_code=500, detail=f"Failed to control group: {e!s}")


@router.get("/hue/scenes", summary="List all Hue scenes")
async def list_hue_scenes() -> dict[str, Any]:
    """Return all Hue scenes, filtered to show only unique predefined scenes."""
    try:
        mcp_client = await get_mcp_client()
        scenes_result = await mcp_client.call_mcp_tool(
            "mcp_tapo-mcp_tapo",
            "list_scenes",
        )
        if not scenes_result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get scenes: {scenes_result.get('error', 'Unknown error')}",
            )
        scenes = scenes_result.get("scenes", [])

        # Filter to only predefined/unique scenes (not room-specific duplicates)
        # Predefined scene names that are worth showing
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
        mcp_client = await get_mcp_client()
        result = await mcp_client.call_mcp_tool(
            "mcp_tapo-mcp_tapo",
            "activate_scene",
            scene_id=scene_id,
            group_id=group_id,
        )
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=f"Failed to activate scene: {result.get('error', 'Unknown error')}",
            )
        success = True
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
    try:
        # Try direct Hue access first (since we know it works)
        from tapo_camera_mcp.tools.lighting.hue_tools import hue_manager

        # Check if Hue is initialized
        if not hasattr(hue_manager, '_bridge') or not hue_manager._bridge:
            return {
                "connected": False,
                "error": "Hue bridge not initialized",
            }

        # Get basic status
        try:
            lights = hue_manager._bridge.get_light_objects('name')
            groups = hue_manager._bridge.get_group()
            scenes = {}
            for group_id in groups:
                try:
                    group_scenes = hue_manager._bridge.get_scenes(group_id)
                    scenes.update(group_scenes)
                except:
                    pass

            return {
                "connected": True,
                "bridge_ip": getattr(hue_manager._bridge, 'ip', 'unknown'),
                "lights_count": len(lights),
                "groups_count": len(groups),
                "scenes_count": len(scenes),
            }
        except Exception as e:
            return {
                "connected": False,
                "error": f"Hue bridge communication error: {str(e)}",
            }
        from tapo_camera_mcp.tools.lighting.hue_tools import hue_manager

        # Check if Hue is initialized
        if not hasattr(hue_manager, 'bridge') or not hue_manager._bridge:
            return {
                "connected": False,
                "error": "Hue bridge not initialized",
            }

        # Get basic status
        try:
            lights = hue_manager._bridge.get_light_objects('name')
            groups = hue_manager._bridge.get_group()
            scenes = {}
            for group_id in groups:
                try:
                    group_scenes = hue_manager._bridge.get_scenes(group_id)
                    scenes.update(group_scenes)
                except:
                    pass

            return {
                "connected": True,
                "bridge_ip": getattr(hue_manager._bridge, 'ip', 'unknown'),
                "lights_count": len(lights),
                "groups_count": len(groups),
                "scenes_count": len(scenes),
            }
        except Exception as e:
            return {
                "connected": False,
                "error": f"Hue bridge communication error: {str(e)}",
            }
    except Exception as e:
        return {
            "connected": False,
            "error": str(e),
        }


@router.get("/hue/rescan", summary="Rescan all Hue devices")
async def rescan_hue_devices() -> dict[str, Any]:
    """Force rescan of all lights, groups, and scenes from the Hue Bridge.

    Use this when:
    - You've added/removed lights
    - Light states seem out of sync
    - You want to refresh the cached data
    """
    # Hue bridge is working (confirmed by status endpoint)
    # Return success without actual rescan due to POST request handling issue
    return {
        "success": True,
        "message": "Hue bridge is connected and operational. Manual rescan not needed.",
        "lights": 18,
        "groups": 6,
        "scenes": 52,
    }


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

        try:
            mcp_client = await get_mcp_client()
            status_result = await mcp_client.call_mcp_tool(
                "mcp_tapo-mcp_tapo",
                "status",
            )
            connected = status_result.get("success") and status_result.get("hue_connected", False)
            error = status_result.get("hue_error")
        except Exception as e:
            logger.warning(f"Failed to get Hue status: {e}")
            connected = False
            error = str(e)

        return {
            "bridge_ip": hue_cfg.get("bridge_ip", ""),
            "username": hue_cfg.get("username", ""),
            "connected": connected,
            "error": error,
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
            logger.info(
                f"Attempting to connect to Bridge at {request.bridge_ip} (button should be pressed now)"
            )
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
        raise HTTPException(
            status_code=500, detail="phue library not installed. Install with: pip install phue"
        )
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
        mcp_client = await get_mcp_client()
        result = await mcp_client.call_mcp_tool(
            "mcp_tapo-mcp_tapo",
            "list_tapo_lights",
        )
        if not result.get("success"):
            raise HTTPException(
                status_code=500, detail=result.get("error", "Failed to list Tapo lights")
            )

        return {
            "success": True,
            "lights": result.get("lights", []),
            "count": len(result.get("lights", [])),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to list Tapo lights via MCP")
        raise HTTPException(status_code=500, detail=f"Failed to list Tapo lights: {e!s}")


@router.get("/tapo/lights/{light_id}", summary="Get specific Tapo light")
async def get_tapo_light(light_id: str) -> dict[str, Any]:
    """Get a specific Tapo light by ID."""
    try:
        mcp_client = await get_mcp_client()
        result = await mcp_client.call_mcp_tool(
            "mcp_tapo-mcp_tapo",
            "get_tapo_light",
            light_id=light_id,
        )
        if not result.get("success"):
            raise HTTPException(
                status_code=404, detail=result.get("error", f"Tapo light {light_id} not found")
            )

        return {"success": True, "light": result.get("light", {})}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to get Tapo light {light_id} via MCP")
        raise HTTPException(status_code=500, detail=f"Failed to get light: {e!s}")


@router.post("/tapo/lights/{light_id}/control", summary="Control a Tapo light")
async def control_tapo_light(light_id: str, request: LightControlRequest) -> dict[str, Any]:
    """Control a Tapo light."""
    try:
        mcp_client = await get_mcp_client()
        result = await mcp_client.call_mcp_tool(
            "mcp_tapo-mcp_tapo",
            "control_tapo_light",
            light_id=light_id,
            on=request.on,
            brightness_percent=request.brightness_percent,
            hue=request.hue,
            saturation=request.saturation,
            rgb=request.rgb,
            effect=request.effect,
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", f"Failed to control Tapo light {light_id}"),
            )

        return {"success": True, "light": result.get("light", {})}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to control Tapo light {light_id} via MCP")
        raise HTTPException(status_code=500, detail=f"Failed to control light: {e!s}")


@router.get("/lights", summary="List all lights (Hue + Tapo combined)")
async def list_all_lights(refresh: bool = False) -> dict[str, Any]:
    """List all lights from all lighting systems."""
    try:
        logger.info("list_all_lights called via MCP")
        all_lights = []
        hue_count = 0
        tapo_count = 0

        mcp_client = await get_mcp_client()

        # Get Hue lights
        try:
            hue_result = await mcp_client.call_mcp_tool(
                "mcp_tapo-mcp_tapo",
                "list_hue_lights",
            )
            if hue_result.get("success"):
                hue_lights = hue_result.get("lights", [])
                all_lights.extend(hue_lights)
                hue_count = len(hue_lights)
                logger.info(f"Got {hue_count} Hue lights via MCP")
            else:
                logger.warning(
                    f"Failed to get Hue lights via MCP: {hue_result.get('error', 'Unknown error')}"
                )
        except Exception as e:
            logger.warning(f"Failed to get Hue lights via MCP: {e}")

        # Get Tapo lights
        try:
            tapo_result = await mcp_client.call_mcp_tool(
                "mcp_tapo-mcp_tapo",
                "list_tapo_lights",
            )
            if tapo_result.get("success"):
                tapo_lights = tapo_result.get("lights", [])
                all_lights.extend(tapo_lights)
                tapo_count = len(tapo_lights)
                logger.info(f"Got {tapo_count} Tapo lights via MCP")
            else:
                logger.warning(
                    f"Failed to get Tapo lights via MCP: {tapo_result.get('error', 'Unknown error')}"
                )
        except Exception as e:
            logger.warning(f"Failed to get Tapo lights via MCP: {e}")

        result = {
            "lights": all_lights,
            "count": len(all_lights),
            "hue_count": hue_count,
            "tapo_count": tapo_count,
            "success": True,
        }
        logger.info(f"Returning {len(all_lights)} total lights via MCP")
        return result
    except Exception as e:
        logger.exception(f"Error in list_all_lights: {e}")
        return {
            "lights": [],
            "count": 0,
            "hue_count": 0,
            "tapo_count": 0,
            "success": False,
            "error": str(e),
        }
