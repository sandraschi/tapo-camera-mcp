"""
Tapo Smart Plug Energy Monitoring Tools for Tapo Camera MCP

This module provides MCP tools for monitoring and controlling Tapo smart plugs
with energy consumption tracking, cost analysis, and smart automation.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from ...tools.base_tool import BaseTool

logger = logging.getLogger(__name__)


class TapoSmartPlug(BaseModel):
    """Tapo Smart Plug device data model."""
    
    device_id: str = Field(..., description="Unique device identifier")
    name: str = Field(..., description="Device name")
    location: str = Field(..., description="Device location")
    power_state: bool = Field(..., description="Current power state (on/off)")
    current_power: float = Field(..., description="Current power consumption in watts")
    daily_energy: float = Field(..., description="Daily energy consumption in kWh")
    monthly_energy: float = Field(..., description="Monthly energy consumption in kWh")
    daily_cost: float = Field(..., description="Daily cost in USD")
    monthly_cost: float = Field(..., description="Monthly cost in USD")
    last_seen: str = Field(..., description="Last communication timestamp")
    automation_enabled: bool = Field(default=False, description="Whether automation is enabled")
    energy_monitoring: bool = Field(default=True, description="Whether energy monitoring is enabled")


class EnergyUsageData(BaseModel):
    """Energy usage data point."""
    
    timestamp: str = Field(..., description="Timestamp of the data point")
    device_id: str = Field(..., description="Device identifier")
    power_consumption: float = Field(..., description="Power consumption in watts")
    energy_consumption: float = Field(..., description="Energy consumption in kWh")
    cost: float = Field(..., description="Estimated cost in USD")


class EnergyAutomation(BaseModel):
    """Energy automation rule."""
    
    rule_id: str = Field(..., description="Unique rule identifier")
    name: str = Field(..., description="Rule name")
    device_id: str = Field(..., description="Target device")
    condition: str = Field(..., description="Automation condition")
    action: str = Field(..., description="Action to take")
    enabled: bool = Field(default=True, description="Whether rule is enabled")


class TapoPlugManager:
    """Manager for Tapo smart plugs and energy monitoring."""
    
    def __init__(self):
        self.devices: Dict[str, TapoSmartPlug] = {}
        self.usage_history: List[EnergyUsageData] = []
        self.automation_rules: List[EnergyAutomation] = []
        self._initialized = False
        self._electricity_rate = 0.12  # USD per kWh (default rate)
    
    async def initialize(self, tapo_account: Dict[str, str]) -> bool:
        """Initialize connection to Tapo smart plugs."""
        try:
            logger.info("Initializing Tapo smart plug connection...")
            
            # Simulate device discovery
            await self._discover_devices()
            
            # Load historical data
            await self._load_historical_data()
            
            self._initialized = True
            logger.info("Tapo smart plug connection initialized successfully")
            return True
            
        except Exception as e:
            logger.exception("Failed to initialize Tapo smart plugs: %s", e)
            return False
    
    async def _discover_devices(self):
        """Discover Tapo smart plugs on the network."""
        # Simulate discovered devices
        sample_devices = [
            {
                "device_id": "tapo_plug_living_room_tv",
                "name": "Living Room TV",
                "location": "Living Room",
                "power_state": True,
                "current_power": 45.5,
                "daily_energy": 0.85,
                "monthly_energy": 25.5,
                "daily_cost": 0.10,
                "monthly_cost": 3.06,
                "last_seen": "2025-01-16T10:30:00Z",
                "automation_enabled": True,
                "energy_monitoring": True
            },
            {
                "device_id": "tapo_plug_kitchen_coffee",
                "name": "Kitchen Coffee Maker",
                "location": "Kitchen",
                "power_state": True,
                "current_power": 850.0,
                "daily_energy": 2.1,
                "monthly_energy": 63.0,
                "daily_cost": 0.25,
                "monthly_cost": 7.56,
                "last_seen": "2025-01-16T10:30:00Z",
                "automation_enabled": True,
                "energy_monitoring": True
            },
            {
                "device_id": "tapo_plug_bedroom_lamp",
                "name": "Bedroom Lamp",
                "location": "Bedroom",
                "power_state": False,
                "current_power": 0.0,
                "daily_energy": 0.3,
                "monthly_energy": 9.0,
                "daily_cost": 0.04,
                "monthly_cost": 1.08,
                "last_seen": "2025-01-16T10:30:00Z",
                "automation_enabled": False,
                "energy_monitoring": True
            },
            {
                "device_id": "tapo_plug_garage_door",
                "name": "Garage Door Opener",
                "location": "Garage",
                "power_state": True,
                "current_power": 12.0,
                "daily_energy": 0.1,
                "monthly_energy": 3.0,
                "daily_cost": 0.01,
                "monthly_cost": 0.36,
                "last_seen": "2025-01-16T10:30:00Z",
                "automation_enabled": True,
                "energy_monitoring": True
            }
        ]
        
        for device_data in sample_devices:
            device = TapoSmartPlug(**device_data)
            self.devices[device.device_id] = device
    
    async def _load_historical_data(self):
        """Load historical energy usage data."""
        # Simulate some historical data
        now = datetime.now()
        for i in range(24):  # Last 24 hours
            timestamp = now - timedelta(hours=i)
            for device_id, device in self.devices.items():
                # Simulate varying power consumption
                power = device.current_power if device.power_state else 0
                energy = power / 1000  # Convert watts to kWh
                cost = energy * self._electricity_rate
                
                usage_data = EnergyUsageData(
                    timestamp=timestamp.isoformat(),
                    device_id=device_id,
                    power_consumption=power,
                    energy_consumption=energy,
                    cost=cost
                )
                self.usage_history.append(usage_data)
    
    async def get_all_devices(self) -> List[TapoSmartPlug]:
        """Get all Tapo smart plug devices."""
        if not self._initialized:
            await self.initialize({})
        
        return list(self.devices.values())
    
    async def get_device_status(self, device_id: str) -> Optional[TapoSmartPlug]:
        """Get status of a specific smart plug device."""
        if not self._initialized:
            await self.initialize({})
        
        return self.devices.get(device_id)
    
    async def toggle_device(self, device_id: str, power_state: bool) -> bool:
        """Toggle power state of a smart plug device."""
        try:
            if device_id not in self.devices:
                return False
            
            device = self.devices[device_id]
            device.power_state = power_state
            device.current_power = 0.0 if not power_state else device.current_power
            device.last_seen = datetime.now().isoformat()
            
            logger.info("Toggled device %s to %s", device_id, "ON" if power_state else "OFF")
            return True
            
        except Exception as e:
            logger.exception("Failed to toggle device %s: %s", device_id, e)
            return False
    
    async def get_energy_usage_history(self, device_id: Optional[str] = None, hours: int = 24) -> List[EnergyUsageData]:
        """Get energy usage history for devices."""
        if not self._initialized:
            await self.initialize({})
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        filtered_data = [
            data for data in self.usage_history
            if datetime.fromisoformat(data.timestamp) >= cutoff_time
        ]
        
        if device_id:
            filtered_data = [data for data in filtered_data if data.device_id == device_id]
        
        return filtered_data
    
    async def calculate_cost_savings(self) -> Dict[str, float]:
        """Calculate potential cost savings from automation."""
        total_current_cost = sum(device.daily_cost for device in self.devices.values())
        
        # Simulate 15% savings from automation
        potential_savings = total_current_cost * 0.15
        monthly_savings = potential_savings * 30
        
        return {
            "daily_savings": potential_savings,
            "monthly_savings": monthly_savings,
            "annual_savings": monthly_savings * 12,
            "current_daily_cost": total_current_cost,
            "savings_percentage": 15.0
        }


# Global Tapo plug manager instance
tapo_plug_manager = TapoPlugManager()


class GetSmartPlugStatusTool(BaseTool):
    """Get status of all Tapo smart plug devices."""
    
    name: str = "get_smart_plug_status"
    description: str = "Get status and energy consumption information for all Tapo smart plug devices"
    category: str = "energy"
    
    async def execute(self) -> Dict[str, Any]:
        """Execute the tool to get smart plug status."""
        try:
            devices = await tapo_plug_manager.get_all_devices()
            
            # Calculate totals
            total_current_power = sum(device.current_power for device in devices if device.power_state)
            total_daily_cost = sum(device.daily_cost for device in devices)
            total_monthly_cost = sum(device.monthly_cost for device in devices)
            active_devices = len([d for d in devices if d.power_state])
            
            return {
                "status": "success",
                "devices": [device.dict() for device in devices],
                "summary": {
                    "total_devices": len(devices),
                    "active_devices": active_devices,
                    "inactive_devices": len(devices) - active_devices,
                    "total_current_power_watts": total_current_power,
                    "total_daily_cost_usd": total_daily_cost,
                    "total_monthly_cost_usd": total_monthly_cost,
                    "automation_enabled_devices": len([d for d in devices if d.automation_enabled])
                },
                "high_consumption_devices": [
                    {
                        "name": d.name,
                        "location": d.location,
                        "current_power": d.current_power,
                        "daily_cost": d.daily_cost
                    } for d in sorted(devices, key=lambda x: x.daily_cost, reverse=True)[:3]
                ]
            }
            
        except Exception as e:
            logger.exception("Failed to get smart plug status: %s", e)
            return {"error": str(e)}


class ControlSmartPlugTool(BaseTool):
    """Control Tapo smart plug devices."""
    
    name: str = "control_smart_plug"
    description: str = "Turn on/off Tapo smart plug devices"
    category: str = "energy"
    
    async def execute(self, device_id: str, power_state: bool) -> Dict[str, Any]:
        """
        Execute the tool to control a smart plug device.
        
        Args:
            device_id: ID of the smart plug device to control
            power_state: True to turn on, False to turn off
        """
        try:
            device = await tapo_plug_manager.get_device_status(device_id)
            if not device:
                return {"error": f"Device {device_id} not found"}
            
            success = await tapo_plug_manager.toggle_device(device_id, power_state)
            
            if success:
                action = "turned on" if power_state else "turned off"
                return {
                    "status": "success",
                    "message": f"Device {device.name} {action} successfully",
                    "device_id": device_id,
                    "device_name": device.name,
                    "power_state": power_state,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {"error": f"Failed to control device {device_id}"}
                
        except Exception as e:
            logger.exception("Failed to control smart plug %s: %s", device_id, e)
            return {"error": str(e)}


class GetEnergyConsumptionTool(BaseTool):
    """Get energy consumption data for smart plug devices."""
    
    name: str = "get_energy_consumption"
    description: str = "Get detailed energy consumption data and cost analysis for smart plug devices"
    category: str = "energy"
    
    async def execute(self, device_id: Optional[str] = None, period: str = "day") -> Dict[str, Any]:
        """
        Execute the tool to get energy consumption data.
        
        Args:
            device_id: Specific device ID (optional, gets all devices if not specified)
            period: Time period (day, week, month)
        """
        try:
            hours_map = {"day": 24, "week": 168, "month": 720}
            hours = hours_map.get(period, 24)
            
            usage_data = await tapo_plug_manager.get_energy_usage_history(device_id, hours)
            
            if not usage_data:
                return {"error": "No usage data available for the specified period"}
            
            # Calculate statistics
            total_power = sum(data.power_consumption for data in usage_data)
            total_energy = sum(data.energy_consumption for data in usage_data)
            total_cost = sum(data.cost for data in usage_data)
            avg_power = total_power / len(usage_data) if usage_data else 0
            peak_power = max(data.power_consumption for data in usage_data) if usage_data else 0
            
            return {
                "status": "success",
                "period": period,
                "hours": hours,
                "device_id": device_id,
                "statistics": {
                    "total_power_consumption_watts": total_power,
                    "total_energy_consumption_kwh": total_energy,
                    "total_cost_usd": total_cost,
                    "average_power_watts": avg_power,
                    "peak_power_watts": peak_power,
                    "data_points": len(usage_data)
                },
                "usage_data": [data.dict() for data in usage_data[-24:]],  # Last 24 data points
                "cost_breakdown": {
                    "hourly_average_cost": total_cost / hours if hours > 0 else 0,
                    "daily_projection": total_cost * (24 / hours) if hours > 0 else 0,
                    "monthly_projection": total_cost * (720 / hours) if hours > 0 else 0
                }
            }
            
        except Exception as e:
            logger.exception("Failed to get energy consumption data: %s", e)
            return {"error": str(e)}


class GetEnergyCostAnalysisTool(BaseTool):
    """Get detailed cost analysis and savings recommendations."""
    
    name: str = "get_energy_cost_analysis"
    description: str = "Get detailed energy cost analysis and savings recommendations"
    category: str = "energy"
    
    async def execute(self) -> Dict[str, Any]:
        """Execute the tool to get energy cost analysis."""
        try:
            devices = await tapo_plug_manager.get_all_devices()
            savings_data = await tapo_plug_manager.calculate_cost_savings()
            
            # Analyze device usage patterns
            high_consumption_devices = [
                {
                    "name": d.name,
                    "location": d.location,
                    "daily_cost": d.daily_cost,
                    "monthly_cost": d.monthly_cost,
                    "power_state": d.power_state,
                    "automation_enabled": d.automation_enabled
                }
                for d in sorted(devices, key=lambda x: x.daily_cost, reverse=True)
            ]
            
            # Generate recommendations
            recommendations = []
            for device in devices:
                if device.daily_cost > 0.20:  # High cost threshold
                    recommendations.append({
                        "device": device.name,
                        "recommendation": "Consider using automation to reduce energy consumption",
                        "potential_savings": device.daily_cost * 0.15,
                        "priority": "high"
                    })
                elif not device.automation_enabled:
                    recommendations.append({
                        "device": device.name,
                        "recommendation": "Enable automation for better energy management",
                        "potential_savings": device.daily_cost * 0.10,
                        "priority": "medium"
                    })
            
            return {
                "status": "success",
                "cost_analysis": savings_data,
                "device_breakdown": high_consumption_devices,
                "recommendations": recommendations,
                "summary": {
                    "total_devices": len(devices),
                    "total_daily_cost": savings_data["current_daily_cost"],
                    "potential_daily_savings": savings_data["daily_savings"],
                    "savings_percentage": savings_data["savings_percentage"],
                    "high_consumption_count": len([d for d in devices if d.daily_cost > 0.20]),
                    "automation_coverage": len([d for d in devices if d.automation_enabled]) / len(devices) * 100
                }
            }
            
        except Exception as e:
            logger.exception("Failed to get energy cost analysis: %s", e)
            return {"error": str(e)}


class SetEnergyAutomationTool(BaseTool):
    """Set up energy automation rules for smart plug devices."""
    
    name: str = "set_energy_automation"
    description: str = "Configure automation rules for energy management on smart plug devices"
    category: str = "energy"
    
    async def execute(
        self, 
        device_id: str, 
        rule_name: str, 
        condition: str, 
        action: str,
        enabled: bool = True
    ) -> Dict[str, Any]:
        """
        Execute the tool to set up energy automation.
        
        Args:
            device_id: Target device ID
            rule_name: Name of the automation rule
            condition: Automation condition (e.g., "time_after_23:00")
            action: Action to take (e.g., "turn_off")
            enabled: Whether the rule is enabled
        """
        try:
            device = await tapo_plug_manager.get_device_status(device_id)
            if not device:
                return {"error": f"Device {device_id} not found"}
            
            # Create automation rule
            rule = EnergyAutomation(
                rule_id=f"rule_{device_id}_{rule_name.lower().replace(' ', '_')}",
                name=rule_name,
                device_id=device_id,
                condition=condition,
                action=action,
                enabled=enabled
            )
            
            tapo_plug_manager.automation_rules.append(rule)
            
            return {
                "status": "success",
                "message": f"Automation rule '{rule_name}' created for {device.name}",
                "rule": rule.dict(),
                "device_name": device.name,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.exception("Failed to set energy automation: %s", e)
            return {"error": str(e)}
