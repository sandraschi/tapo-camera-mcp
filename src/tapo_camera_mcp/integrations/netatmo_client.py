"""
Netatmo Weather Station Integration Client

Uses pyatmo 8.x async API to fetch real weather data from Netatmo stations.
Falls back to simulated data if not configured or on error.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import aiohttp
from aiohttp import resolver

from ..config import get_model
from ..config.models import WeatherSettings
from ..db import TimeSeriesDB
from ..utils import get_logger

logger = get_logger(__name__)

# Check if pyatmo is available
try:
    import pyatmo
    from pyatmo.auth import AbstractAsyncAuth

    PYATMO_AVAILABLE = True
except ImportError:
    PYATMO_AVAILABLE = False
    AbstractAsyncAuth = object  # type: ignore[misc,assignment]


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


class NetatmoOAuth2Auth(AbstractAsyncAuth):
    """OAuth2 authentication handler for pyatmo 8.x using refresh token."""

    def __init__(
        self,
        websession: aiohttp.ClientSession,
        client_id: str,
        client_secret: str,
        refresh_token: str,
    ):
        super().__init__(websession)
        self._client_id = client_id
        self._client_secret = client_secret
        self._refresh_token = refresh_token
        self._access_token: str | None = None
        self._token_expiry: float = 0

    async def async_get_access_token(self) -> str:
        """Return a valid access token, refreshing if needed."""
        if self._access_token and time.time() < self._token_expiry - 60:
            return self._access_token

        # Refresh the token
        url = "https://api.netatmo.com/oauth2/token"
        data = {
            "grant_type": "refresh_token",
            "client_id": self._client_id,
            "client_secret": self._client_secret,
            "refresh_token": self._refresh_token,
        }

        async with self.websession.post(url, data=data) as resp:
            if resp.status != 200:
                error_text = await resp.text()
                raise RuntimeError(f"Token refresh failed: {resp.status} - {error_text}")

            tokens = await resp.json()
            self._access_token = tokens["access_token"]
            self._token_expiry = time.time() + tokens.get("expires_in", 10800)

            # Update refresh token if a new one was issued
            if "refresh_token" in tokens:
                self._refresh_token = tokens["refresh_token"]
                logger.info("Netatmo refresh token updated")

            logger.debug("Netatmo access token refreshed successfully")
            return self._access_token


class NetatmoService:
    """Netatmo weather station service with real API calls via pyatmo 8.x."""

    def __init__(self) -> None:
        self.config = get_netatmo_config()
        self._initialized = False
        self._account: Any = None  # pyatmo.AsyncAccount
        self._session: aiohttp.ClientSession | None = None
        self._db = TimeSeriesDB()
        self._use_real_api = False

    async def initialize(self) -> None:
        """Initialize Netatmo client if enabled and credentials provided."""
        if self._initialized:
            return
        self._initialized = True

        if not self.config.enabled:
            logger.info("Netatmo disabled in config; using simulated data")
            return

        if not PYATMO_AVAILABLE:
            logger.warning(
                "pyatmo not installed; using simulated data. Install with: pip install pyatmo"
            )
            return

        # Check for required credentials
        if not all(
            [
                self.config.client_id,
                self.config.client_secret,
                self.config.refresh_token,
            ]
        ):
            logger.warning(
                "Netatmo enabled but missing credentials (client_id, client_secret, refresh_token). "
                "Using simulated data."
            )
            return

        try:
            # Create aiohttp session with IPv4 preference and timeout
            # Force IPv4 to avoid IPv6 DNS resolution issues
            # Python's getaddrinfo can fail on Windows with IPv6/IPv4 conflicts
            import socket
            
            # Use system DNS resolver with IPv4 preference
            # This avoids aiodns which might not be installed or might have issues
            dns_resolver = resolver.DefaultResolver()
            family = socket.AF_INET  # Force IPv4 only
            connector = aiohttp.TCPConnector(
                family=family,
                limit=10,
                resolver=dns_resolver,
                use_dns_cache=True,
                ttl_dns_cache=300,
                enable_cleanup_closed=True
            )
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            self._session = aiohttp.ClientSession(connector=connector, timeout=timeout)

            # Create auth handler
            auth = NetatmoOAuth2Auth(
                websession=self._session,
                client_id=self.config.client_id,
                client_secret=self.config.client_secret,
                refresh_token=self.config.refresh_token,
            )

            # Create account and fetch initial data
            self._account = pyatmo.AsyncAccount(auth)
            await self._account.async_update_weather_stations()

            self._use_real_api = True
            logger.info(
                f"Netatmo initialized: {len(self._account.homes)} homes, weather stations loaded"
            )

        except Exception as e:
            error_type = type(e).__name__
            error_msg = str(e)
            # Log the actual error for debugging
            logger.error(f"Failed to initialize Netatmo: {error_type}: {error_msg}")
            
            # Check if it's a DNS error - if so, try to fix it
            if "getaddrinfo" in error_msg or "ClientConnectorDNSError" in error_type or "DNS" in error_type:
                logger.warning(f"Netatmo DNS error detected. Retrying with explicit IPv4 resolution...")
                # Try again with pre-resolved IP address
                try:
                    # Pre-resolve the IP address
                    import socket
                    addrinfo = socket.getaddrinfo('api.netatmo.com', 443, socket.AF_INET, socket.SOCK_STREAM)
                    if addrinfo:
                        ip_address = addrinfo[0][4][0]
                        logger.info(f"Resolved api.netatmo.com to {ip_address}, retrying connection...")
                        # Close old session
                        if self._session:
                            await self._session.close()
                        # Create new session with resolved IP (but we can't easily override pyatmo's URL)
                        # Instead, ensure our session config is correct
                        family = socket.AF_INET
                        dns_resolver = resolver.DefaultResolver()
                        connector = aiohttp.TCPConnector(
                            family=family,
                            resolver=dns_resolver,
                            use_dns_cache=True,
                            ttl_dns_cache=300
                        )
                        timeout = aiohttp.ClientTimeout(total=30, connect=10)
                        self._session = aiohttp.ClientSession(connector=connector, timeout=timeout)
                        auth = NetatmoOAuth2Auth(
                            websession=self._session,
                            client_id=self.config.client_id,
                            client_secret=self.config.client_secret,
                            refresh_token=self.config.refresh_token,
                        )
                        self._account = pyatmo.AsyncAccount(auth)
                        await self._account.async_update_weather_stations()
                        self._use_real_api = True
                        logger.info(f"Netatmo initialized successfully after retry: {len(self._account.homes)} homes")
                        return
                except Exception as retry_error:
                    logger.error(f"Retry also failed: {retry_error}")
            
            # If we get here, initialization failed
            logger.error(f"Netatmo initialization failed. Check network connectivity and credentials.")
            if self._session:
                try:
                    await self._session.close()
                except Exception:
                    pass
                self._session = None
            self._account = None
            self._use_real_api = False
            raise  # Re-raise the error so caller knows it failed

    async def close(self) -> None:
        """Clean up resources."""
        if self._session:
            await self._session.close()
            self._session = None

    async def list_stations(self) -> list[dict[str, Any]]:
        """Return list of weather stations with basic info."""
        await self.initialize()

        if self._use_real_api and self._account:
            try:
                # Refresh data
                await self._account.async_update_weather_stations()

                stations = []
                for home_id, home in self._account.homes.items():
                    # Find weather station modules in this home
                    for module_id, module in home.modules.items():
                        if hasattr(module, "device_type") and "NAMain" in str(module.device_type):
                            station = {
                                "station_id": module_id,
                                "station_name": getattr(module, "name", "Weather Station"),
                                "location": home.name if hasattr(home, "name") else home_id,
                                "is_online": getattr(module, "reachable", True),
                                "home_id": home_id,
                                "modules": [],
                                "last_update": getattr(module, "last_seen", time.time()),
                            }

                            # Add connected modules
                            for sub_id, sub_module in home.modules.items():
                                if sub_id != module_id:
                                    mod_info = {
                                        "module_id": sub_id,
                                        "module_name": getattr(sub_module, "name", sub_id),
                                        "module_type": self._get_module_type(sub_module),
                                        "is_online": getattr(sub_module, "reachable", True),
                                        "battery_percent": getattr(sub_module, "battery", None),
                                    }
                                    station["modules"].append(mod_info)

                            stations.append(station)

                if stations:
                    return stations

            except Exception:
                logger.exception("Error fetching Netatmo stations")

        # Fallback to simulated data
        return self._get_simulated_stations()

    async def current_data(self, station_id: str, module_type: str) -> tuple[dict[str, Any], float]:
        """Return current weather data and timestamp."""
        await self.initialize()

        if self._use_real_api and self._account:
            try:
                await self._account.async_update_weather_stations()

                data = {}
                timestamp = time.time()

                # Find the station and its modules
                for _home_id, home in self._account.homes.items():
                    for _mod_id, module in home.modules.items():
                        # Main indoor module (NAMain)
                        if "NAMain" in str(getattr(module, "device_type", "")):
                            if module_type in ("indoor", "all"):
                                indoor = {
                                    "temperature": getattr(module, "temperature", None),
                                    "humidity": getattr(module, "humidity", None),
                                    "co2": getattr(module, "co2", None),
                                    "noise": getattr(module, "noise", None),
                                    "pressure": getattr(module, "pressure", None),
                                    "temp_trend": getattr(module, "temp_trend", "stable"),
                                    "pressure_trend": getattr(module, "pressure_trend", "stable"),
                                }
                                if module_type == "all":
                                    data["indoor"] = indoor
                                else:
                                    data = indoor
                                timestamp = getattr(module, "last_seen", time.time())

                        # Outdoor module (NAModule1)
                        elif "NAModule1" in str(
                            getattr(module, "device_type", "")
                        ) and module_type in ("outdoor", "all"):
                            outdoor = {
                                "temperature": getattr(module, "temperature", None),
                                "humidity": getattr(module, "humidity", None),
                                "temp_trend": getattr(module, "temp_trend", "stable"),
                            }
                            if module_type == "all":
                                data["outdoor"] = outdoor
                            else:
                                data = outdoor

                        # Additional indoor modules (NAModule4) - e.g., Bathroom
                        elif "NAModule4" in str(
                            getattr(module, "device_type", "")
                        ) and module_type in ("indoor_extra", "all"):
                            module_name = getattr(module, "name", "Extra Indoor Module")
                            extra_indoor = {
                                "name": module_name,
                                "temperature": getattr(module, "temperature", None),
                                "humidity": getattr(module, "humidity", None),
                                "co2": getattr(module, "co2", None),
                                "temp_trend": getattr(module, "temp_trend", "stable"),
                                "battery_percent": getattr(module, "battery_percent", None),
                            }
                            if module_type == "all":
                                # Store additional modules in a list under "extra_indoor"
                                if "extra_indoor" not in data:
                                    data["extra_indoor"] = []
                                data["extra_indoor"].append(extra_indoor)
                            else:
                                data = extra_indoor

                if data:
                    self._store_data(station_id, module_type, data)
                    return data, timestamp

            except Exception:
                logger.exception("Error fetching Netatmo data")

        # Fallback to simulated data
        return self._get_simulated_data(station_id, module_type)

    def _get_module_type(self, module: Any) -> str:
        """Determine module type from device_type."""
        device_type = str(getattr(module, "device_type", ""))
        if "NAMain" in device_type:
            return "indoor"
        if "NAModule1" in device_type:
            return "outdoor"
        if "NAModule2" in device_type:
            return "wind"
        if "NAModule3" in device_type:
            return "rain"
        if "NAModule4" in device_type:
            return "indoor_extra"
        return "unknown"

    def _store_data(self, station_id: str, module_type: str, data: dict[str, Any]) -> None:
        """Store weather data in the database."""
        try:
            timestamp = datetime.now(timezone.utc)

            if module_type in ("indoor", "all"):
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

            if module_type in ("outdoor", "all"):
                outdoor_data = data.get("outdoor") if module_type == "all" else data
                if outdoor_data:
                    self._db.store_weather_data(
                        station_id=station_id,
                        module_type="outdoor",
                        timestamp=timestamp,
                        temperature_c=outdoor_data.get("temperature"),
                        humidity_percent=outdoor_data.get("humidity"),
                    )

            # Store extra indoor modules (e.g., Bathroom)
            if module_type == "all" and "extra_indoor" in data:
                for extra_module in data["extra_indoor"]:
                    module_name = extra_module.get("name", "unknown")
                    # Use module name as unique identifier (e.g., "Bathroom")
                    module_id = f"extra_{module_name.lower().replace(' ', '_')}"
                    self._db.store_weather_data(
                        station_id=station_id,
                        module_type=module_id,  # e.g., "extra_bathroom"
                        timestamp=timestamp,
                        temperature_c=extra_module.get("temperature"),
                        humidity_percent=extra_module.get("humidity"),
                        co2_ppm=extra_module.get("co2"),
                    )
        except Exception as e:
            logger.warning(f"Failed to store weather data: {e}")

    def _get_simulated_stations(self) -> list[dict[str, Any]]:
        """Return simulated station data for development/testing."""
        return [
            {
                "station_id": "netatmo_sim_001",
                "station_name": "Living Room Weather Station (Simulated)",
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
                "last_update": time.time(),
            }
        ]

    def _get_simulated_data(
        self, station_id: str, module_type: str
    ) -> tuple[dict[str, Any], float]:
        """Return simulated weather data for development/testing."""
        timestamp = time.time()

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
                "outdoor": {
                    "temperature": 18.7,
                    "humidity": 62,
                    "temp_trend": "down",
                },
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
            data = {
                "temperature": 18.7,
                "humidity": 62,
                "temp_trend": "down",
            }
        else:
            data = {}

        self._store_data(station_id, module_type, data)
        return data, timestamp
