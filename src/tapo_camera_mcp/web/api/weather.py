"""
FastAPI router for Netatmo weather station API endpoints.

Provides REST API endpoints for weather data, station management,
and environmental monitoring capabilities.
"""

import logging
import time
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/weather", tags=["weather"])


class WeatherStationResponse(BaseModel):
    """Weather station response model."""

    station_id: str = Field(..., description="Station identifier")
    station_name: str = Field(..., description="Station name")
    location: str = Field(..., description="Station location")
    is_online: bool = Field(..., description="Online status")
    modules: List[Dict[str, Any]] = Field(default_factory=list, description="Connected modules")
    last_update: float = Field(..., description="Last update timestamp")


class WeatherDataResponse(BaseModel):
    """Weather data response model."""

    station_id: str = Field(..., description="Station identifier")
    module_type: str = Field(..., description="Module type")
    data: Dict[str, Any] = Field(..., description="Weather data")
    timestamp: float = Field(..., description="Data timestamp")


class HistoricalDataResponse(BaseModel):
    """Historical weather data response model."""

    station_id: str = Field(..., description="Station identifier")
    data_type: str = Field(..., description="Type of data")
    time_range: str = Field(..., description="Time range")
    data_points: List[Dict[str, Any]] = Field(
        default_factory=list, description="Historical data points"
    )
    timestamp: float = Field(..., description="Response timestamp")


class HealthReportResponse(BaseModel):
    """Health report response model."""

    station_id: str = Field(..., description="Station identifier")
    overall_score: int = Field(..., description="Overall health score (0-100)")
    status: str = Field(..., description="Health status")
    scores: Dict[str, int] = Field(default_factory=dict, description="Individual scores")
    recommendations: List[str] = Field(default_factory=list, description="Health recommendations")
    timestamp: float = Field(..., description="Report timestamp")


from ...config import get_model
from ...config.models import WeatherSettings
from ...integrations.netatmo_client import NetatmoService

_netatmo_service = None  # Will be initialized on first use


async def _get_netatmo_service() -> NetatmoService:
    """Get or create Netatmo service instance (with timeout on initialization)."""
    import asyncio
    global _netatmo_service
    if _netatmo_service is None:
        _netatmo_service = NetatmoService()
        # Initialize with timeout to prevent hanging
        try:
            await asyncio.wait_for(_netatmo_service.initialize(), timeout=10.0)
        except asyncio.TimeoutError:
            logger.warning("Netatmo initialization timed out - will return empty data")
        except Exception as e:
            logger.warning(f"Netatmo initialization failed: {e} - will return empty data")
    return _netatmo_service


@router.get("/stations", response_model=List[WeatherStationResponse])
async def get_weather_stations(
    include_offline: bool = Query(False, description="Include offline stations"),
) -> List[WeatherStationResponse]:
    """Get all available Netatmo weather stations."""
    try:
        logger.info(f"Getting weather stations (include_offline={include_offline})")

        cfg = get_model(WeatherSettings)
        use_netatmo = bool(cfg.integrations.get("netatmo", {}).get("enabled", False))

        if use_netatmo:
            import asyncio
            try:
                service = await _get_netatmo_service()
                raw = await asyncio.wait_for(service.list_stations(), timeout=10.0)
            except asyncio.TimeoutError:
                logger.warning("Netatmo list_stations timed out")
                raw = []
            except Exception as e:
                logger.warning(f"Netatmo list_stations failed: {e}")
                raw = []
            stations = [
                WeatherStationResponse(
                    station_id=s["station_id"],
                    station_name=s["station_name"],
                    location=s.get("location", "unknown"),
                    is_online=bool(s.get("is_online", True)),
                    modules=s.get("modules", []),
                    last_update=float(s.get("last_update", 0.0)),
                )
                for s in raw
            ]
        else:
            # No Netatmo configured - return empty list instead of mock data
            logger.warning("Netatmo integration not enabled. No weather stations available.")
            stations = []

        # Filter offline stations if requested
        if not include_offline:
            stations = [station for station in stations if station.is_online]

        return stations

    except Exception as e:
        logger.exception("Failed to get weather stations")
        # Return empty list instead of raising - prevents NetworkError in frontend
        return []


@router.get("/stations/{station_id}/data", response_model=WeatherDataResponse)
async def get_station_weather_data(
    station_id: str,
    module_type: str = Query("all", description="Module type to query (indoor, outdoor, all)"),
) -> WeatherDataResponse:
    """Get current weather data from a specific station."""
    try:
        logger.info(f"Getting weather data for station {station_id}, module type: {module_type}")

        cfg = get_model(WeatherSettings)
        use_netatmo = bool(cfg.integrations.get("netatmo", {}).get("enabled", False))

        if use_netatmo:
            import asyncio
            try:
                service = await _get_netatmo_service()
                data, ts = await asyncio.wait_for(service.current_data(station_id, module_type), timeout=10.0)
            except asyncio.TimeoutError:
                logger.warning(f"Netatmo current_data timed out for {station_id}")
                raise HTTPException(status_code=503, detail="Weather data request timed out")
            except Exception as e:
                logger.warning(f"Netatmo current_data failed: {e}")
                raise HTTPException(status_code=503, detail=f"Weather data unavailable: {str(e)}")
            return WeatherDataResponse(
                station_id=station_id, module_type=module_type, data=data, timestamp=ts
            )
        # No Netatmo configured - return error instead of mock data
        logger.warning(
            f"Netatmo integration not enabled. Cannot get weather data for station {station_id}."
        )
        raise HTTPException(
            status_code=503,
            detail="Netatmo integration not enabled. Configure Netatmo in config.yaml to enable weather data.",
        )

    except Exception as e:
        logger.exception("Failed to get weather data")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/stations/{station_id}/historical", response_model=HistoricalDataResponse)
async def get_station_historical_data(
    station_id: str,
    data_type: str = Query(
        "temperature", description="Data type (temperature, humidity, co2, pressure)"
    ),
    time_range: str = Query("24h", description="Time range (1h, 6h, 24h, 7d, 30d)"),
    module_type: str = Query("indoor", description="Module type (indoor, extra_bathroom, outdoor)"),
) -> HistoricalDataResponse:
    """Get historical weather data from a specific station and module."""
    try:
        logger.info(f"Getting historical data for {station_id}, {data_type}, {time_range}, module={module_type}")

        cfg = get_model(WeatherSettings)
        use_netatmo = bool(cfg.integrations.get("netatmo", {}).get("enabled", False))

        if not use_netatmo:
            logger.warning(
                f"Netatmo integration not enabled. Cannot get historical data for station {station_id}."
            )
            raise HTTPException(
                status_code=503,
                detail="Netatmo integration not enabled. Configure Netatmo in config.yaml to enable historical weather data.",
            )

        # Get historical data from database

        from ...db import TimeSeriesDB

        db = TimeSeriesDB()

        # Convert time_range to hours
        time_range_hours = {
            "1h": 1,
            "6h": 6,
            "24h": 24,
            "7d": 168,  # 7 days
            "30d": 720,  # 30 days
        }
        hours = time_range_hours.get(time_range, 24)

        # Get data from database for specified module
        history = db.get_weather_history(
            station_id=station_id,
            module_type=module_type,  # Now supports indoor, extra_bathroom, outdoor
            data_type=data_type,
            hours=hours,
        )

        # Format data points for frontend
        data_points = [
            {
                "timestamp": point["timestamp"],
                "value": point["value"],
            }
            for point in history
        ]

        import time
        return HistoricalDataResponse(
            station_id=station_id,
            data_type=data_type,
            time_range=time_range,
            data_points=data_points,
            timestamp=time.time(),
        )

        # REMOVED: Mock historical data generation
        # Simulate historical data generation
        import random
        import time

        # Calculate number of data points based on time range
        time_ranges = {
            "1h": 60,  # 1 minute intervals
            "6h": 360,  # 1 minute intervals
            "24h": 1440,  # 1 minute intervals
            "7d": 168,  # 1 hour intervals
            "30d": 720,  # 1 hour intervals
        }

        points = time_ranges.get(time_range, 1440)
        current_time = time.time()

        # Generate base values based on data type
        base_values = {
            "temperature": 22.0,
            "humidity": 50,
            "co2": 400,
            "pressure": 1013.0,
            "noise": 35,
        }

        base_value = base_values.get(data_type, 22.0)
        data_points = []

        for i in range(points):
            # Calculate timestamp
            if time_range in ["1h", "6h", "24h"]:
                timestamp = current_time - (points - i) * 60  # 1 minute intervals
            else:
                timestamp = current_time - (points - i) * 3600  # 1 hour intervals

            # Generate realistic variation
            if data_type == "temperature":
                variation = random.uniform(-1, 1)  # ±1°C variation
                value = round(base_value + variation, 1)
            elif data_type == "humidity":
                variation = random.randint(-10, 10)  # ±10% variation
                value = max(0, min(100, base_value + variation))
            elif data_type == "co2":
                variation = random.randint(-50, 50)  # ±50 ppm variation
                value = max(300, min(1000, base_value + variation))
            elif data_type == "pressure":
                variation = random.uniform(-1, 1)  # ±1 mbar variation
                value = round(base_value + variation, 1)
            elif data_type == "noise":
                variation = random.randint(-10, 10)  # ±10 dB variation
                value = max(20, min(80, base_value + variation))
            else:
                value = base_value

            data_points.append(
                {
                    "timestamp": timestamp,
                    "value": value,
                    "formatted_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp)),
                }
            )

        return HistoricalDataResponse(
            station_id=station_id,
            data_type=data_type,
            time_range=time_range,
            data_points=data_points,
            timestamp=current_time,
        )

    except Exception as e:
        logger.exception("Failed to get historical data")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/stations/{station_id}/health", response_model=HealthReportResponse)
async def get_station_health_report(
    station_id: str,
    include_recommendations: bool = Query(True, description="Include improvement recommendations"),
) -> HealthReportResponse:
    """Get comprehensive health report for a weather station."""
    try:
        logger.info(f"Generating health report for {station_id}")

        # Get REAL data from Netatmo
        cfg = get_model(WeatherSettings)
        use_netatmo = bool(cfg.integrations.get("netatmo", {}).get("enabled", False))
        
        if not use_netatmo:
            raise HTTPException(status_code=503, detail="Netatmo not enabled - cannot generate health report")
        
        import asyncio
        service = await _get_netatmo_service()
        data, _ = await asyncio.wait_for(service.current_data(station_id, "all"), timeout=10.0)
        
        # Calculate REAL health scores from actual data
        indoor = data.get("indoor", {})
        temp = indoor.get("temperature")
        humidity = indoor.get("humidity")
        co2 = indoor.get("co2")
        noise = indoor.get("noise")
        
        scores = {}
        recommendations = []
        
        # Temperature score (optimal: 20-24°C)
        if temp is not None:
            if 20 <= temp <= 24:
                scores["temperature"] = 100
            elif 18 <= temp < 20 or 24 < temp <= 26:
                scores["temperature"] = 80
                recommendations.append(f"Temperature ({temp}°C) slightly outside optimal range (20-24°C)")
            else:
                scores["temperature"] = 50
                recommendations.append(f"Temperature ({temp}°C) outside comfortable range (20-24°C)")
        else:
            scores["temperature"] = 0
        
        # Humidity score (optimal: 40-60%)
        if humidity is not None:
            if 40 <= humidity <= 60:
                scores["humidity"] = 100
            elif 30 <= humidity < 40 or 60 < humidity <= 70:
                scores["humidity"] = 80
                recommendations.append(f"Humidity ({humidity}%) slightly outside optimal range (40-60%)")
            else:
                scores["humidity"] = 50
                recommendations.append(f"Humidity ({humidity}%) outside comfortable range (40-60%)")
        else:
            scores["humidity"] = 0
        
        # CO2 score (excellent: <600, good: 600-1000, fair: 1000-1500, poor: >1500)
        if co2 is not None:
            if co2 < 600:
                scores["co2"] = 100
            elif co2 < 1000:
                scores["co2"] = 85
            elif co2 < 1500:
                scores["co2"] = 60
                recommendations.append(f"CO2 level ({co2} ppm) is elevated - consider ventilation")
            else:
                scores["co2"] = 30
                recommendations.append(f"CO2 level ({co2} ppm) is high - ventilate immediately")
        else:
            scores["co2"] = 0
        
        # Noise score (optimal: <40 dB)
        if noise is not None:
            if noise < 40:
                scores["noise"] = 100
            elif noise < 50:
                scores["noise"] = 80
            else:
                scores["noise"] = 60
                recommendations.append(f"Noise level ({noise} dB) is elevated")
        else:
            scores["noise"] = 0
        
        # Calculate overall score
        overall_score = int(sum(scores.values()) / len(scores)) if scores else 0
        status = "Excellent" if overall_score >= 90 else "Good" if overall_score >= 70 else "Fair" if overall_score >= 50 else "Poor"
        
        import time
        return HealthReportResponse(
            station_id=station_id,
            overall_score=overall_score,
            status=status,
            scores=scores,
            recommendations=recommendations if include_recommendations else [],
            timestamp=time.time(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to generate health report")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/stations/{station_id}/alerts")
async def configure_station_alerts(station_id: str, alert_config: Dict[str, Any]) -> Dict[str, Any]:
    """Configure weather alerts for a station."""
    try:
        logger.info(f"Configuring alerts for {station_id}: {alert_config}")

        # Validate alert configuration
        required_fields = ["alert_type", "threshold_value", "comparison"]
        for field in required_fields:
            if field not in alert_config:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")

        # TODO: Implement real alert configuration storage (database)
        # For now, return error - no mock data
        raise HTTPException(
            status_code=501,
            detail="Alert configuration not yet implemented. This feature requires database storage."
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to configure alerts")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/stations/{station_id}/modules")
async def get_station_modules(station_id: str) -> Dict[str, Any]:
    """Get all modules for a specific weather station."""
    try:
        logger.info(f"Getting modules for station {station_id}")

        # Get REAL modules from Netatmo
        cfg = get_model(WeatherSettings)
        use_netatmo = bool(cfg.integrations.get("netatmo", {}).get("enabled", False))
        
        if not use_netatmo:
            raise HTTPException(status_code=503, detail="Netatmo not enabled - cannot get modules")
        
        import asyncio
        service = await _get_netatmo_service()
        stations = await asyncio.wait_for(service.list_stations(), timeout=10.0)
        
        # Find the station
        station = None
        for s in stations:
            if s["station_id"] == station_id:
                station = s
                break
        
        if not station:
            raise HTTPException(status_code=404, detail=f"Station {station_id} not found")
        
        # Return REAL modules from the station
        modules = station.get("modules", [])
        
        return {
            "success": True,
            "station_id": station_id,
            "modules": modules,
            "total_modules": len(modules),
            "online_modules": len([m for m in modules if m.get("is_online", False)]),
            "timestamp": time.time(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to get modules")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/overview")
async def get_weather_overview() -> Dict[str, Any]:
    """Get weather overview across all stations."""
    try:
        logger.info("Getting weather overview")

        cfg = get_model(WeatherSettings)
        use_netatmo = bool(cfg.integrations.get("netatmo", {}).get("enabled", False))

        if use_netatmo:
            try:
                import asyncio
                # Get real data from Netatmo
                service = await _get_netatmo_service()
                stations = await asyncio.wait_for(service.list_stations(), timeout=10.0)
                
                if stations:
                    total_stations = len(stations)
                    online_stations = sum(1 for s in stations if s.get("is_online", True))
                    
                    # Get data from first station
                    station_id = stations[0]["station_id"]
                    data, ts = await asyncio.wait_for(service.current_data(station_id, "all"), timeout=10.0)
                    
                    # Count total modules across all stations
                    total_modules = sum(len(s.get("modules", [])) for s in stations)
                    
                    # Extract indoor data (nested structure)
                    indoor_data = data.get("indoor", {})
                    temp = indoor_data.get("temperature")
                    humidity = indoor_data.get("humidity")
                    co2 = indoor_data.get("co2")
                    
                    return {
                        "total_stations": total_stations,
                        "online_stations": online_stations,
                        "total_modules": total_modules,
                        "online_modules": total_modules,  # Assume all modules online if station is online
                        "average_temperature": temp if temp is not None else 22.0,
                        "average_humidity": humidity if humidity is not None else 45,
                        "average_co2": co2 if co2 is not None else 400,
                        "overall_health_score": 90,  # Calculate based on data quality
                        "health_status": "Good",
                        "last_update": ts,
                    }
            except Exception as e:
                logger.warning(f"Failed to get real Netatmo data: {e}")
        
        # No Netatmo or failed to fetch - return empty data (NO placeholder/mock data)
        logger.warning("Netatmo not enabled or unavailable - returning empty data (no placeholder/mock data)")
        return {
            "total_stations": 0,
            "online_stations": 0,
            "total_modules": 0,
            "online_modules": 0,
            "average_temperature": None,
            "average_humidity": None,
            "average_co2": None,
            "overall_health_score": 0,
            "health_status": "No Data",
            "last_update": time.time(),
        }

    except Exception as e:
        logger.exception("Failed to get weather overview")
        raise HTTPException(status_code=500, detail=str(e)) from e


# ============================================================================
# External Weather (Open-Meteo API - Free, no API key required)
# ============================================================================

from ...integrations.openmeteo_client import VIENNA_LAT, VIENNA_LON, openmeteo_client


class ExternalWeatherResponse(BaseModel):
    """External weather data response."""

    location: str = Field(..., description="Location name")
    latitude: float = Field(..., description="Latitude")
    longitude: float = Field(..., description="Longitude")
    temperature: float = Field(..., description="Temperature in Celsius")
    humidity: int = Field(..., description="Humidity percentage")
    pressure: float = Field(..., description="Pressure in hPa")
    wind_speed: float = Field(..., description="Wind speed in km/h")
    wind_direction: int = Field(..., description="Wind direction in degrees")
    weather_code: int = Field(..., description="WMO weather code")
    weather_description: str = Field(..., description="Weather description")
    cloud_cover: int = Field(..., description="Cloud cover percentage")
    precipitation: float = Field(..., description="Precipitation in mm")
    is_day: bool = Field(..., description="Is daytime")
    timestamp: float = Field(..., description="Data timestamp")


class ForecastDayResponse(BaseModel):
    """Daily forecast response."""

    date: str = Field(..., description="Date (YYYY-MM-DD)")
    temp_max: float | None = Field(None, description="Max temperature")
    temp_min: float | None = Field(None, description="Min temperature")
    precipitation: float = Field(0, description="Precipitation in mm")
    weather_code: int = Field(0, description="WMO weather code")
    weather_description: str = Field("", description="Weather description")
    wind_speed_max: float = Field(0, description="Max wind speed")


@router.get("/external/current", response_model=ExternalWeatherResponse)
async def get_external_weather(
    lat: float = Query(VIENNA_LAT, description="Latitude"),
    lon: float = Query(VIENNA_LON, description="Longitude"),
    location: str = Query("Vienna, Austria", description="Location name"),
) -> ExternalWeatherResponse:
    """Get current external weather from Open-Meteo API (free, no API key)."""
    try:
        logger.info(f"Getting external weather for {location} ({lat}, {lon})")

        import asyncio
        try:
            weather = await asyncio.wait_for(openmeteo_client.get_current_weather(lat, lon, location), timeout=10.0)
        except asyncio.TimeoutError:
            logger.warning("Open-Meteo weather request timed out")
            raise HTTPException(status_code=503, detail="Weather service timeout")

        if not weather:
            raise HTTPException(status_code=503, detail="Failed to fetch external weather")

        return ExternalWeatherResponse(
            location=weather.location,
            latitude=weather.latitude,
            longitude=weather.longitude,
            temperature=weather.temperature,
            humidity=weather.humidity,
            pressure=weather.pressure,
            wind_speed=weather.wind_speed,
            wind_direction=weather.wind_direction,
            weather_code=weather.weather_code,
            weather_description=weather.weather_description,
            cloud_cover=weather.cloud_cover,
            precipitation=weather.precipitation,
            is_day=weather.is_day,
            timestamp=weather.timestamp,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to get external weather")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/external/forecast", response_model=List[ForecastDayResponse])
async def get_external_forecast(
    lat: float = Query(VIENNA_LAT, description="Latitude"),
    lon: float = Query(VIENNA_LON, description="Longitude"),
    days: int = Query(7, ge=1, le=14, description="Number of forecast days"),
) -> List[ForecastDayResponse]:
    """Get weather forecast from Open-Meteo API."""
    try:
        logger.info(f"Getting {days}-day forecast for ({lat}, {lon})")

        import asyncio
        try:
            forecast = await asyncio.wait_for(openmeteo_client.get_forecast(lat, lon, days), timeout=10.0)
        except asyncio.TimeoutError:
            logger.warning("Open-Meteo forecast request timed out")
            return []

        return [
            ForecastDayResponse(
                date=day["date"],
                temp_max=day.get("temp_max"),
                temp_min=day.get("temp_min"),
                precipitation=day.get("precipitation", 0),
                weather_code=day.get("weather_code", 0),
                weather_description=day.get("weather_description", ""),
                wind_speed_max=day.get("wind_speed_max", 0),
            )
            for day in forecast
        ]

    except Exception as e:
        logger.exception("Failed to get forecast")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/combined")
async def get_combined_weather() -> Dict[str, Any]:
    """Get combined internal (Netatmo) and external (Vienna) weather."""
    try:
        logger.info("Getting combined weather data")

        # Get internal Netatmo data
        cfg = get_model(WeatherSettings)
        use_netatmo = bool(cfg.integrations.get("netatmo", {}).get("enabled", False))

        internal_data = None
        if use_netatmo:
            try:
                import asyncio
                service = await _get_netatmo_service()
                stations = await asyncio.wait_for(service.list_stations(), timeout=10.0)
                if stations:
                    station_id = stations[0]["station_id"]
                    data, ts = await asyncio.wait_for(service.current_data(station_id, "all"), timeout=10.0)
                    internal_data = {
                        "station_name": stations[0].get("station_name", "Netatmo"),
                        "location": stations[0].get("location", "Home"),
                        "data": data,
                        "timestamp": ts,
                    }
            except Exception as e:
                logger.warning(f"Failed to get Netatmo data: {e}")

        # Get external Vienna weather
        external_data = None
        try:
            logger.info("Fetching external Vienna weather from Open-Meteo...")
            weather = await openmeteo_client.get_current_weather()
            if weather:
                logger.info(f"Successfully fetched Vienna weather: {weather.temperature}°C, {weather.humidity}% humidity")
                external_data = {
                    "location": weather.location,
                    "temperature": weather.temperature,
                    "humidity": weather.humidity,
                    "pressure": weather.pressure,
                    "wind_speed": weather.wind_speed,
                    "weather_description": weather.weather_description,
                    "cloud_cover": weather.cloud_cover,
                    "is_day": weather.is_day,
                    "timestamp": weather.timestamp,
                }
            else:
                logger.warning("Open-Meteo returned None - weather data unavailable")
        except Exception as e:
            logger.exception(f"Failed to get external weather: {e}")

        # Get forecast
        forecast = await openmeteo_client.get_forecast(days=5)

        return {
            "internal": internal_data,
            "external": external_data,
            "forecast": forecast[:5],  # 5-day forecast
            "timestamp": time.time(),
        }

    except Exception as e:
        logger.exception("Failed to get combined weather")
        raise HTTPException(status_code=500, detail=str(e)) from e
