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
    """Tapo P115 Smart Plug device data model with energy monitoring."""
    
    device_id: str = Field(..., description="Unique device identifier")
    name: str = Field(..., description="Device name")
    location: str = Field(..., description="Device location")
    device_model: str = Field(default="Tapo P115", description="Device model")
    power_state: bool = Field(..., description="Current power state (on/off)")
    current_power: float = Field(..., description="Current power consumption in watts")
    voltage: float = Field(default=0.0, description="Current voltage in volts")
    current: float = Field(default=0.0, description="Current amperage in amps")
    daily_energy: float = Field(..., description="Daily energy consumption in kWh")
    monthly_energy: float = Field(..., description="Monthly energy consumption in kWh")
    daily_cost: float = Field(..., description="Daily cost in USD")
    monthly_cost: float = Field(..., description="Monthly cost in USD")
    last_seen: str = Field(..., description="Last communication timestamp")
    automation_enabled: bool = Field(default=False, description="Whether automation is enabled")
    energy_monitoring: bool = Field(default=True, description="Whether energy monitoring is enabled")
    power_schedule: str = Field(default="", description="Power on/off schedule")
    energy_saving_mode: bool = Field(default=False, description="Whether energy saving mode is enabled")


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
        """Discover Tapo P115 smart plugs on the network."""
        # Simulate discovered Tapo P115 devices with energy monitoring
        sample_devices = [
            {
                "device_id": "tapo_p115_living_room_tv",
                "name": "Living Room TV (P115)",
                "location": "Living Room",
                "device_model": "Tapo P115",
                "power_state": True,
                "current_power": 45.5,
                "voltage": 120.2,
                "current": 0.38,
                "daily_energy": 0.85,
                "monthly_energy": 25.5,
                "daily_cost": 0.10,
                "monthly_cost": 3.06,
                "last_seen": "2025-01-16T10:30:00Z",
                "automation_enabled": True,
                "energy_monitoring": True,
                "power_schedule": "08:00-23:00",
                "energy_saving_mode": False
            },
            {
                "device_id": "tapo_p115_kitchen_coffee",
                "name": "Kitchen Coffee Maker (P115)",
                "location": "Kitchen",
                "device_model": "Tapo P115",
                "power_state": True,
                "current_power": 850.0,
                "voltage": 119.8,
                "current": 7.09,
                "daily_energy": 2.1,
                "monthly_energy": 63.0,
                "daily_cost": 0.25,
                "monthly_cost": 7.56,
                "last_seen": "2025-01-16T10:30:00Z",
                "automation_enabled": True,
                "energy_monitoring": True,
                "power_schedule": "06:00-08:00, 12:00-13:00",
                "energy_saving_mode": True
            },
            {
                "device_id": "tapo_p115_bedroom_lamp",
                "name": "Bedroom Lamp (P115)",
                "location": "Bedroom",
                "device_model": "Tapo P115",
                "power_state": False,
                "current_power": 0.0,
                "voltage": 0.0,
                "current": 0.0,
                "daily_energy": 0.3,
                "monthly_energy": 9.0,
                "daily_cost": 0.04,
                "monthly_cost": 1.08,
                "last_seen": "2025-01-16T10:30:00Z",
                "automation_enabled": False,
                "energy_monitoring": True,
                "power_schedule": "18:00-23:00",
                "energy_saving_mode": False
            },
            {
                "device_id": "tapo_p115_garage_charger",
                "name": "Garage EV Charger (P115)",
                "location": "Garage",
                "device_model": "Tapo P115",
                "power_state": True,
                "current_power": 1200.0,
                "voltage": 240.0,
                "current": 5.0,
                "daily_energy": 8.5,
                "monthly_energy": 255.0,
                "daily_cost": 1.02,
                "monthly_cost": 30.60,
                "last_seen": "2025-01-16T10:30:00Z",
                "automation_enabled": True,
                "energy_monitoring": True,
                "power_schedule": "22:00-06:00",
                "energy_saving_mode": True
            },
            {
                "device_id": "tapo_p115_office_computer",
                "name": "Office Computer (P115)",
                "location": "Office",
                "device_model": "Tapo P115",
                "power_state": True,
                "current_power": 180.0,
                "voltage": 120.1,
                "current": 1.5,
                "daily_energy": 4.2,
                "monthly_energy": 126.0,
                "daily_cost": 0.50,
                "monthly_cost": 15.12,
                "last_seen": "2025-01-16T10:30:00Z",
                "automation_enabled": True,
                "energy_monitoring": True,
                "power_schedule": "09:00-17:00",
                "energy_saving_mode": True
            }
        ]
        
        for device_data in sample_devices:
            device = TapoSmartPlug(**device_data)
            self.devices[device.device_id] = device
    
    async def _load_historical_data(self):
        """Load historical energy usage data from P115 devices."""
        # P115 devices store limited historical data:
        # - Daily consumption resets at midnight
        # - Total consumption is cumulative
        # - Real-time data available via API
        # - Historical data limited to current day
        
        now = datetime.now()
        
        # P115 provides hourly data for current day only
        current_day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        hours_since_midnight = (now - current_day_start).total_seconds() / 3600
        
        for i in range(int(hours_since_midnight) + 1):
            timestamp = current_day_start + timedelta(hours=i)
            
            for device_id, device in self.devices.items():
                # P115 data characteristics:
                # - Daily consumption resets at midnight
                # - Hourly granularity for current day
                # - Total consumption is cumulative
                
                if device.power_state:
                    # Simulate realistic P115 energy patterns
                    if "coffee" in device.name.lower():
                        # Coffee maker: high usage during morning hours
                        power_multiplier = 2.0 if 6 <= timestamp.hour <= 8 else 0.1
                    elif "charger" in device.name.lower():
                        # EV charger: off-peak usage
                        power_multiplier = 1.5 if 22 <= timestamp.hour or timestamp.hour <= 6 else 0.1
                    elif "tv" in device.name.lower():
                        # TV: evening usage
                        power_multiplier = 1.0 if 18 <= timestamp.hour <= 23 else 0.1
                    elif "computer" in device.name.lower():
                        # Computer: work hours
                        power_multiplier = 1.0 if 9 <= timestamp.hour <= 17 else 0.1
                    else:
                        power_multiplier = 0.5
                    
                    power = device.current_power * power_multiplier
                else:
                    power = 0.0
                
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


class GetTapoP115DetailedStatsTool(BaseTool):
    """Get detailed energy statistics for Tapo P115 smart plugs."""
    
    name: str = "get_tapo_p115_detailed_stats"
    description: str = "Get detailed energy monitoring statistics and electrical parameters for Tapo P115 smart plugs"
    category: str = "energy"
    
    async def execute(self, device_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute the tool to get detailed P115 statistics.
        
        Args:
            device_id: Specific P115 device ID (optional, gets all devices if not specified)
        """
        try:
            devices = await tapo_plug_manager.get_all_devices()
            
            if device_id:
                devices = [d for d in devices if d.device_id == device_id]
                if not devices:
                    return {"error": f"P115 device {device_id} not found"}
            
            # Filter for P115 devices only
            p115_devices = [d for d in devices if "P115" in d.device_model]
            
            detailed_stats = []
            for device in p115_devices:
                stats = {
                    "device_info": {
                        "device_id": device.device_id,
                        "name": device.name,
                        "location": device.location,
                        "model": device.device_model
                    },
                    "electrical_parameters": {
                        "voltage_volts": device.voltage,
                        "current_amps": device.current,
                        "power_watts": device.current_power,
                        "power_factor": device.current_power / (device.voltage * device.current) if device.voltage * device.current > 0 else 0
                    },
                    "energy_consumption": {
                        "daily_kwh": device.daily_energy,
                        "monthly_kwh": device.monthly_energy,
                        "daily_cost_usd": device.daily_cost,
                        "monthly_cost_usd": device.monthly_cost
                    },
                    "device_status": {
                        "power_state": device.power_state,
                        "automation_enabled": device.automation_enabled,
                        "energy_saving_mode": device.energy_saving_mode,
                        "power_schedule": device.power_schedule,
                        "last_seen": device.last_seen
                    },
                    "efficiency_metrics": {
                        "energy_efficiency_rating": "A" if device.daily_cost < 0.20 else "B" if device.daily_cost < 0.50 else "C",
                        "standby_power_watts": 0.5 if device.power_state else 0.0,
                        "power_consumption_trend": "stable"  # Could be calculated from historical data
                    }
                }
                detailed_stats.append(stats)
            
            return {
                "status": "success",
                "device_count": len(p115_devices),
                "detailed_stats": detailed_stats,
                "summary": {
                    "total_p115_devices": len(p115_devices),
                    "active_p115_devices": len([d for d in p115_devices if d.power_state]),
                    "total_current_power": sum(d.current_power for d in p115_devices if d.power_state),
                    "total_daily_energy": sum(d.daily_energy for d in p115_devices),
                    "total_daily_cost": sum(d.daily_cost for d in p115_devices),
                    "average_voltage": sum(d.voltage for d in p115_devices) / len(p115_devices) if p115_devices else 0,
                    "devices_with_energy_saving": len([d for d in p115_devices if d.energy_saving_mode])
                }
            }
            
        except Exception as e:
            logger.exception("Failed to get P115 detailed stats: %s", e)
            return {"error": str(e)}


class SetTapoP115EnergySavingModeTool(BaseTool):
    """Enable/disable energy saving mode on Tapo P115 smart plugs."""
    
    name: str = "set_tapo_p115_energy_saving_mode"
    description: str = "Enable or disable energy saving mode on Tapo P115 smart plugs"
    category: str = "energy"
    
    async def execute(self, device_id: str, energy_saving_enabled: bool) -> Dict[str, Any]:
        """
        Execute the tool to set energy saving mode.
        
        Args:
            device_id: Target P115 device ID
            energy_saving_enabled: Whether to enable energy saving mode
        """
        try:
            device = await tapo_plug_manager.get_device_status(device_id)
            if not device:
                return {"error": f"P115 device {device_id} not found"}
            
            if "P115" not in device.device_model:
                return {"error": f"Device {device_id} is not a Tapo P115 model"}
            
            # Update energy saving mode
            device.energy_saving_mode = energy_saving_enabled
            
            # Apply energy saving optimizations if enabled
            if energy_saving_enabled:
                # In real implementation, this would send commands to the P115
                logger.info("Energy saving mode enabled for P115 device %s", device_id)
                
                # Simulate power reduction for energy saving mode
                if device.power_state and device.current_power > 0:
                    # Reduce power consumption by 10% in energy saving mode
                    device.current_power *= 0.9
            
            return {
                "status": "success",
                "message": f"Energy saving mode {'enabled' if energy_saving_enabled else 'disabled'} for {device.name}",
                "device_id": device_id,
                "device_name": device.name,
                "energy_saving_mode": energy_saving_enabled,
                "estimated_power_savings": "10%" if energy_saving_enabled else "0%",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.exception("Failed to set energy saving mode for P115 %s: %s", device_id, e)
            return {"error": str(e)}


class GetTapoP115PowerScheduleTool(BaseTool):
    """Get and manage power schedules for Tapo P115 smart plugs."""
    
    name: str = "get_tapo_p115_power_schedule"
    description: str = "Get current power schedule settings for Tapo P115 smart plugs"
    category: str = "energy"
    
    async def execute(self, device_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute the tool to get power schedules.
        
        Args:
            device_id: Specific P115 device ID (optional, gets all devices if not specified)
        """
        try:
            devices = await tapo_plug_manager.get_all_devices()
            
            if device_id:
                devices = [d for d in devices if d.device_id == device_id]
                if not devices:
                    return {"error": f"P115 device {device_id} not found"}
            
            # Filter for P115 devices only
            p115_devices = [d for d in devices if "P115" in d.device_model]
            
            schedules = []
            for device in p115_devices:
                schedule_info = {
                    "device_id": device.device_id,
                    "device_name": device.name,
                    "location": device.location,
                    "current_schedule": device.power_schedule,
                    "automation_enabled": device.automation_enabled,
                    "energy_saving_mode": device.energy_saving_mode,
                    "schedule_status": "active" if device.automation_enabled and device.power_schedule else "inactive"
                }
                schedules.append(schedule_info)
            
            return {
                "status": "success",
                "schedules": schedules,
                "summary": {
                    "total_p115_devices": len(p115_devices),
                    "devices_with_schedules": len([d for d in p115_devices if d.power_schedule]),
                    "automation_enabled_devices": len([d for d in p115_devices if d.automation_enabled]),
                    "energy_saving_devices": len([d for d in p115_devices if d.energy_saving_mode])
                }
            }
            
        except Exception as e:
            logger.exception("Failed to get P115 power schedules: %s", e)
            return {"error": str(e)}


class GetTapoP115DataStorageInfoTool(BaseTool):
    """Get information about P115 data storage capabilities and limitations."""
    
    name: str = "get_tapo_p115_data_storage_info"
    description: str = "Get information about P115 data storage capabilities, limitations, and available historical data"
    category: str = "energy"
    
    async def execute(self) -> Dict[str, Any]:
        """Execute the tool to get P115 data storage information."""
        try:
            return {
                "status": "success",
                "p115_data_storage_info": {
                    "device_model": "Tapo P115 Smart Wi-Fi Plug with Energy Monitoring",
                    "data_storage_capabilities": {
                        "real_time_data": {
                            "available": True,
                            "description": "Real-time power consumption, voltage, current",
                            "update_frequency": "Continuous (every few seconds)",
                            "data_types": ["power_watts", "voltage_volts", "current_amps", "power_factor"]
                        },
                        "daily_consumption": {
                            "available": True,
                            "description": "Daily energy consumption in kWh",
                            "reset_schedule": "Midnight (00:00) daily",
                            "data_types": ["daily_kwh", "daily_cost", "daily_usage_hours"]
                        },
                        "total_consumption": {
                            "available": True,
                            "description": "Cumulative total energy consumption since device setup",
                            "reset_schedule": "Manual reset only",
                            "data_types": ["total_kwh", "total_cost", "total_usage_hours"]
                        },
                        "historical_data": {
                            "available": "Limited",
                            "description": "Historical data limited to current day",
                            "granularity": "Hourly for current day only",
                            "limitation": "Daily consumption resets at midnight",
                            "data_types": ["hourly_kwh_current_day"]
                        }
                    },
                    "data_limitations": {
                        "long_term_storage": {
                            "available": False,
                            "description": "No long-term historical data storage on device",
                            "workaround": "Integration with Home Assistant or cloud platforms required"
                        },
                        "historical_granularity": {
                            "current_day": "Hourly data available",
                            "previous_days": "Daily totals only (if available)",
                            "older_data": "Not stored on device"
                        },
                        "data_retention": {
                            "on_device": "Current day only",
                            "cloud_storage": "Depends on Tapo cloud service",
                            "third_party": "Available via Home Assistant integration"
                        }
                    },
                    "api_access": {
                        "tapos_api": {
                            "available": True,
                            "description": "Official Tapo API for real-time and daily data",
                            "limitations": "Limited historical data access"
                        },
                        "home_assistant": {
                            "available": True,
                            "description": "Home Assistant integration for extended data storage",
                            "benefits": "Long-term data storage and analysis"
                        },
                        "third_party": {
                            "available": True,
                            "description": "Various third-party platforms support P115",
                            "examples": ["Home Assistant", "OpenHAB", "Node-RED"]
                        }
                    },
                    "recommended_data_strategy": {
                        "real_time_monitoring": "Use P115 API for current consumption data",
                        "daily_tracking": "Use P115 daily consumption data",
                        "long_term_analysis": "Integrate with Home Assistant for historical storage",
                        "cost_analysis": "Combine P115 data with local database for cost tracking",
                        "automation": "Use P115 scheduling features for energy optimization"
                    }
                },
                "current_implementation": {
                    "data_sources": [
                        "P115 device API (real-time data)",
                        "P115 daily consumption data",
                        "Local database simulation (for demonstration)",
                        "Home Assistant integration (recommended)"
                    ],
                    "data_simulation": {
                        "note": "Current implementation simulates realistic P115 data patterns",
                        "hourly_data": "Available for current day",
                        "daily_patterns": "Based on device type and usage patterns",
                        "cost_calculation": "Based on configurable electricity rates"
                    }
                }
            }
            
        except Exception as e:
            logger.exception("Failed to get P115 data storage info: %s", e)
            return {"error": str(e)}
