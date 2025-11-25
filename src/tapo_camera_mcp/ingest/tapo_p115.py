"""
Real ingestion adapter for TP-Link Tapo P115 smart plugs.

Uses the 'tapo' Python library (not python-kasa) for Tapo P115 plugs.
"""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

from ..config import get_config
from ..db import TimeSeriesDB

if TYPE_CHECKING:
    from tapo import ApiClient
else:
    try:
        from tapo import ApiClient
    except ImportError:  # pragma: no cover - tapo is optional
        ApiClient = None  # type: ignore[assignment,misc]

logger = logging.getLogger(__name__)


class IngestionUnavailableError(RuntimeError):
    """Raised when a real ingestion adapter cannot be used."""


class TapoP115IngestionService:
    """
    Communicates with Tapo P115 plugs via the 'tapo' Python library.

    The service looks for configuration in the main `config.yaml` under
    `energy.tapo_p115`. If no configuration is present it falls back to
    environment variables:

    - `TAPO_ACCOUNT_EMAIL`
    - `TAPO_ACCOUNT_PASSWORD`
    - `TAPO_P115_HOSTS` (comma separated list)
    """

    def __init__(self, config: dict | None = None):
        self._config = config or get_config().get("energy", {}).get("tapo_p115", {})
        self._account = self._config.get("account", {})
        self._devices_cfg = self._config.get("devices", [])
        self._discovery_cfg = self._config.get("discovery", {})
        self._db = TimeSeriesDB()  # Initialize database for time series storage
        self._hosts: list[str] = [
            device.get("host") for device in self._devices_cfg if device.get("host")
        ]

        env_hosts = os.getenv("TAPO_P115_HOSTS")
        if env_hosts:
            self._hosts.extend(host.strip() for host in env_hosts.split(",") if host.strip())

        self._hosts = list(dict.fromkeys(self._hosts))  # deduplicate while preserving order

        self._email = (
            self._account.get("email")
            or self._account.get("username")
            or os.getenv("TAPO_ACCOUNT_EMAIL")
            or os.getenv("TAPO_ACCOUNT_USERNAME")
        )
        self._password = self._account.get("password") or os.getenv("TAPO_ACCOUNT_PASSWORD")

        self._discovery_enabled = self._discovery_cfg.get("enabled", False)
        self._discovery_timeout = int(self._discovery_cfg.get("timeout", 4))
        self._metadata_by_host = {device.get("host"): device for device in self._devices_cfg}

        # Cache for ApiClient instance
        self._client: ApiClient | None = None
        self._client_lock = asyncio.Lock()

        if ApiClient is None:
            raise IngestionUnavailableError(
                "tapo library is not installed; install it to enable real Tapo P115 ingestion: pip install tapo"
            )

        if not self._email or not self._password:
            raise IngestionUnavailableError(
                "Tapo account credentials not configured. Provide email/password in config.yaml under "
                "`energy.tapo_p115.account` or set TAPO_ACCOUNT_EMAIL and TAPO_ACCOUNT_PASSWORD."
            )

        if not self._hosts and not self._discovery_enabled:
            raise IngestionUnavailableError(
                "No Tapo P115 hosts configured. Provide hosts in config.yaml under "
                "`energy.tapo_p115.devices` or set TAPO_P115_HOSTS."
            )

    async def _get_client(self) -> ApiClient:
        """Get or create ApiClient instance."""
        if self._client is None:
            async with self._client_lock:
                if self._client is None:
                    if not self._email or not self._password:
                        raise IngestionUnavailableError("Tapo credentials not configured")
                    self._client = ApiClient(self._email, self._password)
        return self._client

    async def discover_devices(self) -> list[dict[str, object]]:
        """
        Discover and fetch real-time statistics for configured Tapo P115 plugs.
        """
        discovered_host_data: list[dict[str, object]] = []
        hosts = list(self._hosts)

        # If no hosts configured and discovery enabled, we'd need to query Tapo API
        # For now, we require hosts to be configured
        if not hosts:
            logger.warning("No P115 hosts configured for discovery")
            return []

        results = await asyncio.gather(
            *(self._fetch_device_snapshot(host) for host in hosts),
            return_exceptions=True,
        )

        for result in results:
            if isinstance(result, Exception):
                logger.debug("Tapo P115 snapshot error: %s", result)
                continue
            if result:
                discovered_host_data.append(result)

        return discovered_host_data

    async def _fetch_device_snapshot(self, host: str) -> dict[str, object] | None:
        """
        Collect realtime metrics for a single plug using tapo library.
        """
        try:
            client = await self._get_client()
            plug = await client.p115(host)

            # Get device info
            device_info = await plug.get_device_info()
            device_name = getattr(
                device_info, "nickname", getattr(device_info, "name", f"P115 {host}")
            )
            model = getattr(device_info, "model", "P115")
            device_id_attr = getattr(device_info, "device_id", None)

            # Get power state
            try:
                # Use device_info.device_on instead of is_on() method
                device_info_for_state = await plug.get_device_info()
                power_state = bool(getattr(device_info_for_state, "device_on", False))
            except Exception:
                power_state = False

            # Get real-time current power (watts)
            current_power = 0.0
            voltage = 220.0  # Default to 220V for European mains (user specified)
            current = 0.0
            try:
                # Use get_current_power() method for real-time power reading
                power_data = await plug.get_current_power()
                # Try multiple attribute names for current power
                for attr in ["current_power", "power", "power_mw", "power_w"]:
                    val = getattr(power_data, attr, None)
                    if val is not None:
                        current_power = float(val)
                        # If power_mw, convert to watts
                        if attr == "power_mw":
                            current_power = current_power / 1000.0
                        break

                # Try to get voltage and current from power_data
                for attr in ["voltage", "voltage_v", "voltage_mv"]:
                    val = getattr(power_data, attr, None)
                    if val is not None:
                        voltage = float(val)
                        if attr == "voltage_mv":
                            voltage = voltage / 1000.0
                        break

                for attr in ["current", "current_a", "current_ma"]:
                    val = getattr(power_data, attr, None)
                    if val is not None:
                        current = float(val)
                        if attr == "current_ma":
                            current = current / 1000.0
                        break

                # Calculate current from power and voltage if not available
                if current == 0.0 and current_power > 0 and voltage > 0:
                    current = current_power / voltage

            except Exception as e:
                logger.debug(f"Real-time power not available for {host}: {e}")
                # Keep defaults (0W, 220V, 0A)

            # Get energy usage (daily/monthly totals)
            today_energy = 0.0
            month_energy = 0.0
            try:
                energy = await plug.get_energy_usage()
                # Energy values are in Wh (watt-hours), convert to kWh
                today_energy = float(getattr(energy, "today_energy", 0)) / 1000.0
                month_energy = float(getattr(energy, "month_energy", 0)) / 1000.0

                logger.debug(f"Energy data for {host}: power={current_power}W, voltage={voltage}V, current={current}A, today={today_energy}kWh")
            except Exception as e:
                logger.warning(f"Energy usage not available for {host}: {e}")

            metadata = self._metadata_by_host.get(host, {})
            device_id = metadata.get("device_id") or device_id_attr
            if not device_id:
                device_id = f"tapo_p115_{host.replace('.', '_')}"

            snapshot_data = {
                "host": host,
                "device_id": device_id,
                "name": metadata.get("name") or device_name,
                "location": metadata.get("location", "Unknown"),
                "device_model": model,
                "power_state": power_state,
                "current_power": current_power,
                "voltage": voltage,
                "current": current,
                "daily_energy": today_energy,
                "monthly_energy": month_energy,
                "last_seen": datetime.now(tz=timezone.utc).isoformat(),
            }

            # Store data point in database
            try:
                timestamp = datetime.now(tz=timezone.utc)
                self._db.store_energy_data(
                    device_id=device_id,
                    timestamp=timestamp,
                    power_w=current_power,
                    voltage_v=voltage,
                    current_a=current,
                    daily_energy_kwh=today_energy,
                    monthly_energy_kwh=month_energy,
                    power_state=power_state,
                )
            except Exception as db_exc:
                logger.warning(f"Failed to store energy data in database: {db_exc}")

            return snapshot_data
        except Exception as exc:
            logger.warning(f"Unable to query Tapo P115 at {host}: {exc}")
            return None

    async def control_device(self, host: str, *, turn_on: bool | None = None) -> None:
        """
        Toggle plug state using tapo library.
        """
        client = await self._get_client()
        plug = await client.p115(host)

        if turn_on is True:
            await plug.on()
        elif turn_on is False:
            await plug.off()

    async def fetch_usage_series(self, host: str, *, hours: int = 24) -> list[dict[str, object]]:
        """
        Build a lightweight time series using real readings. Tapo P115 only
        exposes day-level counters, so we provide the latest realtime snapshot
        and a synthetic series derived from daily totals.
        """
        snapshot = await self._fetch_device_snapshot(host)
        if not snapshot:
            return []

        now = datetime.now(tz=timezone.utc)
        hourly_energy = float(snapshot["daily_energy"])
        # Spread the daily energy across the elapsed hours.
        elapsed_hours = max(1, now.hour or 1)
        per_hour = hourly_energy / elapsed_hours if hourly_energy else 0.0

        series: list[dict[str, object]] = []
        for i in range(min(hours, elapsed_hours)):
            ts = now.replace(minute=0, second=0, microsecond=0) - timedelta(hours=i)
            series.append(
                {
                    "timestamp": ts.isoformat(),
                    "energy_kwh": per_hour,
                    "power_w": snapshot["current_power"],
                }
            )

        return list(reversed(series))
