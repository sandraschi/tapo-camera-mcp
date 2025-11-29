"""
Ring Doorbell and Alarm integration client.

Uses the ring_doorbell library for unofficial API access.
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


class RingAlarmMode(Enum):
    """Ring alarm modes."""

    DISARMED = "none"
    HOME = "some"
    AWAY = "all"


class RingDeviceType(Enum):
    """Ring device types."""

    DOORBELL = "doorbell"
    CAMERA = "camera"
    ALARM_BASE = "alarm_base"
    CONTACT_SENSOR = "contact_sensor"
    MOTION_SENSOR = "motion_sensor"
    KEYPAD = "keypad"
    RANGE_EXTENDER = "range_extender"
    OTHER = "other"


@dataclass
class RingDevice:
    """Ring device data."""

    id: str
    name: str
    device_type: RingDeviceType
    battery_level: Optional[int] = None
    is_online: bool = True
    last_activity: Optional[datetime] = None
    extra_data: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "device_type": self.device_type.value,
            "battery_level": self.battery_level,
            "is_online": self.is_online,
            "last_activity": (
                self.last_activity.isoformat() if self.last_activity else None
            ),
            **self.extra_data,
        }


@dataclass
class RingSensor:
    """Ring sensor state."""

    id: str
    name: str
    sensor_type: str  # contact, motion
    is_open: Optional[bool] = None  # For contact sensors
    motion_detected: bool = False  # For motion sensors
    battery_level: Optional[int] = None
    is_online: bool = True

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "sensor_type": self.sensor_type,
            "is_open": self.is_open,
            "motion_detected": self.motion_detected,
            "battery_level": self.battery_level,
            "is_online": self.is_online,
        }


@dataclass
class RingAlarmStatus:
    """Ring alarm status."""

    mode: RingAlarmMode
    is_armed: bool
    sensors: list[RingSensor] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "mode": self.mode.value,
            "mode_name": self.mode.name.lower(),
            "is_armed": self.is_armed,
            "sensors": [s.to_dict() for s in self.sensors],
            "last_updated": self.last_updated.isoformat(),
        }


class RingClient:
    """Ring doorbell and alarm client."""

    def __init__(
        self,
        email: str,
        password: Optional[str] = None,
        token_file: str = "ring_token.cache",
        cache_ttl: int = 60,
    ):
        self.email = email
        self.password = password
        self.token_file = Path(token_file)
        self.cache_ttl = cache_ttl

        self._ring = None
        self._auth = None
        self._cache: dict[str, Any] = {}
        self._cache_time: dict[str, datetime] = {}
        self._2fa_pending = False
        self._initialized = False

    async def initialize(self) -> bool:
        """Initialize Ring connection."""
        try:
            from ring_doorbell import Auth, Ring

            # Check for cached token
            if self.token_file.exists():
                logger.info("Loading Ring token from cache")
                token_data = json.loads(self.token_file.read_text())
                self._auth = Auth(
                    "TapoCameraMCP/1.0", token_data, self._token_updated
                )
                self._ring = Ring(self._auth)
                await asyncio.to_thread(self._ring.update_data)
                self._initialized = True
                logger.info("Ring initialized from cached token")
                return True

            # Need fresh authentication
            if not self.password:
                logger.error("Ring password required for initial authentication")
                return False

            logger.info("Authenticating with Ring...")
            self._auth = Auth("TapoCameraMCP/1.0", None, self._token_updated)

            try:
                await asyncio.to_thread(
                    self._auth.fetch_token, self.email, self.password
                )
            except Exception as e:
                error_str = str(type(e).__name__).lower() + " " + str(e).lower()
                if "2fa" in error_str or "verification" in error_str or "requires2fa" in error_str:
                    self._2fa_pending = True
                    logger.warning(
                        "Ring 2FA required - check your email/SMS for code"
                    )
                    return True  # Return True so client stays active for 2FA
                raise

            self._ring = Ring(self._auth)
            await asyncio.to_thread(self._ring.update_data)
            self._initialized = True
            logger.info("Ring initialized successfully")

        except ImportError:
            logger.warning("ring_doorbell library not installed")
            return False
        except Exception:
            logger.exception("Failed to initialize Ring")
            return False
        else:
            return True

    def _token_updated(self, token: dict):
        """Callback when token is updated."""
        self.token_file.write_text(json.dumps(token))
        logger.debug("Ring token updated and cached")

    async def submit_2fa_code(self, code: str) -> bool:
        """Submit 2FA verification code."""
        if not self._2fa_pending:
            logger.warning("No 2FA pending")
            return False

        try:
            await asyncio.to_thread(
                self._auth.fetch_token, self.email, self.password, code
            )
            self._2fa_pending = False

            from ring_doorbell import Ring

            self._ring = Ring(self._auth)
            await asyncio.to_thread(self._ring.update_data)
            self._initialized = True
            logger.info("Ring 2FA completed successfully")
        except Exception:
            logger.exception("Ring 2FA failed")
            return False
        else:
            return True

    @property
    def is_2fa_pending(self) -> bool:
        return self._2fa_pending

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    def _is_cache_valid(self, key: str) -> bool:
        if key not in self._cache_time:
            return False
        elapsed = (datetime.now() - self._cache_time[key]).total_seconds()
        return elapsed < self.cache_ttl

    async def _update_data(self):
        """Update Ring data from API."""
        if not self._initialized or not self._ring:
            return
        await asyncio.to_thread(self._ring.update_data)

    async def get_doorbells(self) -> list[RingDevice]:
        """Get all Ring doorbells."""
        if not self._initialized:
            return []

        cache_key = "doorbells"
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]

        try:
            await self._update_data()
            devices = []

            for doorbell in self._ring.video_devices():
                battery = (
                    doorbell.battery_life
                    if hasattr(doorbell, "battery_life")
                    else None
                )
                kind = (
                    doorbell.kind if hasattr(doorbell, "kind") else "unknown"
                )
                has_sub = (
                    doorbell.has_subscription
                    if hasattr(doorbell, "has_subscription")
                    else False
                )
                device = RingDevice(
                    id=str(doorbell.id),
                    name=doorbell.name,
                    device_type=RingDeviceType.DOORBELL,
                    battery_level=battery,
                    is_online=True,
                    extra_data={
                        "kind": kind,
                        "has_subscription": has_sub,
                    },
                )
                devices.append(device)

            self._cache[cache_key] = devices
            self._cache_time[cache_key] = datetime.now()
        except Exception:
            logger.exception("Failed to get Ring doorbells")
            return []
        else:
            return devices

    async def get_alarm_status(self) -> Optional[RingAlarmStatus]:
        """Get Ring alarm status."""
        if not self._initialized:
            return None

        cache_key = "alarm_status"
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]

        try:
            await self._update_data()

            # Get alarm from groups
            alarm_groups = (
                self._ring.groups() if hasattr(self._ring, "groups") else {}
            )

            mode = RingAlarmMode.DISARMED
            sensors = []

            # Try to get alarm mode from devices
            for _group_name, group_devices in alarm_groups.items():
                for device in group_devices:
                    if hasattr(device, "mode"):
                        mode_str = device.mode
                        if mode_str == "all":
                            mode = RingAlarmMode.AWAY
                        elif mode_str == "some":
                            mode = RingAlarmMode.HOME
                        else:
                            mode = RingAlarmMode.DISARMED
                        break

            # Get sensors
            all_devices = self._ring.devices()
            if "other" in all_devices:
                for device in all_devices["other"]:
                    device_type = (
                        str(device.kind).lower()
                        if hasattr(device, "kind")
                        else ""
                    )

                    if "contact" in device_type or "sensor" in device_type:
                        is_open = (
                            device.is_open
                            if hasattr(device, "is_open")
                            else None
                        )
                        motion = (
                            device.motion_detected
                            if hasattr(device, "motion_detected")
                            else False
                        )
                        battery = (
                            device.battery_life
                            if hasattr(device, "battery_life")
                            else None
                        )
                        sensor = RingSensor(
                            id=str(device.id),
                            name=device.name,
                            sensor_type=(
                                "contact" if "contact" in device_type else "motion"
                            ),
                            is_open=is_open,
                            motion_detected=motion,
                            battery_level=battery,
                            is_online=True,
                        )
                        sensors.append(sensor)

            status = RingAlarmStatus(
                mode=mode,
                is_armed=mode != RingAlarmMode.DISARMED,
                sensors=sensors,
            )

            self._cache[cache_key] = status
            self._cache_time[cache_key] = datetime.now()
        except Exception:
            logger.exception("Failed to get Ring alarm status")
            return None
        else:
            return status

    async def set_alarm_mode(self, mode: RingAlarmMode) -> bool:
        """Set Ring alarm mode."""
        if not self._initialized:
            return False

        try:
            # Clear cache
            self._cache.pop("alarm_status", None)

            # Find alarm device and set mode
            alarm_groups = (
                self._ring.groups() if hasattr(self._ring, "groups") else {}
            )

            for _group_name, group_devices in alarm_groups.items():
                for device in group_devices:
                    if hasattr(device, "set_mode"):
                        await asyncio.to_thread(device.set_mode, mode.value)
                        logger.info(f"Ring alarm mode set to {mode.name}")
                        return True

            logger.warning("No Ring alarm device found to set mode")
        except Exception:
            logger.exception("Failed to set Ring alarm mode")
            return False
        else:
            return False

    async def get_doorbell_snapshot(self, device_id: str) -> Optional[bytes]:
        """Get a snapshot from a Ring doorbell."""
        if not self._initialized:
            return None

        try:
            for doorbell in self._ring.video_devices():
                if str(doorbell.id) == device_id:
                    # Get last recording snapshot if available
                    if hasattr(doorbell, "recording_download"):
                        # This would get the last event snapshot
                        pass
                    return None
        except Exception:
            logger.exception("Failed to get Ring snapshot")
            return None
        else:
            return None

    async def get_recent_events(self, limit: int = 10) -> list[dict]:
        """Get recent Ring events (motion, ding, etc.)."""
        if not self._initialized:
            return []

        cache_key = f"events_{limit}"
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]

        try:
            events = []

            for doorbell in self._ring.video_devices():
                try:
                    # Use async history method
                    history = await doorbell.async_history(limit=limit)
                    for event in history:
                        event_data = {
                            "device_id": str(doorbell.id),
                            "device_name": doorbell.name,
                            "event_type": event.get("kind", "unknown"),
                            "timestamp": event.get("created_at"),
                            "answered": event.get("answered", False),
                            "recording_id": event.get("id"),
                            "duration": event.get("duration"),
                        }
                        # Try to get video URL for this event
                        try:
                            if event.get("id"):
                                url = await doorbell.async_recording_url(event["id"])
                                event_data["video_url"] = url
                        except Exception as url_err:
                            logger.debug("Could not get video URL: %s", url_err)
                        events.append(event_data)
                except Exception as e:
                    logger.warning(f"Failed to get history for {doorbell.name}: {e}")

            # Sort by timestamp
            events.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            events = events[:limit]

            self._cache[cache_key] = events
            self._cache_time[cache_key] = datetime.now()
        except Exception:
            logger.exception("Failed to get Ring events")
            return []
        else:
            return events

    async def get_summary(self) -> dict:
        """Get a summary of Ring status for dashboard."""
        doorbells = await self.get_doorbells()
        alarm_status = await self.get_alarm_status()
        events = await self.get_recent_events(limit=5)

        return {
            "initialized": self._initialized,
            "2fa_pending": self._2fa_pending,
            "doorbells": [d.to_dict() for d in doorbells],
            "doorbell_count": len(doorbells),
            "alarm": alarm_status.to_dict() if alarm_status else None,
            "recent_events": events,
            "last_event": events[0] if events else None,
        }


# Singleton instance
ring_client: Optional[RingClient] = None


def get_ring_client() -> Optional[RingClient]:
    """Get the Ring client singleton."""
    return ring_client


async def init_ring_client(
    email: str,
    password: Optional[str] = None,
    token_file: str = "ring_token.cache",
    cache_ttl: int = 60,
) -> RingClient:
    """Initialize the Ring client singleton."""
    global ring_client
    ring_client = RingClient(
        email=email,
        password=password,
        token_file=token_file,
        cache_ttl=cache_ttl,
    )
    await ring_client.initialize()
    return ring_client
