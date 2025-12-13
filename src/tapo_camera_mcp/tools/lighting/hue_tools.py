"""
Philips Hue Lighting Control Tools for Tapo Camera MCP

This module provides MCP tools for controlling Philips Hue lights, groups, and scenes.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from ...config import get_config
from ...tools.base_tool import BaseTool, ToolCategory, tool

logger = logging.getLogger(__name__)

# Try to import phue library
try:
    from phue import Bridge
    PHUE_AVAILABLE = True
except ImportError:
    PHUE_AVAILABLE = False
    Bridge = None  # type: ignore[assignment, misc]


class HueLight(BaseModel):
    """Philips Hue light device data model."""

    light_id: str = Field(..., description="Unique light identifier (Hue ID)")
    name: str = Field(..., description="Light name")
    room: str = Field(default="", description="Room/group name")
    model: str = Field(default="", description="Light model")
    manufacturer: str = Field(default="Philips", description="Manufacturer")
    on: bool = Field(..., description="Current power state")
    brightness: int = Field(..., description="Brightness (0-254)")
    brightness_percent: int = Field(..., description="Brightness percentage (0-100)")
    color_mode: str = Field(default="ct", description="Color mode (xy, ct, hs)")
    color_temp: int = Field(default=0, description="Color temperature (mireds)")
    color_temp_kelvin: int = Field(default=0, description="Color temperature (Kelvin)")
    hue: int = Field(default=0, description="Hue (0-65535)")
    saturation: int = Field(..., description="Saturation (0-254)")
    xy: List[float] = Field(default_factory=list, description="XY color coordinates")
    rgb: List[int] = Field(default_factory=list, description="RGB color values (0-255)")
    reachable: bool = Field(..., description="Whether light is reachable")
    last_seen: str = Field(..., description="Last communication timestamp")
    energy_usage: Optional[float] = Field(default=None, description="Power consumption in watts (if available)")


class HueGroup(BaseModel):
    """Philips Hue group/room data model."""

    group_id: str = Field(..., description="Unique group identifier")
    name: str = Field(..., description="Group/room name")
    type: str = Field(default="Room", description="Group type (Room, Zone, etc.)")
    lights: List[str] = Field(default_factory=list, description="Light IDs in this group")
    on: bool = Field(..., description="Whether any lights in group are on")
    brightness: int = Field(default=0, description="Average brightness")
    reachable_lights: int = Field(default=0, description="Number of reachable lights")


class HueScene(BaseModel):
    """Philips Hue scene data model."""

    scene_id: str = Field(..., description="Unique scene identifier")
    name: str = Field(..., description="Scene name")
    group: str = Field(default="", description="Group/room this scene belongs to")
    lights: List[str] = Field(default_factory=list, description="Light IDs in this scene")
    active: bool = Field(default=False, description="Whether scene is currently active")


class HueManager:
    """Manager for Philips Hue lights, groups, and scenes.
    
    Uses caching to avoid slow bridge queries on every operation.
    Call rescan() to refresh the cache when needed.
    """

    def __init__(self):
        self.lights: Dict[str, HueLight] = {}
        self.groups: Dict[str, HueGroup] = {}
        self.scenes: Dict[str, HueScene] = {}
        self._initialized = False
        self._bridge: Optional[Any] = None
        self._bridge_ip: Optional[str] = None
        self._bridge_username: Optional[str] = None
        self._connection_error: Optional[str] = None
        self._cache_loaded = False  # Track if we've loaded from bridge at least once
        self._last_scan_time: Optional[datetime] = None

    async def initialize(self) -> bool:
        """Initialize connection to Philips Hue Bridge."""
        try:
            if not PHUE_AVAILABLE:
                self._connection_error = "phue library not installed. Install with: pip install phue"
                logger.warning(self._connection_error)
                return False

            # Load configuration
            cfg = get_config() or {}
            hue_cfg = cfg.get("lighting", {}).get("philips_hue", {})

            bridge_ip = hue_cfg.get("bridge_ip")
            bridge_username = hue_cfg.get("username")

            if not bridge_ip:
                self._connection_error = "Hue Bridge IP not configured in config.yaml"
                logger.warning(self._connection_error)
                return False

            self._bridge_ip = bridge_ip
            self._bridge_username = bridge_username

            # Connect to bridge
            try:
                if bridge_username:
                    self._bridge = Bridge(bridge_ip, username=bridge_username)
                else:
                    # First-time connection - user needs to press bridge button
                    self._bridge = Bridge(bridge_ip)
                    # Get username after button press
                    self._bridge_username = self._bridge.username
                    logger.info(f"Hue Bridge connected. Username: {self._bridge_username}")
                    logger.info("Save this username to config.yaml: lighting.philips_hue.username")
            except Exception as e:
                self._connection_error = f"Failed to connect to Hue Bridge: {e!s}"
                logger.error(self._connection_error)
                if "link button not pressed" in str(e).lower():
                    self._connection_error += " - Press the button on your Hue Bridge and try again"
                return False

            # Discover devices (initial scan)
            await self._discover_devices()
            self._initialized = True
            self._cache_loaded = True
            self._last_scan_time = datetime.now()
            logger.info(f"Philips Hue initialized: {len(self.lights)} lights, {len(self.groups)} groups, {len(self.scenes)} scenes")
            return True

        except Exception as e:
            logger.exception("Failed to initialize Philips Hue")
            self._connection_error = str(e)
            return False

    async def _discover_devices(self):
        """Discover all Hue lights, groups, and scenes."""
        if not self._bridge:
            return

        try:
            # Discover lights (handle individual light errors gracefully)
            self.lights.clear()
            bridge_lights = self._bridge.lights
            for light in bridge_lights:
                try:
                    light_data = self._create_light_from_bridge(light)
                    self.lights[light_data.light_id] = light_data
                except Exception as e:
                    logger.warning(f"Failed to process light {getattr(light, 'light_id', 'unknown')}: {e}")
                    # Continue with other lights even if one fails

            # Discover groups
            self.groups.clear()
            try:
                bridge_groups = self._bridge.groups
                for group in bridge_groups:
                    try:
                        group_data = self._create_group_from_bridge(group)
                        self.groups[group_data.group_id] = group_data
                    except Exception as e:
                        logger.warning(f"Failed to process group {getattr(group, 'group_id', 'unknown')}: {e}")
            except Exception as e:
                logger.warning(f"Failed to discover groups: {e}")

            # Discover scenes
            self.scenes.clear()
            try:
                bridge_scenes = self._bridge.scenes
                for scene in bridge_scenes:
                    try:
                        scene_data = self._create_scene_from_bridge(scene)
                        self.scenes[scene_data.scene_id] = scene_data
                    except Exception as e:
                        logger.warning(f"Failed to process scene {getattr(scene, 'scene_id', 'unknown')}: {e}")
            except Exception as e:
                logger.warning(f"Failed to discover scenes: {e}")

            logger.info(f"Discovered {len(self.lights)} lights, {len(self.groups)} groups, {len(self.scenes)} scenes")

        except Exception:
            logger.exception("Failed to discover Hue devices")
            # Don't raise - return what we have

    def _create_light_from_bridge(self, light: Any) -> HueLight:
        """Create HueLight from phue Light object.
        
        Note: phue raises exceptions when accessing properties that don't exist
        for certain light types (e.g., colormode on white-only bulbs). We wrap
        all property accesses in try/except to handle this gracefully.
        """
        # Get brightness safely
        brightness = 0
        try:
            brightness = light.brightness
        except Exception:
            pass
        brightness_percent = int((brightness / 254) * 100) if brightness > 0 else 0

        # Get color temperature safely (not all lights support this)
        color_temp = 0
        color_temp_mireds = 0
        try:
            color_temp = light.colortemp_k
        except Exception:
            pass
        try:
            color_temp_mireds = light.colortemp
        except Exception:
            pass

        # Get XY color coordinates safely (color bulbs only)
        xy = []
        rgb = []
        try:
            xy_value = light.xy
            if xy_value:
                xy = list(xy_value) if isinstance(xy_value, (list, tuple)) else []
                # Convert XY to RGB for display
                rgb = self._xy_to_rgb(xy[0], xy[1], brightness) if len(xy) >= 2 else [255, 255, 255]
        except Exception:
            pass  # White-only bulbs don't support xy

        # Get hue and saturation safely (color bulbs only)
        hue = 0
        saturation = 0
        try:
            hue = light.hue
        except Exception:
            pass
        try:
            saturation = light.saturation
        except Exception:
            pass

        # Get color mode safely - determines if bulb is color-capable
        # Possible values: 'xy', 'ct' (color temp), 'hs' (hue/sat), or None for white-only
        color_mode = "none"  # Default for white-only bulbs
        try:
            color_mode = light.colormode or "none"
        except Exception:
            pass  # White-only bulbs don't have colormode

        # Get model info safely
        model = "Unknown"
        manufacturer = "Philips"
        try:
            model = light.modelid or "Unknown"
        except Exception:
            pass
        try:
            manufacturer = light.manufacturername or "Philips"
        except Exception:
            pass

        # Get reachable status safely
        reachable = True
        try:
            reachable = light.reachable
        except Exception:
            pass

        return HueLight(
            light_id=str(light.light_id),
            name=light.name,
            room="",  # Will be populated from groups
            model=model,
            manufacturer=manufacturer,
            on=light.on,
            brightness=brightness,
            brightness_percent=brightness_percent,
            color_mode=color_mode,
            color_temp=color_temp_mireds,
            color_temp_kelvin=color_temp,
            hue=hue,
            saturation=saturation,
            xy=xy,
            rgb=rgb,
            reachable=reachable,
            last_seen=datetime.now().isoformat(),
            energy_usage=None,  # Hue API doesn't provide energy data directly
        )

    def _create_group_from_bridge(self, group: Any) -> HueGroup:
        """Create HueGroup from phue Group object.
        
        Note: phue raises exceptions when accessing certain properties,
        so we wrap all accesses in try/except.
        """
        # Get light IDs safely
        light_ids = []
        try:
            light_ids = [str(lid) for lid in group.lights]
        except Exception:
            pass

        # Calculate group state from individual lights
        on = False
        total_brightness = 0
        reachable_count = 0

        for light_id in light_ids:
            if light_id in self.lights:
                light = self.lights[light_id]
                if light.on:
                    on = True
                    total_brightness += light.brightness
                if light.reachable:
                    reachable_count += 1

        avg_brightness = int(total_brightness / len(light_ids)) if light_ids else 0

        # Get group name safely
        name = "Unknown"
        try:
            name = group.name or "Unknown"
        except Exception:
            pass

        # Get group type safely - phue raises exception if not available
        group_type = "Room"
        try:
            group_type = group.type or "Room"
        except Exception:
            pass  # Default to "Room" if type property not accessible

        return HueGroup(
            group_id=str(group.group_id),
            name=name,
            type=group_type,
            lights=light_ids,
            on=on,
            brightness=avg_brightness,
            reachable_lights=reachable_count,
        )

    def _create_scene_from_bridge(self, scene: Any) -> HueScene:
        """Create HueScene from phue Scene object."""
        light_ids = [str(lid) for lid in scene.lights] if hasattr(scene, 'lights') else []

        return HueScene(
            scene_id=scene.scene_id,
            name=scene.name,
            group=getattr(scene, 'group', ''),
            lights=light_ids,
            active=False,  # Would need to check current state
        )

    async def get_all_lights(self) -> List[HueLight]:
        """Get all discovered lights (from cache, with auto-rescan if stale)."""
        if not self._initialized:
            await self.initialize()

        # Auto-rescan if cache looks stale (all lights off + not reachable = likely stale)
        if self.lights and all(not l.on and not l.reachable for l in self.lights.values()):
            logger.info("Cache appears stale (all lights off + unreachable), rescanning...")
            await self.rescan()

        return list(self.lights.values())

    async def get_light(self, light_id: str) -> Optional[HueLight]:
        """Get a specific light by ID (from cache, fast)."""
        if not self._initialized:
            await self.initialize()
        # Return from cache - don't do full discovery on every get
        return self.lights.get(light_id)

    def _get_light_by_id(self, light_id: int):
        """Get a light object by ID (phue doesn't have lights_by_id)."""
        for light in self._bridge.lights:
            if light.light_id == light_id:
                return light
        return None

    def _xy_to_rgb(self, x: float, y: float, brightness: int = 254) -> List[int]:
        """Convert CIE 1931 XY color space to RGB for Hue lights.
        
        Converts XY coordinates back to RGB for display purposes.
        Uses sRGB color space with D65 white point.
        """
        try:
            # Normalize brightness (0-254 to 0-1)
            brightness_norm = brightness / 254.0 if brightness > 0 else 1.0

            # Convert xy to XYZ (using Y as brightness)
            # We need to reconstruct Z from x, y, and Y
            # x = X / (X + Y + Z), y = Y / (X + Y + Z)
            # If we set Y = brightness_norm, we can solve for X and Z
            if y == 0:
                return [255, 255, 255]  # Avoid division by zero

            Y = brightness_norm
            X = (x / y) * Y
            Z = ((1 - x - y) / y) * Y

            # Convert XYZ to linear RGB (inverse of sRGB to XYZ matrix)
            r_linear = X * 3.2404542 + Y * -1.5371385 + Z * -0.4985314
            g_linear = X * -0.9692660 + Y * 1.8760108 + Z * 0.0415560
            b_linear = X * 0.0556434 + Y * -0.2040259 + Z * 1.0572252

            # Apply inverse gamma correction (sRGB)
            def inv_gamma_correct(val):
                if val > 0.0031308:
                    return 1.055 * (val ** (1.0 / 2.4)) - 0.055
                return 12.92 * val

            r_norm = max(0.0, min(1.0, inv_gamma_correct(r_linear)))
            g_norm = max(0.0, min(1.0, inv_gamma_correct(g_linear)))
            b_norm = max(0.0, min(1.0, inv_gamma_correct(b_linear)))

            # Convert to 0-255 RGB
            r = int(round(r_norm * 255))
            g = int(round(g_norm * 255))
            b = int(round(b_norm * 255))

            return [r, g, b]
        except Exception:
            logger.exception("Failed to convert XY to RGB")
            return [255, 255, 255]  # Default to white on error

    def _rgb_to_xy(self, r: int, g: int, b: int) -> List[float] | None:
        """Convert RGB (0-255) to CIE 1931 XY color space for Hue lights.
        
        Based on Philips Hue API specification for RGB to XY conversion.
        Uses sRGB color space with D65 white point.
        """
        try:
            # Normalize RGB values to 0-1
            r_norm = r / 255.0
            g_norm = g / 255.0
            b_norm = b / 255.0

            # Apply gamma correction (sRGB gamma)
            def gamma_correct(val):
                if val > 0.04045:
                    return ((val + 0.055) / 1.055) ** 2.4
                return val / 12.92

            r_gamma = gamma_correct(r_norm)
            g_gamma = gamma_correct(g_norm)
            b_gamma = gamma_correct(b_norm)

            # Convert to XYZ color space (sRGB to XYZ matrix, D65 white point)
            x = r_gamma * 0.4124564 + g_gamma * 0.3575761 + b_gamma * 0.1804375
            y = r_gamma * 0.2126729 + g_gamma * 0.7151522 + b_gamma * 0.0721750
            z = r_gamma * 0.0193339 + g_gamma * 0.1191920 + b_gamma * 0.9503041

            # Convert XYZ to xy (chromaticity coordinates)
            total = x + y + z
            if total == 0:
                return None

            x_xy = x / total
            y_xy = y / total

            # Hue lights use a specific color gamut (most use Gamut B)
            # Clamp to valid range for Hue lights (approximate)
            x_xy = max(0.0, min(1.0, x_xy))
            y_xy = max(0.0, min(1.0, y_xy))

            return [round(x_xy, 4), round(y_xy, 4)]
        except Exception:
            logger.exception("Failed to convert RGB to XY")
            return None

    def _get_group_by_id(self, group_id: int):
        """Get a group object by ID (phue doesn't have groups_by_id)."""
        for group in self._bridge.groups:
            if group.group_id == group_id:
                return group
        return None

    async def set_light_state(
        self,
        light_id: str,
        on: Optional[bool] = None,
        brightness: Optional[int] = None,
        brightness_percent: Optional[int] = None,
        color_temp: Optional[int] = None,
        hue: Optional[int] = None,
        saturation: Optional[int] = None,
        rgb: Optional[List[int]] = None,
    ) -> bool:
        """Set light state."""
        if not self._bridge:
            raise RuntimeError("Hue Bridge not connected")

        try:
            light = self._get_light_by_id(int(light_id))
            if not light:
                raise ValueError(f"Light {light_id} not found")

            # Set power state
            if on is not None:
                light.on = on

            # Set brightness (accept both 0-254 and 0-100)
            if brightness is not None:
                light.brightness = max(0, min(254, brightness))
            elif brightness_percent is not None:
                light.brightness = int((brightness_percent / 100) * 254)

            # Set color temperature (mireds)
            if color_temp is not None:
                light.colortemp_k = color_temp

            # Set hue and saturation
            if hue is not None:
                light.hue = hue
            if saturation is not None:
                light.saturation = saturation

            # Set RGB (convert to XY)
            if rgb and len(rgb) == 3:
                # Convert RGB to XY color space (CIE 1931)
                # This is the color space that Hue lights use
                xy = self._rgb_to_xy(rgb[0], rgb[1], rgb[2])
                if xy:
                    light.xy = xy
                    # Also set colormode to 'xy' for color bulbs
                    try:
                        light.colormode = 'xy'
                    except Exception:
                        pass  # Some lights may not support setting colormode

            # Update local cache instead of re-querying entire bridge
            # The phue library sends the command directly, we just update our cache
            if light_id in self.lights:
                if on is not None:
                    self.lights[light_id].on = on
                if brightness is not None:
                    self.lights[light_id].brightness = brightness
                    self.lights[light_id].brightness_percent = int((brightness / 254) * 100)
                elif brightness_percent is not None:
                    self.lights[light_id].brightness = int((brightness_percent / 100) * 254)
                    self.lights[light_id].brightness_percent = brightness_percent
                if hue is not None:
                    self.lights[light_id].hue = hue
                if saturation is not None:
                    self.lights[light_id].saturation = saturation
                if rgb and len(rgb) == 3:
                    self.lights[light_id].rgb = rgb
                    # Update XY coordinates in cache
                    xy = self._rgb_to_xy(rgb[0], rgb[1], rgb[2])
                    if xy:
                        self.lights[light_id].xy = xy
                        self.lights[light_id].color_mode = 'xy'

            return True

        except Exception:
            logger.exception(f"Failed to set light {light_id} state")
            raise

    async def get_all_groups(self) -> List[HueGroup]:
        """Get all groups/rooms (from cache, with auto-rescan if stale)."""
        if not self._initialized:
            await self.initialize()

        # Auto-rescan if cache looks stale (all groups off + 0 reachable = likely stale)
        if self.groups and all(not g.on and g.reachable_lights == 0 for g in self.groups.values()):
            logger.info("Cache appears stale (all groups off + 0 reachable), rescanning...")
            await self.rescan()

        return list(self.groups.values())

    async def get_all_scenes(self) -> List[HueScene]:
        """Get all discovered scenes (from cache)."""
        if not self._initialized:
            await self.initialize()
        # Use cached data - don't re-query bridge
        return list(self.scenes.values())

    async def rescan(self) -> Dict[str, int]:
        """Manually rescan all devices from bridge. Use when devices change."""
        if not self._bridge:
            raise RuntimeError("Hue Bridge not connected")

        await self._discover_devices()
        self._last_scan_time = datetime.now()

        return {
            "lights": len(self.lights),
            "groups": len(self.groups),
            "scenes": len(self.scenes),
            "scanned_at": self._last_scan_time.isoformat() if self._last_scan_time else None,
        }

    async def set_group_state(
        self,
        group_id: str,
        on: Optional[bool] = None,
        brightness: Optional[int] = None,
    ) -> bool:
        """Set group/room state."""
        if not self._bridge:
            raise RuntimeError("Hue Bridge not connected")

        try:
            group = self._get_group_by_id(int(group_id))
            if not group:
                raise ValueError(f"Group {group_id} not found")

            if on is not None:
                group.on = on

            if brightness is not None:
                brightness_val = max(0, min(254, brightness))
                group.brightness = brightness_val

            # Update local cache instead of re-querying entire bridge
            if group_id in self.groups:
                if on is not None:
                    self.groups[group_id].on = on
                if brightness is not None:
                    self.groups[group_id].brightness = brightness

            return True

        except Exception:
            logger.exception(f"Failed to set group {group_id} state")
            raise

    async def activate_scene(self, scene_id: str, group_id: Optional[str] = None) -> bool:
        """Activate a scene."""
        if not self._bridge:
            raise RuntimeError("Hue Bridge not connected")

        try:
            # Find scene by iterating through scenes
            scene = None
            for s in self._bridge.scenes:
                if s.scene_id == scene_id:
                    scene = s
                    break

            if not scene:
                raise ValueError(f"Scene {scene_id} not found")

            # Determine which group to use
            target_group_id = None
            if group_id:
                target_group_id = int(group_id)
            else:
                # Get scene's associated group
                scene_group = getattr(scene, 'group', None)
                if scene_group:
                    target_group_id = int(scene_group)
                # If scene has no group, find a group that contains the scene's lights
                elif hasattr(scene, 'lights') and scene.lights:
                    scene_light_ids = set(str(lid) for lid in scene.lights)
                    for grp in self._bridge.groups:
                        if grp.group_id != 0:  # Skip group 0 (all lights)
                            try:
                                group_light_ids = set(str(lid) for lid in grp.lights)
                            except Exception:
                                continue
                            if scene_light_ids.intersection(group_light_ids):
                                target_group_id = grp.group_id
                                break

            if target_group_id is None:
                raise ValueError(f"Could not determine group for scene {scene_id}")

            # Activate scene using the bridge's set_group method
            # The phue Group object's .scene property doesn't work for activation
            # Must use bridge.set_group(group_id, 'scene', scene_id)
            self._bridge.set_group(target_group_id, 'scene', scene_id)

            logger.info(f"Activated scene {scene_id} on group {target_group_id}")
            return True

        except Exception:
            logger.exception(f"Failed to activate scene {scene_id}")
            raise


# Global manager instance
hue_manager = HueManager()


# MCP Tools
@tool(
    category=ToolCategory.LIGHTING,
    description="Get status of all Philips Hue lights",
)
class GetHueLightsTool(BaseTool):
    """Get all Philips Hue lights."""

    async def run(self) -> Dict[str, Any]:
        """Get all lights."""
        lights = await hue_manager.get_all_lights()
        return {
            "lights": [light.model_dump() for light in lights],
            "count": len(lights),
        }


@tool(
    category=ToolCategory.LIGHTING,
    description="Control a Philips Hue light (on/off, brightness, color)",
)
class ControlHueLightTool(BaseTool):
    """Control a Philips Hue light."""

    light_id: str = Field(..., description="Light ID")
    on: Optional[bool] = Field(None, description="Turn light on/off")
    brightness_percent: Optional[int] = Field(None, description="Brightness (0-100)")
    color_temp_kelvin: Optional[int] = Field(None, description="Color temperature in Kelvin")

    async def run(self) -> Dict[str, Any]:
        """Control light."""
        success = await hue_manager.set_light_state(
            self.light_id,
            on=self.on,
            brightness_percent=self.brightness_percent,
            color_temp=self.color_temp_kelvin,
        )
        light = await hue_manager.get_light(self.light_id)
        return {
            "success": success,
            "light": light.model_dump() if light else None,
        }


@tool(
    category=ToolCategory.LIGHTING,
    description="Get all Philips Hue groups/rooms",
)
class GetHueGroupsTool(BaseTool):
    """Get all Hue groups/rooms."""

    async def run(self) -> Dict[str, Any]:
        """Get all groups."""
        groups = await hue_manager.get_all_groups()
        return {
            "groups": [group.model_dump() for group in groups],
            "count": len(groups),
        }


@tool(
    category=ToolCategory.LIGHTING,
    description="Control a Philips Hue group/room (all lights in room)",
)
class ControlHueGroupTool(BaseTool):
    """Control a Hue group/room."""

    group_id: str = Field(..., description="Group ID")
    on: Optional[bool] = Field(None, description="Turn all lights in group on/off")
    brightness: Optional[int] = Field(None, description="Brightness (0-254)")

    async def run(self) -> Dict[str, Any]:
        """Control group."""
        success = await hue_manager.set_group_state(
            self.group_id,
            on=self.on,
            brightness=self.brightness,
        )
        return {"success": success}

