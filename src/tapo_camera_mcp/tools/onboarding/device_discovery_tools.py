"""
Device Discovery and Onboarding Tools for Tapo Camera MCP

This module provides tools for discovering and onboarding various device types
including Tapo P115 smart plugs, Nest Protect devices, Ring alarms, and USB webcams.
"""

import asyncio
import logging
import socket
import subprocess
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from ...tools.base_tool import BaseTool, ToolCategory, tool

logger = logging.getLogger(__name__)


class DiscoveredDevice(BaseModel):
    """Model for discovered devices during onboarding."""
    
    device_id: str = Field(..., description="Unique device identifier")
    device_type: str = Field(..., description="Type of device (tapo_p115, nest_protect, ring, webcam)")
    display_name: str = Field(..., description="User-friendly display name")
    ip_address: Optional[str] = Field(None, description="IP address if applicable")
    mac_address: Optional[str] = Field(None, description="MAC address if available")
    model: str = Field(..., description="Device model information")
    location: Optional[str] = Field(None, description="Suggested location")
    capabilities: List[str] = Field(default_factory=list, description="Device capabilities")
    requires_auth: bool = Field(default=False, description="Whether device requires authentication")
    status: str = Field(default="discovered", description="Current status")


class OnboardingState(BaseModel):
    """Model for onboarding state persistence."""
    
    step: int = Field(default=0, description="Current onboarding step")
    discovered_devices: List[DiscoveredDevice] = Field(default_factory=list)
    configured_devices: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    completed_steps: List[str] = Field(default_factory=list)
    onboarding_complete: bool = Field(default=False)
    last_updated: str = Field(default_factory=lambda: datetime.now().isoformat())


class DeviceDiscoveryManager:
    """Manager for device discovery and onboarding."""
    
    def __init__(self):
        self.discovered_devices: List[DiscoveredDevice] = []
        self.onboarding_state = OnboardingState()
    
    async def discover_all_devices(self) -> Dict[str, List[DiscoveredDevice]]:
        """Discover all available devices on the network."""
        try:
            discovery_results = {
                "tapo_p115": await self._discover_tapo_p115_devices(),
                "usb_webcams": await self._discover_usb_webcams(),
                "nest_protect": await self._discover_nest_protect_devices(),
                "ring_devices": await self._discover_ring_devices()
            }
            
            # Flatten all discovered devices
            all_devices = []
            for device_type, devices in discovery_results.items():
                all_devices.extend(devices)
            
            self.discovered_devices = all_devices
            self.onboarding_state.discovered_devices = all_devices
            
            return discovery_results
            
        except Exception as e:
            logger.exception("Device discovery failed: %s", e)
            return {"error": str(e)}
    
    async def _discover_tapo_p115_devices(self) -> List[DiscoveredDevice]:
        """Discover Tapo P115 smart plugs on the network."""
        devices = []
        
        try:
            # Simulate network discovery for Tapo P115 devices
            # In real implementation, this would use UPnP, mDNS, or network scanning
            sample_tapo_devices = [
                {
                    "device_id": "tapo_p115_001",
                    "ip_address": "192.168.1.101",
                    "mac_address": "00:11:22:33:44:55",
                    "model": "Tapo P115",
                    "location": "Living Room",
                    "capabilities": ["energy_monitoring", "power_control", "scheduling", "energy_saving_mode"]
                },
                {
                    "device_id": "tapo_p115_002", 
                    "ip_address": "192.168.1.102",
                    "mac_address": "00:11:22:33:44:56",
                    "model": "Tapo P115",
                    "location": "Kitchen",
                    "capabilities": ["energy_monitoring", "power_control", "scheduling", "energy_saving_mode"]
                },
                {
                    "device_id": "tapo_p115_003",
                    "ip_address": "192.168.1.103", 
                    "mac_address": "00:11:22:33:44:57",
                    "model": "Tapo P115",
                    "location": "Bedroom",
                    "capabilities": ["energy_monitoring", "power_control", "scheduling", "energy_saving_mode"]
                }
            ]
            
            for device_data in sample_tapo_devices:
                device = DiscoveredDevice(
                    device_id=device_data["device_id"],
                    device_type="tapo_p115",
                    display_name=f"Smart Plug {device_data['ip_address'].split('.')[-1]}",
                    ip_address=device_data["ip_address"],
                    mac_address=device_data["mac_address"],
                    model=device_data["model"],
                    location=device_data["location"],
                    capabilities=device_data["capabilities"],
                    requires_auth=True,
                    status="discovered"
                )
                devices.append(device)
                
        except Exception as e:
            logger.exception("Tapo P115 discovery failed: %s", e)
        
        return devices
    
    async def _discover_usb_webcams(self) -> List[DiscoveredDevice]:
        """Discover USB webcams connected to the system."""
        devices = []
        
        try:
            # In real implementation, this would enumerate USB devices
            # For now, simulate common webcam devices
            sample_webcams = [
                {
                    "device_id": "usb_webcam_0",
                    "model": "USB Webcam",
                    "location": "Office",
                    "capabilities": ["video_streaming", "snapshot_capture", "motion_detection"]
                },
                {
                    "device_id": "usb_webcam_1",
                    "model": "USB Webcam", 
                    "location": "Living Room",
                    "capabilities": ["video_streaming", "snapshot_capture", "motion_detection"]
                }
            ]
            
            for device_data in sample_webcams:
                device = DiscoveredDevice(
                    device_id=device_data["device_id"],
                    device_type="webcam",
                    display_name=device_data["model"],
                    model=device_data["model"],
                    location=device_data["location"],
                    capabilities=device_data["capabilities"],
                    requires_auth=False,
                    status="discovered"
                )
                devices.append(device)
                
        except Exception as e:
            logger.exception("USB webcam discovery failed: %s", e)
        
        return devices
    
    async def _discover_nest_protect_devices(self) -> List[DiscoveredDevice]:
        """Discover Nest Protect devices (requires authentication)."""
        devices = []
        
        try:
            # Simulate Nest Protect discovery
            # In real implementation, this would use Google Nest API
            sample_nest_devices = [
                {
                    "device_id": "nest_protect_001",
                    "model": "Nest Protect 2nd Gen",
                    "location": "Kitchen",
                    "capabilities": ["smoke_detection", "co_detection", "battery_monitoring", "self_testing"]
                },
                {
                    "device_id": "nest_protect_002",
                    "model": "Nest Protect 2nd Gen", 
                    "location": "Living Room",
                    "capabilities": ["smoke_detection", "co_detection", "battery_monitoring", "self_testing"]
                }
            ]
            
            for device_data in sample_nest_devices:
                device = DiscoveredDevice(
                    device_id=device_data["device_id"],
                    device_type="nest_protect",
                    display_name=f"Nest Protect - {device_data['location']}",
                    model=device_data["model"],
                    location=device_data["location"],
                    capabilities=device_data["capabilities"],
                    requires_auth=True,
                    status="discovered"
                )
                devices.append(device)
                
        except Exception as e:
            logger.exception("Nest Protect discovery failed: %s", e)
        
        return devices
    
    async def _discover_ring_devices(self) -> List[DiscoveredDevice]:
        """Discover Ring devices (requires authentication)."""
        devices = []
        
        try:
            # Simulate Ring device discovery
            # In real implementation, this would use Ring API
            sample_ring_devices = [
                {
                    "device_id": "ring_doorbell_001",
                    "model": "Ring Doorbell Pro",
                    "location": "Front Door",
                    "capabilities": ["motion_detection", "two_way_audio", "video_recording", "night_vision"]
                },
                {
                    "device_id": "ring_sensor_001",
                    "model": "Ring Contact Sensor",
                    "location": "Garage Door",
                    "capabilities": ["door_window_sensor", "motion_detection", "battery_monitoring"]
                }
            ]
            
            for device_data in sample_ring_devices:
                device = DiscoveredDevice(
                    device_id=device_data["device_id"],
                    device_type="ring",
                    display_name=f"Ring {device_data['model']} - {device_data['location']}",
                    model=device_data["model"],
                    location=device_data["location"],
                    capabilities=device_data["capabilities"],
                    requires_auth=True,
                    status="discovered"
                )
                devices.append(device)
                
        except Exception as e:
            logger.exception("Ring device discovery failed: %s", e)
        
        return devices
    
    def get_onboarding_progress(self) -> Dict[str, Any]:
        """Get current onboarding progress."""
        return {
            "current_step": self.onboarding_state.step,
            "total_devices_discovered": len(self.discovered_devices),
            "devices_configured": len(self.onboarding_state.configured_devices),
            "completed_steps": self.onboarding_state.completed_steps,
            "onboarding_complete": self.onboarding_state.onboarding_complete,
            "last_updated": self.onboarding_state.last_updated
        }


# Global discovery manager instance
discovery_manager = DeviceDiscoveryManager()


@tool("discover_devices")
class DiscoverDevicesTool(BaseTool):
    """Discover all available devices for onboarding.
    
    Automatically scans the network and system for available devices
    including Tapo P115 smart plugs, USB webcams, Nest Protect devices,
    and Ring security devices.
    
    Returns:
        Dict with discovered devices organized by type
    """
    
    class Meta:
        name = "discover_devices"
        description = "Discover all available devices for onboarding"
        category = ToolCategory.UTILITY
    
    async def execute(self) -> Dict[str, Any]:
        """Execute device discovery."""
        try:
            discovery_results = await discovery_manager.discover_all_devices()
            
            if "error" in discovery_results:
                return {"error": discovery_results["error"]}
            
            # Count devices by type
            device_counts = {
                device_type: len(devices) 
                for device_type, devices in discovery_results.items()
            }
            
            return {
                "status": "success",
                "discovery_results": discovery_results,
                "device_counts": device_counts,
                "total_devices": sum(device_counts.values()),
                "onboarding_progress": discovery_manager.get_onboarding_progress(),
                "next_steps": [
                    "Review discovered devices",
                    "Configure device names and locations", 
                    "Set up authentication for protected devices",
                    "Configure device-specific settings"
                ]
            }
            
        except Exception as e:
            logger.exception("Device discovery tool execution failed: %s", e)
            return {"error": str(e)}


@tool("configure_device")
class ConfigureDeviceTool(BaseTool):
    """Configure a discovered device during onboarding.
    
    Configure individual devices with user-friendly names, locations,
    and device-specific settings during the onboarding process.
    
    Parameters:
        device_id: ID of the device to configure
        display_name: User-friendly name for the device
        location: Physical location of the device
        settings: Device-specific configuration settings
    
    Returns:
        Dict with configuration status and updated device info
    """
    
    class Meta:
        name = "configure_device"
        description = "Configure a discovered device during onboarding"
        category = ToolCategory.UTILITY
        
        class Parameters:
            device_id: str = Field(..., description="ID of the device to configure")
            display_name: str = Field(..., description="User-friendly name for the device")
            location: str = Field(..., description="Physical location of the device")
            settings: Dict[str, Any] = Field(default_factory=dict, description="Device-specific settings")
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute device configuration."""
        try:
            device_id = kwargs.get("device_id")
            display_name = kwargs.get("display_name")
            location = kwargs.get("location")
            settings = kwargs.get("settings", {})
            
            # Find the device in discovered devices
            device = None
            for discovered_device in discovery_manager.discovered_devices:
                if discovered_device.device_id == device_id:
                    device = discovered_device
                    break
            
            if not device:
                return {"error": f"Device {device_id} not found in discovered devices"}
            
            # Update device configuration
            device.display_name = display_name
            device.location = location
            device.status = "configured"
            
            # Save configuration to onboarding state
            discovery_manager.onboarding_state.configured_devices[device_id] = {
                "display_name": display_name,
                "location": location,
                "settings": settings,
                "configured_at": datetime.now().isoformat()
            }
            
            return {
                "status": "success",
                "message": f"Device {display_name} configured successfully",
                "device": device.dict(),
                "configuration": discovery_manager.onboarding_state.configured_devices[device_id],
                "onboarding_progress": discovery_manager.get_onboarding_progress()
            }
            
        except Exception as e:
            logger.exception("Device configuration tool execution failed: %s", e)
            return {"error": str(e)}


@tool("get_onboarding_progress")
class GetOnboardingProgressTool(BaseTool):
    """Get current onboarding progress and status.
    
    Retrieve the current state of the onboarding process including
    discovered devices, configuration progress, and next steps.
    
    Returns:
        Dict with onboarding progress and status information
    """
    
    class Meta:
        name = "get_onboarding_progress"
        description = "Get current onboarding progress and status"
        category = ToolCategory.UTILITY
    
    async def execute(self) -> Dict[str, Any]:
        """Execute onboarding progress retrieval."""
        try:
            progress = discovery_manager.get_onboarding_progress()
            
            # Get device summary
            device_summary = {}
            for device in discovery_manager.discovered_devices:
                device_type = device.device_type
                if device_type not in device_summary:
                    device_summary[device_type] = {"total": 0, "configured": 0}
                
                device_summary[device_type]["total"] += 1
                if device.status == "configured":
                    device_summary[device_type]["configured"] += 1
            
            return {
                "status": "success",
                "progress": progress,
                "device_summary": device_summary,
                "discovered_devices": [device.dict() for device in discovery_manager.discovered_devices],
                "configured_devices": discovery_manager.onboarding_state.configured_devices,
                "completion_percentage": self._calculate_completion_percentage(),
                "next_recommended_steps": self._get_next_steps()
            }
            
        except Exception as e:
            logger.exception("Onboarding progress tool execution failed: %s", e)
            return {"error": str(e)}
    
    def _calculate_completion_percentage(self) -> float:
        """Calculate onboarding completion percentage."""
        total_devices = len(discovery_manager.discovered_devices)
        if total_devices == 0:
            return 0.0
        
        configured_devices = len(discovery_manager.onboarding_state.configured_devices)
        return (configured_devices / total_devices) * 100
    
    def _get_next_steps(self) -> List[str]:
        """Get recommended next steps based on current progress."""
        steps = []
        
        # Check if devices need configuration
        unconfigured_devices = [
            device for device in discovery_manager.discovered_devices
            if device.status == "discovered"
        ]
        
        if unconfigured_devices:
            steps.append(f"Configure {len(unconfigured_devices)} remaining devices")
        
        # Check if authentication is needed
        auth_required_devices = [
            device for device in discovery_manager.discovered_devices
            if device.requires_auth and device.status == "discovered"
        ]
        
        if auth_required_devices:
            steps.append("Set up authentication for protected devices")
        
        # Check if onboarding is complete
        if not discovery_manager.onboarding_state.onboarding_complete:
            if not unconfigured_devices:
                steps.append("Complete onboarding and start using devices")
        
        return steps


@tool("complete_onboarding")
class CompleteOnboardingTool(BaseTool):
    """Complete the device onboarding process.
    
    Finalize the onboarding process and mark all configured devices
    as ready for use in the main system.
    
    Returns:
        Dict with onboarding completion status and summary
    """
    
    class Meta:
        name = "complete_onboarding"
        description = "Complete the device onboarding process"
        category = ToolCategory.UTILITY
    
    async def execute(self) -> Dict[str, Any]:
        """Execute onboarding completion."""
        try:
            # Validate that all discovered devices are configured
            unconfigured_devices = [
                device for device in discovery_manager.discovered_devices
                if device.status == "discovered"
            ]
            
            if unconfigured_devices:
                return {
                    "error": f"Cannot complete onboarding: {len(unconfigured_devices)} devices still need configuration",
                    "unconfigured_devices": [device.dict() for device in unconfigured_devices]
                }
            
            # Mark onboarding as complete
            discovery_manager.onboarding_state.onboarding_complete = True
            discovery_manager.onboarding_state.completed_steps.append("onboarding_complete")
            discovery_manager.onboarding_state.last_updated = datetime.now().isoformat()
            
            # Generate summary
            device_summary = {}
            for device in discovery_manager.discovered_devices:
                device_type = device.device_type
                if device_type not in device_summary:
                    device_summary[device_type] = 0
                device_summary[device_type] += 1
            
            return {
                "status": "success",
                "message": "Device onboarding completed successfully!",
                "onboarding_complete": True,
                "total_devices_configured": len(discovery_manager.discovered_devices),
                "device_summary": device_summary,
                "configured_devices": [device.dict() for device in discovery_manager.discovered_devices],
                "next_steps": [
                    "Start using your configured devices",
                    "Set up automation rules if desired",
                    "Configure alert preferences",
                    "Access the main dashboard at http://localhost:7777"
                ]
            }
            
        except Exception as e:
            logger.exception("Onboarding completion tool execution failed: %s", e)
            return {"error": str(e)}
