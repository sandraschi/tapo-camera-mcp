"""
Energy API endpoints for Tapo P115 smart plugs and Wien Energie smart meters.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from ...config import get_config
from ...db import TimeSeriesDB
from ...ingest import IngestionUnavailableError, WienEnergieIngestionService
from ...tools.energy.tapo_plug_tools import tapo_plug_manager

router = APIRouter(prefix="/api/energy", tags=["energy"])

def get_energy_db() -> TimeSeriesDB:
    """Lazy initialization of energy database."""
    if not hasattr(get_energy_db, '_db'):
        get_energy_db._db = TimeSeriesDB()
    return get_energy_db._db


# Global smart meter service instance
_smart_meter_service: WienEnergieIngestionService | None = None


def get_smart_meter_service() -> WienEnergieIngestionService | None:
    """Get or create smart meter service instance."""
    global _smart_meter_service
    if _smart_meter_service is None:
        try:
            _smart_meter_service = WienEnergieIngestionService()
        except IngestionUnavailableError:
            return None
        except Exception:
            return None
    return _smart_meter_service


@router.get("/devices", summary="List all energy devices")
async def list_energy_devices() -> dict[str, Any]:
    """
    Return all energy monitoring devices (Tapo P115 plugs + Wien Energie smart meter).
    """
    devices = []

    # Get Tapo P115 devices with fresh API data
    try:
        tapo_devices = await tapo_plug_manager.get_all_devices()
        for device in tapo_devices:
            device_id = device.device_id
            host = tapo_plug_manager.get_device_host(device_id)

            # Get fresh data from Tapo API if we have credentials and host
            current_power = 0.0
            voltage = 0.0
            current = 0.0
            today_energy = 0.0
            month_energy = 0.0
            power_state = False

            if host:
                try:
                    # Get fresh data directly from Tapo API
                    account_email = config.get('energy', {}).get('tapo_p115', {}).get('account', {}).get('email')
                    account_password = config.get('energy', {}).get('tapo_p115', {}).get('account', {}).get('password')

                    if account_email and account_password:
                        import tapo
                        client = await tapo.ApiClient(account_email, account_password).p115(host)
                        device_info = await client.get_device_info()
                        energy_usage = await client.get_energy_usage()

                        # Get real-time current power (Tapo P115 DOES provide this!)
                        current_power_result = await client.get_current_power()
                        current_power = current_power_result.current_power if hasattr(current_power_result, 'current_power') else 0.0

                        # Get energy usage data
                        power_state = device_info.device_on if hasattr(device_info, 'device_on') else False
                        today_energy = energy_usage.today_energy if hasattr(energy_usage, 'today_energy') else 0
                        month_energy = energy_usage.month_energy if hasattr(energy_usage, 'month_energy') else 0

                        # Voltage and current are not provided by Tapo P115 API
                        voltage = 0.0
                        current = 0.0

                except Exception as e:
                    # If API call fails, use cached device data
                    current_power = device.current_power
                    voltage = device.voltage
                    current = device.current
                    today_energy = device.daily_energy
                    month_energy = device.monthly_energy
                    power_state = device.power_state

            devices.append({
                "device_id": device.device_id,
                "name": device.name,
                "location": device.location,
                "type": "tapo_p115",
                "device_model": device.device_model,
                "power_state": power_state,
                "current_power": current_power,  # Always 0.0 for Tapo P115 (not supported)
                "voltage": voltage,
                "current": current,
                "daily_energy": today_energy,
                "monthly_energy": month_energy,
                "daily_cost": device.daily_cost,
                "monthly_cost": device.monthly_cost,
                "last_seen": device.last_seen,
            })
    except Exception:
        # Continue even if Tapo devices fail
        pass

    # Get Wien Energie smart meter
    try:
        service = get_smart_meter_service()
        if service:
            meter_info = await service.discover_meter()
            reading = await service.fetch_current_reading()
            if meter_info and reading:
                tariff_info = await service.get_tariff_info()
                cost = service.calculate_energy_cost(reading.get("daily_energy_kwh", 0))

                devices.append({
                    "device_id": "wien_energie_smart_meter",
                    "name": "Wien Energie Smart Meter",
                    "location": "Main",
                    "type": "smart_meter",
                    "device_model": "Wiener Netze Smart Meter",
                    "power_state": reading.get("active_power_w", 0) > 0,
                    "current_power": reading.get("active_power_w", 0),
                    "voltage": reading.get("voltage_v", 230),
                    "current": reading.get("current_a", 0),
                    "daily_energy": reading.get("daily_energy_kwh", 0),
                    "monthly_energy": reading.get("total_energy_kwh", 0) / 30 if reading.get("total_energy_kwh") else 0,
                    "daily_cost": cost,
                    "monthly_cost": cost * 30,
                    "last_seen": reading.get("timestamp", datetime.now(timezone.utc).isoformat()),
                    "tariff": tariff_info,
                })
    except Exception:
        # Continue even if smart meter fails
        pass

    return {
        "devices": devices,
        "total_devices": len(devices),
        "smart_plugs": len([d for d in devices if d.get("type") == "tapo_p115"]),
        "smart_meters": len([d for d in devices if d.get("type") == "smart_meter"]),
    }


@router.get("/smart-meter/status", summary="Get Wien Energie smart meter status")
async def get_smart_meter_status() -> dict[str, Any]:
    """
    Get current status and readings from Wien Energie smart meter.
    """
    service = get_smart_meter_service()
    if not service:
        raise HTTPException(
            status_code=503,
            detail="Smart meter service not available. Check configuration and adapter connection."
        )

    try:
        meter_info = await service.discover_meter()
        if not meter_info:
            raise HTTPException(
                status_code=503,
                detail="Unable to discover smart meter. Check adapter connection and security key."
            )

        reading = await service.fetch_current_reading()
        if not reading:
            raise HTTPException(
                status_code=503,
                detail="Unable to fetch current reading from smart meter."
            )

        tariff_info = await service.get_tariff_info()

        return {
            "success": True,
            "meter": meter_info,
            "reading": reading,
            "tariff": tariff_info,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/smart-meter/current", summary="Get current smart meter reading")
async def get_smart_meter_current() -> dict[str, Any]:
    """
    Get real-time energy reading from Wien Energie smart meter.
    """
    service = get_smart_meter_service()
    if not service:
        raise HTTPException(
            status_code=503,
            detail="Smart meter service not available."
        )

    try:
        reading = await service.fetch_current_reading()
        if not reading:
            raise HTTPException(
                status_code=503,
                detail="Unable to fetch current reading."
            )

        return {
            "success": True,
            "data": reading,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/smart-meter/history", summary="Get smart meter history")
async def get_smart_meter_history(
    hours: int = Query(24, ge=1, le=168, description="Hours of history"),
    start_date: str | None = Query(None, description="Start date (ISO format)"),
    end_date: str | None = Query(None, description="End date (ISO format)"),
) -> dict[str, Any]:
    """
    Get historical energy consumption data from Wien Energie smart meter.
    """
    service = get_smart_meter_service()
    if not service:
        raise HTTPException(
            status_code=503,
            detail="Smart meter service not available."
        )

    try:
        if start_date and end_date:
            start = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            end = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
        else:
            end = datetime.now(timezone.utc)
            start = end - timedelta(hours=hours)

        history = await service.fetch_historical_data(start, end)

        return {
            "success": True,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "data_points": len(history),
            "history": history,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/smart-meter/cost", summary="Calculate energy cost")
async def calculate_smart_meter_cost(
    energy_kwh: float | None = Query(None, description="Energy in kWh"),
    time_range: str = Query("24h", description="Time range: 1h, 24h, 7d, 30d"),
) -> dict[str, Any]:
    """
    Calculate energy cost based on Wien Energie tariffs.
    """
    service = get_smart_meter_service()
    if not service:
        raise HTTPException(
            status_code=503,
            detail="Smart meter service not available."
        )

    try:
        tariff_info = await service.get_tariff_info()

        if energy_kwh is None:
            reading = await service.fetch_current_reading()
            if reading:
                if time_range == "1h":
                    energy_kwh = reading.get("active_power_w", 0) / 1000.0
                elif time_range == "24h":
                    energy_kwh = reading.get("daily_energy_kwh", 0)
                elif time_range == "7d":
                    energy_kwh = reading.get("daily_energy_kwh", 0) * 7
                elif time_range == "30d":
                    energy_kwh = reading.get("daily_energy_kwh", 0) * 30
                else:
                    energy_kwh = reading.get("daily_energy_kwh", 0)
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Unable to fetch current reading. Please provide energy_kwh parameter."
                )

        cost = service.calculate_energy_cost(energy_kwh)

        return {
            "success": True,
            "energy_kwh": energy_kwh,
            "time_range": time_range,
            "cost_eur": cost,
            "tariff": tariff_info,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/current-usage", summary="Get current energy usage")
async def get_current_usage() -> dict[str, Any]:
    """
    Get current energy usage across all devices.
    """
    devices = []
    total_power = 0.0
    total_daily_energy = 0.0
    total_daily_cost = 0.0

    # Get Tapo P115 devices
    try:
        tapo_devices = await tapo_plug_manager.get_all_devices()
        for device in tapo_devices:
            devices.append({
                "device_id": device.device_id,
                "name": device.name,
                "power": device.current_power,
                "daily_energy": device.daily_energy,
                "daily_cost": device.daily_cost,
            })
            total_power += device.current_power
            total_daily_energy += device.daily_energy
            total_daily_cost += device.daily_cost
    except Exception:
        pass

    # Get smart meter data
    try:
        service = get_smart_meter_service()
        if service:
            reading = await service.fetch_current_reading()
            if reading:
                daily_energy = reading.get("daily_energy_kwh", 0)
                cost = service.calculate_energy_cost(daily_energy)
                devices.append({
                    "device_id": "wien_energie_smart_meter",
                    "name": "Wien Energie Smart Meter",
                    "power": reading.get("active_power_w", 0),
                    "daily_energy": daily_energy,
                    "daily_cost": cost,
                })
                total_power += reading.get("active_power_w", 0)
                total_daily_energy += daily_energy
                total_daily_cost += cost
    except Exception:
        pass

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_power_w": total_power,
        "total_daily_energy_kwh": total_daily_energy,
        "total_daily_cost_eur": total_daily_cost,
        "devices": devices,
    }


@router.get("/usage-history", summary="Get energy usage history")
async def get_usage_history(
    period: str = Query("day", description="Period: day, week, month"),
) -> dict[str, Any]:
    """
    Get historical energy usage data.
    """
    end = datetime.now(timezone.utc)
    if period == "day":
        start = end - timedelta(days=1)
    elif period == "week":
        start = end - timedelta(days=7)
    elif period == "month":
        start = end - timedelta(days=30)
    else:
        start = end - timedelta(days=1)

    history = get_energy_db().get_energy_history(start_time=start, end_time=end)

    return {
        "period": period,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "history": history,
    }


@router.get("/stats", summary="Get energy statistics")
async def get_energy_stats() -> dict[str, Any]:
    """
    Get energy statistics summary.
    """
    try:
        devices = await tapo_plug_manager.get_all_devices()
        total_devices = len(devices)
        active_devices = sum(1 for d in devices if d.power_state)
        total_power = sum(d.current_power for d in devices)
        daily_cost = sum(d.daily_cost for d in devices)

        # Add smart meter if available
        service = get_smart_meter_service()
        if service:
            reading = await service.fetch_current_reading()
            if reading:
                total_devices += 1
                if reading.get("active_power_w", 0) > 0:
                    active_devices += 1
                total_power += reading.get("active_power_w", 0)
                daily_cost += service.calculate_energy_cost(reading.get("daily_energy_kwh", 0))

        return {
            "total_devices": total_devices,
            "active_devices": active_devices,
            "current_power": total_power,
            "daily_cost": daily_cost,
        }
    except Exception as e:
        return {
            "total_devices": 0,
            "active_devices": 0,
            "current_power": 0,
            "daily_cost": 0,
            "error": str(e),
        }


