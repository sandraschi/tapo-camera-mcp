"""
Netatmo Weather Station Integration Client

Uses pyatmo 8.x async API to fetch real weather data from Netatmo stations.
Falls back to simulated data if not configured or on error.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import aiohttp

from ..config import get_model
from ..config.models import WeatherSettings
from ..db import TimeSeriesDB
from ..utils import get_logger

logger = get_logger(__name__)


# Check if pyatmo is available
try:
    import pyatmo
    from pyatmo.auth import AbstractAsyncAuth
    from pyatmo.exceptions import ApiError as PyatmoApiError

    PYATMO_AVAILABLE = True
except ImportError:
    PYATMO_AVAILABLE = False
    AbstractAsyncAuth = object  # type: ignore[misc,assignment]
    PyatmoApiError = Exception  # type: ignore[misc,assignment]


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
        token_update_callback=None,
    ):
        super().__init__(websession)
        self._client_id = client_id
        self._client_secret = client_secret
        self._refresh_token = refresh_token
        self._access_token: str | None = None
        self._token_expiry: float = 0
        self._token_update_callback = token_update_callback  # Callback to save token updates

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

        try:
            async with self.websession.post(url, data=data) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    error_msg = f"Token refresh failed: {resp.status} - {error_text}"
                    logger.error(f"Netatmo OAuth token refresh failed: {error_msg}")

                    # Check for specific error types
                    if "invalid" in error_text.lower() or "invalid_token" in error_text.lower():
                        raise RuntimeError(f"Invalid refresh token. Please re-authenticate with Netatmo. Error: {error_text}")
                    if "expired" in error_text.lower():
                        raise RuntimeError(f"Refresh token expired. Please re-authenticate with Netatmo. Error: {error_text}")
                    if resp.status == 401:
                        raise RuntimeError(f"Authentication failed (401). Invalid credentials or token. Error: {error_text}")
                    if resp.status == 403:
                        raise RuntimeError(f"Access forbidden (403). Check API permissions. Error: {error_text}")
                    raise RuntimeError(error_msg)

                try:
                    tokens = await resp.json()
                except Exception as json_error:
                    error_text = await resp.text()
                    error_msg = f"Failed to parse token response as JSON: {json_error}. Response: {error_text}"
                    logger.error(f"Netatmo token response parsing failed: {error_msg}")
                    raise RuntimeError(error_msg) from json_error

                # Check if access_token is present in response
                if "access_token" not in tokens:
                    error_msg = f"Access token not found in response. Response keys: {list(tokens.keys())}"
                    logger.error(f"Netatmo token response missing access_token: {error_msg}")
                    # Check for error in response
                    if "error" in tokens:
                        error_desc = tokens.get("error_description", tokens.get("error", "Unknown error"))
                        raise RuntimeError(f"Netatmo API error: {error_desc}. Full response: {tokens}")
                    raise RuntimeError(f"Access token not found in Netatmo response: {error_msg}")

                self._access_token = tokens["access_token"]
                self._token_expiry = time.time() + tokens.get("expires_in", 10800)

                # Update refresh token if a new one was issued
                if "refresh_token" in tokens:
                    new_refresh_token = tokens["refresh_token"]
                    self._refresh_token = new_refresh_token
                    # Call callback to save token if provided
                    if self._token_update_callback:
                        try:
                            self._token_update_callback(new_refresh_token)
                        except Exception as e:
                            logger.warning(f"Failed to save refresh token via callback: {e}")
                    logger.info("Netatmo refresh token updated")

                logger.debug("Netatmo access token refreshed successfully")
                return self._access_token
        except RuntimeError:
            # Re-raise RuntimeError as-is (already has proper error message)
            raise
        except aiohttp.ClientError as e:
            error_msg = f"Network error refreshing Netatmo token: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
        except KeyError as e:
            error_msg = f"Missing required field in Netatmo token response: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected error refreshing Netatmo token: {e}"
            logger.exception(error_msg)
            raise RuntimeError(error_msg) from e


class NetatmoService:
    """Netatmo weather station service with real API calls via pyatmo 8.x."""

    def __init__(self, token_file: str = "netatmo_token.cache") -> None:
        self.config = get_netatmo_config()
        self._initialized = False
        self._account: Any = None  # pyatmo.AsyncAccount
        self._session: aiohttp.ClientSession | None = None
        self._db = TimeSeriesDB()
        self._use_real_api = False
        # Token cache file for persisting refresh token updates
        self.token_file = self._adjust_token_path(token_file)
        # Load refresh token from cache if available (overrides config)
        self._load_token_cache()

    @staticmethod
    def _adjust_token_path(token_file: str) -> Path:
        """Adjust token file path for Docker vs native environments."""
        import os
        token_path = Path(token_file)
        # In Docker, store tokens in /app/tokens (mounted volume)
        # In native, store in project root
        if os.getenv("CONTAINER") == "yes" or Path("/.dockerenv").exists():
            tokens_dir = Path("/app/tokens")
            tokens_dir.mkdir(parents=True, exist_ok=True)
            return tokens_dir / token_path.name
        return Path.cwd() / token_path.name

    def _load_token_cache(self) -> None:
        """Load refresh token from cache file if it exists (overrides config)."""
        if self.token_file.exists():
            try:
                with open(self.token_file) as f:
                    cached_token = f.read().strip()
                    if cached_token:
                        logger.info(f"Loaded Netatmo refresh token from cache: {self.token_file}")
                        self.config.refresh_token = cached_token
            except Exception as e:
                logger.warning(f"Failed to load Netatmo token cache: {e}")

    def _save_token_cache(self, refresh_token: str) -> None:
        """Save refresh token to cache file for persistence across restarts."""
        try:
            self.token_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.token_file, "w") as f:
                f.write(refresh_token)
            logger.info(f"Saved Netatmo refresh token to cache: {self.token_file}")
        except Exception as e:
            logger.error(f"Failed to save Netatmo token cache: {e}")

    async def initialize(self) -> None:
        """Initialize Netatmo client if enabled and credentials provided."""
        import asyncio

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
            # Create aiohttp session with IPv4-only connector to fix Windows DNS issues
            # Windows async DNS can fail with IPv6/IPv4 conflicts - force IPv4
            import socket

            from aiohttp import TCPConnector
            from aiohttp.resolver import DefaultResolver

            # Custom resolver that uses sync socket.getaddrinfo (works on Windows)
            class SyncDNSResolver(DefaultResolver):
                """Resolver that uses sync socket.getaddrinfo to bypass Windows async DNS bug."""
                async def resolve(self, host, port=0, family=socket.AF_INET):
                    loop = asyncio.get_event_loop()
                    # Use sync getaddrinfo in thread pool (works on Windows when async fails)
                    addrinfo = await loop.run_in_executor(
                        None,
                        socket.getaddrinfo,
                        host, port, family, socket.SOCK_STREAM
                    )
                    return [{'hostname': host, 'host': addr[4][0], 'port': port, 'family': family, 'proto': 0, 'flags': 0}
                           for addr in addrinfo]

            # Force IPv4 + sync DNS resolver to avoid Windows async DNS issues
            connector = TCPConnector(
                family=socket.AF_INET,  # Force IPv4 only
                resolver=SyncDNSResolver(),  # Use sync DNS resolver
                limit=10,
                limit_per_host=5,
            )
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                connector=connector
            )

            # Create auth handler with callback to save token updates
            auth = NetatmoOAuth2Auth(
                websession=self._session,
                client_id=self.config.client_id,
                client_secret=self.config.client_secret,
                refresh_token=self.config.refresh_token,
                token_update_callback=self._save_token_cache,
            )

            # Create account and fetch initial data with timeout
            self._account = pyatmo.AsyncAccount(auth)
            import asyncio
            await asyncio.wait_for(self._account.async_update_weather_stations(), timeout=10.0)

            self._use_real_api = True
            logger.info(
                f"Netatmo initialized: {len(self._account.homes)} homes, weather stations loaded"
            )

        except asyncio.TimeoutError:
            logger.error("Netatmo initialization timed out - async_update_weather_stations took too long")
            if self._session:
                try:
                    await self._session.close()
                except Exception:
                    pass
                self._session = None
            self._account = None
            self._use_real_api = False
        except RuntimeError as e:
            # OAuth token refresh errors
            error_msg = str(e)
            if "Token refresh failed" in error_msg:
                logger.error(f"Netatmo authentication failed during initialization: {error_msg}")
            else:
                logger.error(f"Netatmo runtime error during initialization: {e}")
            if self._session:
                try:
                    await self._session.close()
                except Exception:
                    pass
                self._session = None
            self._account = None
            self._use_real_api = False
        except AttributeError as e:
            # pyatmo API changes or missing attributes
            logger.error(f"Netatmo API attribute error during initialization (pyatmo version mismatch?): {e}")
            if self._session:
                try:
                    await self._session.close()
                except Exception:
                    pass
                self._session = None
            self._account = None
            self._use_real_api = False
        except KeyError as e:
            # Missing expected data in pyatmo response
            logger.error(f"Netatmo API data structure error during initialization: {e}")
            if self._session:
                try:
                    await self._session.close()
                except Exception:
                    pass
                self._session = None
            self._account = None
            self._use_real_api = False
        except aiohttp.ClientError as e:
            # Network/HTTP errors
            error_msg = str(e)
            error_type = type(e).__name__
            if "getaddrinfo" in error_msg or "ClientConnectorDNSError" in error_type:
                logger.error(f"Netatmo DNS error during initialization: {error_type}: {error_msg}")
                logger.error("This indicates a network/DNS configuration issue, not just async DNS bug")
            else:
                logger.error(f"Netatmo network error during initialization: {error_type}: {error_msg}")
            if self._session:
                try:
                    await self._session.close()
                except Exception:
                    pass
                self._session = None
            self._account = None
            self._use_real_api = False
        except Exception as e:
            error_type = type(e).__name__
            error_msg = str(e)
            # Log the actual error for debugging
            logger.error(f"Failed to initialize Netatmo: {error_type}: {error_msg}")

            # Check if it's a DNS error - should already be using sync resolver, but log it
            if "getaddrinfo" in error_msg or "ClientConnectorDNSError" in error_type or "DNS" in error_type:
                logger.error(f"Netatmo DNS error persists even with sync DNS resolver: {error_type}: {error_msg}")
                logger.error("This indicates a network/DNS configuration issue, not just async DNS bug")
            # Check for pyatmo-specific exceptions
            elif "pyatmo" in error_type.lower() or "netatmo" in error_type.lower():
                logger.error(f"Netatmo/pyatmo exception during initialization: {error_type}: {error_msg}")
            else:
                logger.exception(f"Unexpected error during Netatmo initialization: {error_type}: {error_msg}")

            # Clean up and return - no simulated data
            if self._session:
                try:
                    await self._session.close()
                except Exception:
                    pass
                self._session = None
            self._account = None
            self._use_real_api = False

    async def close(self) -> None:
        """Clean up resources."""
        if self._session:
            await self._session.close()
            self._session = None

    async def list_stations(self) -> list[dict[str, Any]]:
        """Return list of weather stations with basic info."""
        await self.initialize()

        if self._use_real_api and self._account:
            # Helper function to process stations after successful API call
            def _process_stations():
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
                return stations

            try:
                # Force token refresh before API call to ensure we have a valid token
                if hasattr(self._account, 'auth') and hasattr(self._account.auth, 'async_get_access_token'):
                    try:
                        await self._account.auth.async_get_access_token()
                    except RuntimeError as token_error:
                        error_msg = str(token_error)
                        if "Invalid refresh token" in error_msg or "expired" in error_msg.lower():
                            logger.error("Netatmo refresh token is invalid or expired. Please re-authenticate.")
                            logger.error("Run: python scripts/netatmo_oauth_helper.py auth-url <client_id> <redirect_uri>")
                            return []
                        raise

                # Refresh data with timeout to prevent hanging
                await asyncio.wait_for(
                    self._account.async_update_weather_stations(),
                    timeout=10.0
                )

                # Process stations after successful API call
                stations = _process_stations()
                if stations:
                    return stations

            except asyncio.TimeoutError:
                logger.warning("Netatmo list_stations: async_update_weather_stations timed out")
            except PyatmoApiError as e:
                # Handle pyatmo API errors (403 Invalid access token, etc.)
                error_msg = str(e)
                if "403" in error_msg or "Invalid access token" in error_msg:
                    logger.warning("Netatmo access token invalid (403). Attempting token refresh...")
                    # Try to force token refresh and retry once
                    try:
                        if hasattr(self._account, 'auth') and hasattr(self._account.auth, 'async_get_access_token'):
                            # Clear cached token AND expiry to force refresh
                            if hasattr(self._account.auth, '_access_token'):
                                self._account.auth._access_token = None
                            if hasattr(self._account.auth, '_token_expiry'):
                                self._account.auth._token_expiry = 0  # Force expiry check to fail
                            # Force token refresh
                            await self._account.auth.async_get_access_token()
                            logger.info("Netatmo access token refreshed, retrying API call...")
                            # Retry the API call
                            await asyncio.wait_for(
                                self._account.async_update_weather_stations(),
                                timeout=10.0
                            )
                            # If retry succeeds, process stations
                            logger.info("Netatmo token refreshed successfully, processing stations")
                            stations = _process_stations()
                            if stations:
                                return stations
                        else:
                            raise RuntimeError("Cannot refresh token - auth object missing")
                    except (RuntimeError, PyatmoApiError) as refresh_error:
                        refresh_msg = str(refresh_error)
                        if "Invalid refresh token" in refresh_msg or "expired" in refresh_msg.lower():
                            logger.error("Netatmo refresh token is invalid or expired. Please re-authenticate.")
                            logger.error("Run: python scripts/netatmo_oauth_helper.py auth-url <client_id> <redirect_uri>")
                            return []
                        logger.error(f"Netatmo token refresh failed: {refresh_error}")
                        return []
                else:
                    logger.error(f"Netatmo API error: {error_msg}")
                    return []
            except RuntimeError as e:
                # OAuth token refresh errors
                error_msg = str(e)
                if "Token refresh failed" in error_msg or "Invalid refresh token" in error_msg:
                    logger.error(f"Netatmo authentication failed: {error_msg}")
                    logger.error("Please re-authenticate: python scripts/netatmo_oauth_helper.py auth-url <client_id> <redirect_uri>")
                    return []
                logger.exception(f"Netatmo runtime error in list_stations: {e}")
            except AttributeError as e:
                # pyatmo API changes or missing attributes
                logger.error(f"Netatmo API attribute error (pyatmo version mismatch?): {e}")
            except KeyError as e:
                # Missing expected data in pyatmo response
                logger.error(f"Netatmo API data structure error: {e}")
            except aiohttp.ClientError as e:
                # Network/HTTP errors
                logger.error(f"Netatmo network error in list_stations: {e}")
            except Exception as e:
                error_type = type(e).__name__
                error_msg = str(e)
                # Check for pyatmo-specific exceptions
                if "pyatmo" in error_type.lower() or "netatmo" in error_type.lower():
                    logger.error(f"Netatmo/pyatmo exception in list_stations: {error_type}: {error_msg}")
                else:
                    logger.exception(f"Unexpected error fetching Netatmo stations: {error_type}: {error_msg}")

        # NO simulated data - return empty list
        logger.warning("Netatmo API unavailable - returning empty list (no simulated data)")
        return []

    async def current_data(self, station_id: str, module_type: str) -> tuple[dict[str, Any], float]:
        """Return current weather data and timestamp."""
        await self.initialize()

        if self._use_real_api and self._account:
            try:
                # Add timeout to prevent hanging on DNS errors
                import asyncio
                try:
                    await asyncio.wait_for(self._account.async_update_weather_stations(), timeout=10.0)
                except asyncio.TimeoutError:
                    logger.warning("Netatmo data update timed out in current_data")
                    # Return empty data instead of raising
                    return {}, time.time()
                except RuntimeError as e:
                    # OAuth token refresh errors
                    error_msg = str(e)
                    if "Token refresh failed" in error_msg:
                        logger.error(f"Netatmo authentication failed in current_data: {error_msg}")
                    else:
                        logger.error(f"Netatmo runtime error in current_data: {e}")
                    return {}, time.time()
                except AttributeError as e:
                    # pyatmo API changes or missing attributes
                    logger.error(f"Netatmo API attribute error in current_data (pyatmo version mismatch?): {e}")
                    return {}, time.time()
                except KeyError as e:
                    # Missing expected data in pyatmo response
                    logger.error(f"Netatmo API data structure error in current_data: {e}")
                    return {}, time.time()
                except PyatmoApiError as e:
                    # Handle pyatmo API errors (403 Invalid access token, etc.)
                    error_msg = str(e)
                    if "403" in error_msg or "Invalid access token" in error_msg:
                        logger.warning("Netatmo access token invalid (403) in current_data. Attempting token refresh...")
                        # Try to force token refresh and retry once
                        try:
                            if hasattr(self._account, 'auth') and hasattr(self._account.auth, 'async_get_access_token'):
                                # Clear cached token AND expiry to force refresh
                                if hasattr(self._account.auth, '_access_token'):
                                    self._account.auth._access_token = None
                                if hasattr(self._account.auth, '_token_expiry'):
                                    self._account.auth._token_expiry = 0  # Force expiry check to fail
                                # Force token refresh
                                await self._account.auth.async_get_access_token()
                                logger.info("Netatmo access token refreshed in current_data, retrying API call...")
                                # Retry the API call
                                await asyncio.wait_for(
                                    self._account.async_update_weather_stations(),
                                    timeout=10.0
                                )
                                logger.info("Netatmo token refreshed successfully in current_data, continuing...")
                                # Continue processing - don't return empty data yet
                            else:
                                logger.error("Cannot refresh token in current_data - auth object missing")
                                return {}, time.time()
                        except (RuntimeError, PyatmoApiError) as refresh_error:
                            refresh_msg = str(refresh_error)
                            if "Invalid refresh token" in refresh_msg or "expired" in refresh_msg.lower():
                                logger.error("Netatmo refresh token is invalid or expired in current_data. Please re-authenticate.")
                            else:
                                logger.error(f"Netatmo token refresh failed in current_data: {refresh_error}")
                            return {}, time.time()
                    else:
                        logger.error(f"Netatmo API error in current_data: {error_msg}")
                        return {}, time.time()
                except aiohttp.ClientError as e:
                    # Network/HTTP errors
                    error_msg = str(e)
                    if "getaddrinfo" in error_msg or "ClientConnectorDNSError" in type(e).__name__:
                        logger.warning(f"Netatmo DNS error in current_data: {e}")
                    else:
                        logger.error(f"Netatmo network error in current_data: {e}")
                    return {}, time.time()
                except Exception as e:
                    error_type = type(e).__name__
                    error_msg = str(e)
                    # Check for DNS errors
                    if "getaddrinfo" in error_msg or "ClientConnectorDNSError" in error_type or "DNS" in error_type:
                        logger.warning(f"Netatmo DNS error in current_data: {error_type}: {error_msg}")
                    # Check for pyatmo-specific exceptions
                    elif "pyatmo" in error_type.lower() or "netatmo" in error_type.lower():
                        logger.error(f"Netatmo/pyatmo exception in current_data: {error_type}: {error_msg}")
                    else:
                        logger.error(f"Unexpected error in current_data: {error_type}: {error_msg}")
                    return {}, time.time()

                data = {}
                timestamp = time.time()

                # Find the station by station_id first
                target_home = None
                target_station_module = None

                for home_id, home in self._account.homes.items():
                    for mod_id, module in home.modules.items():
                        # Check if this is the station we're looking for
                        if mod_id == station_id and "NAMain" in str(getattr(module, "device_type", "")):
                            target_home = home
                            target_station_module = module
                            break
                    if target_station_module:
                        break

                if not target_station_module or not target_home:
                    logger.warning(f"Station {station_id} not found in Netatmo account")
                    return {}, time.time()

                # Now process modules from the correct station/home
                for mod_id, module in target_home.modules.items():
                    # Main indoor module (NAMain) - this is the station itself
                    if mod_id == station_id and "NAMain" in str(getattr(module, "device_type", "")):
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

                    # Outdoor module (NAModule1) - belongs to this station
                    elif "NAModule1" in str(getattr(module, "device_type", "")) and module_type in ("outdoor", "all"):
                        outdoor = {
                            "temperature": getattr(module, "temperature", None),
                            "humidity": getattr(module, "humidity", None),
                            "temp_trend": getattr(module, "temp_trend", "stable"),
                        }
                        if module_type == "all":
                            data["outdoor"] = outdoor
                        else:
                            data = outdoor

                    # Additional indoor modules (NAModule4) - e.g., Bathroom - belongs to this station
                    elif "NAModule4" in str(getattr(module, "device_type", "")) and module_type in ("indoor_extra", "all"):
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
                logger.warning(f"No data found for station {station_id} with module_type {module_type}")
                return {}, time.time()

            except Exception as e:
                # This catch-all should not be reached due to specific handlers above,
                # but kept as safety net
                error_type = type(e).__name__
                error_msg = str(e)
                # Check for DNS errors
                if "getaddrinfo" in error_msg or "ClientConnectorDNSError" in error_type or "DNS" in error_type:
                    logger.warning(f"Netatmo DNS error in current_data (catch-all): {error_type} - returning empty data")
                elif "TimeoutError" in error_type or "asyncio.TimeoutError" in error_type:
                    logger.warning("Netatmo data update timed out (catch-all) - returning empty data")
                elif "pyatmo" in error_type.lower() or "netatmo" in error_type.lower():
                    logger.error(f"Netatmo/pyatmo exception in current_data (catch-all): {error_type}: {error_msg}")
                else:
                    logger.exception(f"Unexpected error fetching Netatmo data (catch-all): {error_type}: {error_msg}")

        # NO simulated data - return empty dict
        logger.warning(f"Netatmo API unavailable - returning empty data for {station_id} (no simulated data)")
        return {}, time.time()

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
        """Return empty list - NO simulated data in production."""
        logger.warning("Netatmo API unavailable - returning empty list (no simulated data)")
        return []

    def _get_simulated_data(
        self, station_id: str, module_type: str
    ) -> tuple[dict[str, Any], float]:
        """Return empty data - NO simulated data in production."""
        logger.warning(f"Netatmo API unavailable for {station_id} - returning empty data (no simulated data)")
        # Return empty dict - no fake data
        return {}, time.time()
