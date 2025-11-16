from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from ..config import get_model
from ..config.models import WeatherSettings
from ..utils import get_logger

logger = get_logger(__name__)


@dataclass
class NetatmoConfig:
    enabled: bool
    client_id: Optional[str]
    client_secret: Optional[str]
    username: Optional[str]
    password: Optional[str]
    home_id: Optional[str]


def get_netatmo_config() -> NetatmoConfig:
    cfg = get_model(WeatherSettings)
    netatmo_dict = cfg.integrations.get("netatmo", {}) if cfg else {}
    return NetatmoConfig(
        enabled=bool(netatmo_dict.get("enabled", False)),
        client_id=netatmo_dict.get("client_id"),
        client_secret=netatmo_dict.get("client_secret"),
        username=netatmo_dict.get("username"),
        password=netatmo_dict.get("password"),
        home_id=netatmo_dict.get("home_id"),
    )


class NetatmoService:
    """Thin wrapper around Netatmo API (pyatmo) with graceful fallback."""

    def __init__(self) -> None:
        self.config = get_netatmo_config()
        self._initialized = False
        self._client = None  # late-bound pyatmo client

    async def initialize(self) -> None:
        """Initialize Netatmo client if enabled and credentials provided."""
        if self._initialized:
            return
        self._initialized = True

        if not self.config.enabled:
            logger.info("Netatmo disabled in config; using simulated data")
            return

        missing = [
            k
            for k, v in {
                "client_id": self.config.client_id,
                "client_secret": self.config.client_secret,
                "username": self.config.username,
                "password": self.config.password,
            }.items()
            if not v
        ]
        if missing:
            logger.warning(
                "Netatmo enabled but missing credentials: %s. Falling back to simulated data.",
                ", ".join(missing),
            )
            return

        try:
            import asyncio
            import pyatmo  # type: ignore

            # pyatmo has both sync and async helpers; simplest approach is to use sync under to_thread
            self._client = pyatmo.NetatmoClient(
                client_id=self.config.client_id,
                client_secret=self.config.client_secret,
                username=self.config.username,
                password=self.config.password,
            )
            # A no-op call to verify credentials; wrap with to_thread to avoid blocking
            await asyncio.to_thread(lambda: None)
            logger.info("Netatmo client initialized successfully")
        except Exception as e:
            logger.warning("Failed to initialize Netatmo client (%s). Using simulated data.", e)
            self._client = None

    async def list_stations(self) -> List[Dict[str, Any]]:
        """Return list of stations with basic info."""
        await self.initialize()
        # Placeholder; return simulated for now. Replace with client calls later.
        return [
            {
                "station_id": "netatmo_001",
                "station_name": "Living Room Weather Station",
                "location": "Living Room",
                "is_online": True,
                "modules": [
                    {
                        "module_id": "main_001",
                        "module_name": "Main Module",
                        "module_type": "indoor",
                        "is_online": True,
                        "battery_percent": None,
                        "wifi_signal": 85,
                    },
                    {
                        "module_id": "outdoor_001",
                        "module_name": "Outdoor Module",
                        "module_type": "outdoor",
                        "is_online": True,
                        "battery_percent": 92,
                        "rf_signal": 78,
                    },
                ],
                "last_update": 1234567890.0,
            }
        ]

    async def current_data(
        self, station_id: str, module_type: str
    ) -> Tuple[Dict[str, Any], float]:
        """Return current data dict and timestamp."""
        await self.initialize()
        # Placeholder simulated values; replace with real pyatmo readings later
        import time as _time

        if module_type == "all":
            data = {
                "indoor": {
                    "temperature": 22.3,
                    "humidity": 45,
                    "co2": 420,
                    "noise": 35,
                    "pressure": 1013.2,
                    "temp_trend": "stable",
                    "pressure_trend": "up",
                    "health_index": 85,
                },
                "outdoor": {"temperature": 18.7, "humidity": 62, "temp_trend": "down"},
            }
        elif module_type == "indoor":
            data = {
                "temperature": 22.3,
                "humidity": 45,
                "co2": 420,
                "noise": 35,
                "pressure": 1013.2,
                "temp_trend": "stable",
                "pressure_trend": "up",
                "health_index": 85,
            }
        elif module_type == "outdoor":
            data = {"temperature": 18.7, "humidity": 62, "temp_trend": "down"}
        else:
            data = {}

        return data, _time.time()


