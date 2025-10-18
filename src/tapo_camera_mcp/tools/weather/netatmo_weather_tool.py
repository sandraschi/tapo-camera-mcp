"""
Netatmo Weather Portmanteau Tool

Combines Netatmo weather operations:
- Get Netatmo stations
- Get Netatmo weather data
"""

import logging
import time
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from ...tools.base_tool import BaseTool, ToolCategory, tool

logger = logging.getLogger(__name__)


@tool("netatmo_weather")
class NetatmoWeatherTool(BaseTool):
    """Netatmo weather data tool.

    Provides unified Netatmo weather operations including station information
    and current weather data retrieval.

    Parameters:
        operation: Type of weather operation (stations, data).
        station_id: Station ID for data operation (optional).

    Returns:
        A dictionary containing the Netatmo weather result.
    """

    class Meta:
        name = "netatmo_weather"
        description = (
            "Unified Netatmo weather operations including station info and current weather data"
        )
        category = ToolCategory.WEATHER

        class Parameters(BaseModel):
            operation: str = Field(..., description="Weather operation: 'stations', 'data'")
            station_id: Optional[str] = Field(None, description="Station ID for data operation")

    async def _run(
        self,
        operation: str,
        station_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute Netatmo weather operation."""
        try:
            logger.info(f"Netatmo weather {operation} operation")

            if operation == "stations":
                return await self._get_stations()
            if operation == "data":
                return await self._get_weather_data(station_id)
            return {
                "success": False,
                "error": f"Invalid operation: {operation}. Must be 'stations' or 'data'",
                "timestamp": time.time(),
            }

        except Exception as e:
            logger.error(f"Netatmo weather {operation} operation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "operation": operation,
                "timestamp": time.time(),
            }

    async def _get_stations(self) -> Dict[str, Any]:
        """Get Netatmo weather stations."""
        # Simulate Netatmo stations data
        stations = [
            {
                "station_id": "netatmo_001",
                "name": "Indoor Station",
                "location": "Living Room",
                "type": "indoor",
                "modules": [
                    {
                        "module_id": "module_001",
                        "name": "Main Module",
                        "type": "indoor",
                        "battery_level": 100,
                        "signal_strength": 95,
                    },
                    {
                        "module_id": "module_002",
                        "name": "Outdoor Module",
                        "type": "outdoor",
                        "battery_level": 78,
                        "signal_strength": 88,
                    },
                ],
                "last_update": time.time() - 60,
            },
            {
                "station_id": "netatmo_002",
                "name": "Bedroom Station",
                "location": "Bedroom",
                "type": "indoor",
                "modules": [
                    {
                        "module_id": "module_003",
                        "name": "Bedroom Module",
                        "type": "indoor",
                        "battery_level": 92,
                        "signal_strength": 90,
                    }
                ],
                "last_update": time.time() - 45,
            },
        ]

        total_modules = sum(len(station["modules"]) for station in stations)

        return {
            "success": True,
            "operation": "stations",
            "stations": stations,
            "total_stations": len(stations),
            "total_modules": total_modules,
            "message": f"Found {len(stations)} Netatmo stations with {total_modules} modules",
            "timestamp": time.time(),
        }

    async def _get_weather_data(self, station_id: Optional[str]) -> Dict[str, Any]:
        """Get Netatmo weather data."""
        # Simulate weather data
        import secrets

        weather_data = {
            "station_id": station_id or "netatmo_001",
            "timestamp": time.time(),
            "indoor": {
                "temperature": round(22.5 + secrets.randbelow(50) / 10, 1),
                "humidity": round(45 + secrets.randbelow(20), 1),
                "co2": round(450 + secrets.randbelow(200), 1),
                "noise": round(35 + secrets.randbelow(20), 1),
                "pressure": round(1013 + secrets.randbelow(40) - 20, 1),
                "health_index": "Good",
            },
            "outdoor": {
                "temperature": round(18.2 + secrets.randbelow(80) / 10, 1),
                "humidity": round(65 + secrets.randbelow(25), 1),
                "wind_speed": round(secrets.randbelow(20), 1),
                "wind_direction": secrets.randbelow(360),
                "rain": round(secrets.randbelow(10), 1),
                "uv_index": secrets.randbelow(12),
            },
            "forecast": {
                "today": {
                    "high": 25.0,
                    "low": 15.0,
                    "condition": "Partly Cloudy",
                    "rain_probability": 20,
                },
                "tomorrow": {
                    "high": 27.0,
                    "low": 17.0,
                    "condition": "Sunny",
                    "rain_probability": 5,
                },
            },
        }

        return {
            "success": True,
            "operation": "data",
            "weather_data": weather_data,
            "message": f"Weather data retrieved for station {weather_data['station_id']}",
            "timestamp": time.time(),
        }
