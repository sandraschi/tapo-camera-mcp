"""
Onboarding Tools Package

This package provides device discovery and onboarding tools for the
Tapo Camera MCP platform, enabling users to easily set up their
diverse device collections.
"""

from .device_discovery_tools import (
    DiscoverDevicesTool,
    ConfigureDeviceTool,
    GetOnboardingProgressTool,
    CompleteOnboardingTool,
    DiscoveredDevice,
    OnboardingState,
    DeviceDiscoveryManager,
    discovery_manager
)

__all__ = [
    "DiscoverDevicesTool",
    "ConfigureDeviceTool", 
    "GetOnboardingProgressTool",
    "CompleteOnboardingTool",
    "DiscoveredDevice",
    "OnboardingState",
    "DeviceDiscoveryManager",
    "discovery_manager"
]
