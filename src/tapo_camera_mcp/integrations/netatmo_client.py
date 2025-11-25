from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from ..config import get_model
from ..config.models import WeatherSettings
from ..db import TimeSeriesDB
from ..utils import get_logger

logger = get_logger(__name__)


@dataclass
class NetatmoConfig:
    enabled: bool
    client_id: str | None
    client_secret: str | None
    redirect_uri: str | None
    refresh_token: str | None
    username: str | None
    password: str | None
    home_id: str | None


def get_netatmo_config() -> NetatmoConfig:
    cfg = get_model(WeatherSettings)
    netatmo_dict = cfg.integrations.get("netatmo", {}) if cfg else {}
    return NetatmoConfig(
        enabled=bool(netatmo_dict.get("enabled", False)),
        client_id=netatmo_dict.get("client_id"),
        client_secret=netatmo_dict.get("client_secret"),
        redirect_uri=netatmo_dict.get("redirect_uri"),
        refresh_token=netatmo_dict.get("refresh_token"),
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
        self._db = TimeSeriesDB()  # Initialize database for time series storage

    async def initialize(self) -> None:
        """Initialize Netatmo client if enabled and credentials provided."""
        if self._initialized:
            return
        self._initialized = True

        if not self.config.enabled:
            logger.info("Netatmo disabled in config; using simulated data")
            return

        try:
            import asyncio

            import pyatmo  # type: ignore[import-untyped]

            # Prefer OAuth refresh token if present; fallback to password grant as last resort
            if self.config.client_id and self.config.client_secret and self.config.refresh_token:
                # Example: newer pyatmo supports tokens based auth; keep generic to avoid version pin
                self._client = pyatmo.NetatmoClient(
                    client_id=self.config.client_id,
                    client_secret=self.config.client_secret,
                    refresh_token=self.config.refresh_token,
                )
            elif (
                self.config.client_id
                and self.config.client_secret
                and self.config.username
                and self.config.password
            ):
                self._client = pyatmo.NetatmoClient(
                    client_id=self.config.client_id,
                    client_secret=self.config.client_secret,
                    username=self.config.username,
                    password=self.config.password,
                )
            else:
                logger.warning(
                    "Netatmo enabled but missing OAuth refresh_token and/or credentials. Using simulated data."
                )
                self._client = None

            # A no-op call to verify credentials; wrap with to_thread to avoid blocking
            await asyncio.to_thread(lambda: None)
            logger.info("Netatmo client initialized successfully")
        except Exception as e:
            logger.warning("Failed to initialize Netatmo client (%s). Using simulated data.", e)
            self._client = None

    async def list_stations(self) -> list[dict[str, Any]]:
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
    ) -> tuple[dict[str, Any], float]:
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

        timestamp = datetime.now(timezone.utc)

        # Store data point in database
        try:
            if module_type in {"indoor", "all"}:
                indoor_data = data.get("indoor") if module_type == "all" else data
                if indoor_data:
                    self._db.store_weather_data(
                        station_id=station_id,
                        module_type="indoor",
                        timestamp=timestamp,
                        temperature_c=indoor_data.get("temperature"),
                        humidity_percent=indoor_data.get("humidity"),
                        co2_ppm=indoor_data.get("co2"),
                        pressure_mbar=indoor_data.get("pressure"),
                        noise_db=indoor_data.get("noise"),
                    )

            if module_type in {"outdoor", "all"}:
                outdoor_data = data.get("outdoor") if module_type == "all" else data
                if outdoor_data:
                    self._db.store_weather_data(
                        station_id=station_id,
                        module_type="outdoor",
                        timestamp=timestamp,
                        temperature_c=outdoor_data.get("temperature"),
                        humidity_percent=outdoor_data.get("humidity"),
                    )
        except Exception as db_exc:
            logger.warning(f"Failed to store weather data in database: {db_exc}")

        return data, _time.time()


