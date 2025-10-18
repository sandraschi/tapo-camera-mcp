"""
Energy Management Portmanteau Tool

Combines energy monitoring and control operations:
- Get smart plug status
- Control smart plugs (on/off)
- Get energy consumption data
- Get energy cost analysis
"""

import logging
import time
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from ...tools.base_tool import BaseTool, ToolCategory, tool

logger = logging.getLogger(__name__)


@tool("energy_management")
class EnergyManagementTool(BaseTool):
    """Comprehensive energy management tool.

    Provides unified control for energy monitoring including smart plug status,
    control operations, consumption tracking, and cost analysis.

    Parameters:
        operation: Type of energy operation (status, control, consumption, cost).
        device_id: ID of the smart plug device (optional for status).
        action: Control action (on, off, toggle) for control operation.
        time_range: Time range for consumption/cost analysis (1h, 24h, 7d, 30d).

    Returns:
        A dictionary containing the energy operation result.
    """

    class Meta:
        name = "energy_management"
        description = "Unified energy management for smart plugs including status, control, consumption, and cost analysis"
        category = ToolCategory.ENERGY

        class Parameters(BaseModel):
            operation: str = Field(
                ..., description="Energy operation: 'status', 'control', 'consumption', 'cost'"
            )
            device_id: Optional[str] = Field(None, description="Smart plug device ID")
            action: Optional[str] = Field(None, description="Control action: 'on', 'off', 'toggle'")
            time_range: Optional[str] = Field(
                "24h", description="Time range for analysis: '1h', '24h', '7d', '30d'"
            )

    async def _run(
        self,
        operation: str,
        device_id: Optional[str] = None,
        action: Optional[str] = None,
        time_range: str = "24h",
    ) -> Dict[str, Any]:
        """Execute energy management operation."""
        try:
            logger.info(f"Energy {operation} operation")

            if operation == "status":
                return await self._get_status(device_id)
            if operation == "control":
                return await self._control_device(device_id, action)
            if operation == "consumption":
                return await self._get_consumption(time_range)
            if operation == "cost":
                return await self._get_cost_analysis(time_range)
            return {
                "success": False,
                "error": f"Invalid operation: {operation}. Must be 'status', 'control', 'consumption', or 'cost'",
                "timestamp": time.time(),
            }

        except Exception as e:
            logger.error(f"Energy {operation} operation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "operation": operation,
                "timestamp": time.time(),
            }

    async def _get_status(self, device_id: Optional[str]) -> Dict[str, Any]:
        """Get smart plug status."""
        # Simulate smart plug data
        devices = [
            {
                "device_id": "tapo_001",
                "name": "Living Room TV Plug",
                "location": "Living Room",
                "is_on": True,
                "power": 85.5,
                "voltage": 120.2,
                "current": 0.71,
                "daily_energy": 2.1,
                "monthly_energy": 63.0,
                "monthly_cost": 7.56,
            },
            {
                "device_id": "tapo_002",
                "name": "Kitchen Coffee Maker",
                "location": "Kitchen",
                "is_on": False,
                "power": 0.0,
                "voltage": 0.0,
                "current": 0.0,
                "daily_energy": 1.8,
                "monthly_energy": 54.0,
                "monthly_cost": 6.48,
            },
        ]

        if device_id:
            device = next((d for d in devices if d["device_id"] == device_id), None)
            if not device:
                return {
                    "success": False,
                    "error": f"Device {device_id} not found",
                    "timestamp": time.time(),
                }
            devices = [device]

        return {
            "success": True,
            "operation": "status",
            "devices": devices,
            "total_devices": len(devices),
            "online_devices": len([d for d in devices if d["is_on"]]),
            "message": f"Retrieved status for {len(devices)} device(s)",
            "timestamp": time.time(),
        }

    async def _control_device(
        self, device_id: Optional[str], action: Optional[str]
    ) -> Dict[str, Any]:
        """Control smart plug device."""
        if not device_id:
            return {
                "success": False,
                "error": "Device ID is required for control operation",
                "timestamp": time.time(),
            }

        if not action:
            return {
                "success": False,
                "error": "Action is required for control operation",
                "timestamp": time.time(),
            }

        valid_actions = ["on", "off", "toggle"]
        if action not in valid_actions:
            return {
                "success": False,
                "error": f"Invalid action: {action}. Must be one of: {valid_actions}",
                "timestamp": time.time(),
            }

        # Simulate device control
        import secrets

        new_state = action == "on" if action in ["on", "off"] else secrets.choice([True, False])

        return {
            "success": True,
            "operation": "control",
            "device_id": device_id,
            "action": action,
            "new_state": new_state,
            "message": f"Device {device_id} turned {'on' if new_state else 'off'}",
            "timestamp": time.time(),
        }

    async def _get_consumption(self, time_range: str) -> Dict[str, Any]:
        """Get energy consumption data."""
        # Simulate consumption data based on time range
        time_ranges = {
            "1h": {"points": 12, "interval": "5min", "total": 0.15},
            "24h": {"points": 24, "interval": "1h", "total": 18.5},
            "7d": {"points": 7, "interval": "1d", "total": 129.5},
            "30d": {"points": 30, "interval": "1d", "total": 555.0},
        }

        if time_range not in time_ranges:
            return {
                "success": False,
                "error": f"Invalid time range: {time_range}. Must be one of: {list(time_ranges.keys())}",
                "timestamp": time.time(),
            }

        range_info = time_ranges[time_range]

        # Generate consumption data points
        import secrets

        consumption_data = []
        base_consumption = range_info["total"] / range_info["points"]

        for i in range(range_info["points"]):
            variation = (secrets.randbelow(200) - 100) / 100  # ±100% variation
            consumption = max(0, base_consumption * (1 + variation))
            consumption_data.append(
                {
                    "timestamp": time.time() - (range_info["points"] - i) * 3600,
                    "consumption": round(consumption, 3),
                    "formatted_time": f"Point {i + 1}",
                }
            )

        return {
            "success": True,
            "operation": "consumption",
            "time_range": time_range,
            "total_consumption": range_info["total"],
            "data_points": len(consumption_data),
            "consumption_data": consumption_data,
            "message": f"Energy consumption for {time_range}: {range_info['total']} kWh",
            "timestamp": time.time(),
        }

    async def _get_cost_analysis(self, time_range: str) -> Dict[str, Any]:
        """Get energy cost analysis."""
        # Simulate cost analysis
        cost_rates = {
            "1h": {"rate": 0.12, "total_cost": 0.018},
            "24h": {"rate": 0.12, "total_cost": 2.22},
            "7d": {"rate": 0.12, "total_cost": 15.54},
            "30d": {"rate": 0.12, "total_cost": 66.60},
        }

        if time_range not in cost_rates:
            return {
                "success": False,
                "error": f"Invalid time range: {time_range}. Must be one of: {list(cost_rates.keys())}",
                "timestamp": time.time(),
            }

        cost_info = cost_rates[time_range]

        # Simulate cost breakdown by device
        devices_cost = [
            {"device": "Living Room TV Plug", "cost": cost_info["total_cost"] * 0.6},
            {"device": "Kitchen Coffee Maker", "cost": cost_info["total_cost"] * 0.4},
        ]

        return {
            "success": True,
            "operation": "cost",
            "time_range": time_range,
            "total_cost": cost_info["total_cost"],
            "rate_per_kwh": cost_info["rate"],
            "cost_by_device": devices_cost,
            "savings_potential": cost_info["total_cost"] * 0.15,  # 15% savings potential
            "message": f"Energy cost for {time_range}: ${cost_info['total_cost']:.2f}",
            "timestamp": time.time(),
        }
