"""
Onboarding API endpoints for device discovery and configuration.

Provides REST API endpoints for the device onboarding process including
device discovery, configuration, and progress tracking.
"""

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field

from ...mcp_client import call_mcp_tool

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/onboarding", tags=["onboarding"])


class DeviceConfigurationRequest(BaseModel):
    """Request model for device configuration."""

    device_id: str = Field(..., description="ID of the device to configure")
    display_name: str = Field(..., description="User-friendly name for the device")
    location: str = Field(..., description="Physical location of the device")
    settings: Dict[str, Any] = Field(default_factory=dict, description="Device-specific settings")


class OnboardingProgressResponse(BaseModel):
    """Response model for onboarding progress."""

    status: str
    current_step: int
    total_devices_discovered: int
    devices_configured: int
    completed_steps: List[str]
    onboarding_complete: bool
    last_updated: str
    device_summary: Dict[str, Dict[str, int]]
    discovered_devices: List[Dict[str, Any]]
    configured_devices: Dict[str, Dict[str, Any]]
    completion_percentage: float
    next_recommended_steps: List[str]


@router.post("/discover", response_model=Dict[str, Any])
async def discover_devices(background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """Start device discovery process via MCP."""
    try:
        # Wrap background task in error handler to prevent crashes
        async def safe_discover():
            try:
                result = await call_mcp_tool("discover_devices", {})
                if not result.get("success"):
                    logger.error(f"Device discovery failed via MCP: {result.get('error')}")
            except Exception as e:
                error_type = type(e).__name__
                error_msg = str(e).lower()

                # Categorize and log with actionable context
                if "timeout" in error_msg or "timed out" in error_msg:
                    logger.error(
                        f"Device discovery timed out: {e}",
                        extra={
                            "error_category": "timeout",
                            "actionable": "Check network connectivity and device availability. Discovery may take longer on slow networks.",
                        },
                    )
                elif "connection" in error_msg or "network" in error_msg:
                    logger.error(
                        f"Device discovery network error: {e}",
                        extra={
                            "error_category": "network",
                            "actionable": "Check network connectivity, firewall settings, and ensure devices are on the same network.",
                        },
                    )
                elif "auth" in error_msg or "credential" in error_msg:
                    logger.error(
                        f"Device discovery authentication error: {e}",
                        extra={
                            "error_category": "authentication",
                            "actionable": "Check device credentials in config.yaml. Some devices require authentication for discovery.",
                        },
                    )
                else:
                    logger.exception(
                        f"Background device discovery failed: {error_type}: {e}",
                        extra={
                            "error_category": "unknown",
                            "error_type": error_type,
                            "actionable": f"Unexpected error during discovery. Check logs for details. Error: {e}",
                        },
                    )
                # Don't re-raise - background task failures shouldn't crash server

        # Start discovery in background
        background_tasks.add_task(safe_discover)

        return {
            "status": "success",
            "message": "Device discovery started",
            "estimated_duration": "30-60 seconds",
        }

    except Exception as e:
        logger.exception("Device discovery failed")
        raise HTTPException(status_code=500, detail=f"Device discovery failed: {e!s}")


@router.get("/discover/results", response_model=Dict[str, Any])
async def get_discovery_results() -> Dict[str, Any]:
    """Get device discovery results via MCP."""
    try:
        # Get discovery results via MCP
        result = await call_mcp_tool("discover_devices", {"get_results": True})
        if result.get("success"):
            data = result.get("data", {})

            # Reorganize results by device type
            discovered_devices = data.get("discovered_devices", [])
            discovery_results = {
                "tapo_p115": [d for d in discovered_devices if d.get("device_type") == "tapo_p115"],
                "usb_webcams": [d for d in discovered_devices if d.get("device_type") == "webcam"],
                "nest_protect": [
                    d for d in discovered_devices if d.get("device_type") == "nest_protect"
                ],
                "ring_devices": [d for d in discovered_devices if d.get("device_type") == "ring"],
            }

            device_counts = {
                device_type: len(devices) for device_type, devices in discovery_results.items()
            }

            return {
                "status": "success",
                "discovery_results": discovery_results,
                "device_counts": device_counts,
                "total_devices": sum(device_counts.values()),
                "onboarding_progress": data.get("onboarding_progress", {}),
            }
        return {
            "status": "error",
            "message": result.get("error", "Failed to get discovery results"),
            "discovery_results": {},
            "device_counts": {},
            "total_devices": 0,
            "onboarding_progress": {},
        }

    except Exception as e:
        logger.exception("Failed to get discovery results via MCP")
        raise HTTPException(status_code=500, detail=f"Failed to get discovery results: {e!s}")


@router.post("/configure", response_model=Dict[str, Any])
async def configure_device(config: DeviceConfigurationRequest) -> Dict[str, Any]:
    """Configure a discovered device via MCP."""
    try:
        result = await call_mcp_tool(
            "configure_device",
            {
                "device_id": config.device_id,
                "display_name": config.display_name,
                "location": config.location,
                "settings": config.settings,
            },
        )

        if result.get("success"):
            data = result.get("data", {})
            return {
                "status": "success",
                "message": data.get(
                    "message", f"Device {config.display_name} configured successfully"
                ),
                "device": data.get("device", {}),
                "configuration": data.get("configuration", {}),
            }
        error_msg = result.get("error", "Failed to configure device")
        if "not found" in error_msg.lower():
            raise HTTPException(status_code=404, detail=error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Device configuration failed via MCP")
        raise HTTPException(status_code=500, detail=f"Device configuration failed: {e!s}")


@router.get("/progress")
async def get_onboarding_progress() -> OnboardingProgressResponse:
    """Get current onboarding progress via MCP."""
    try:
        result = await call_mcp_tool("get_onboarding_progress", {})
        if result.get("success"):
            data = result.get("data", {})
            return OnboardingProgressResponse(**data)
        raise HTTPException(
            status_code=500, detail=result.get("error", "Failed to get onboarding progress")
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to get onboarding progress via MCP")
        raise HTTPException(status_code=500, detail=f"Failed to get onboarding progress: {e!s}")


@router.post("/complete", response_model=Dict[str, Any])
async def complete_onboarding() -> Dict[str, Any]:
    """Complete the onboarding process via MCP."""
    try:
        result = await call_mcp_tool("complete_onboarding", {})
        if result.get("success"):
            return result.get("data", result)
        error_msg = result.get("error", "Failed to complete onboarding")
        if "still need configuration" in error_msg.lower():
            raise HTTPException(status_code=400, detail=error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Onboarding completion failed via MCP")
        raise HTTPException(status_code=500, detail=f"Onboarding completion failed: {e!s}")


@router.get("/devices", response_model=Dict[str, Any])
async def get_discovered_devices() -> Dict[str, Any]:
    """Get all discovered devices via MCP."""
    try:
        result = await call_mcp_tool("discover_devices", {"get_devices": True})
        if result.get("success"):
            data = result.get("data", {})
            return {
                "status": "success",
                "devices": data.get("devices", []),
                "total_count": data.get("total_count", 0),
            }
        return {
            "status": "error",
            "devices": [],
            "total_count": 0,
            "error": result.get("error", "Failed to get discovered devices"),
        }

    except Exception as e:
        logger.exception("Failed to get discovered devices via MCP")
        raise HTTPException(status_code=500, detail=f"Failed to get discovered devices: {e!s}")


@router.get("/devices/{device_id}", response_model=Dict[str, Any])
async def get_device_details(device_id: str) -> Dict[str, Any]:
    """Get details for a specific device via MCP."""
    try:
        result = await call_mcp_tool("discover_devices", {"get_device": device_id})
        if result.get("success"):
            data = result.get("data", {})
            if data:
                return {
                    "status": "success",
                    "device": data.get("device", {}),
                    "configuration": data.get("configuration"),
                    "is_configured": data.get("is_configured", False),
                }
            raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
        error_msg = result.get("error", "Failed to get device details")
        if "not found" in error_msg.lower():
            raise HTTPException(status_code=404, detail=error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to get device details via MCP")
        raise HTTPException(status_code=500, detail=f"Failed to get device details: {e!s}")


@router.delete("/reset", response_model=Dict[str, Any])
async def reset_onboarding() -> Dict[str, Any]:
    """Reset the onboarding process via MCP."""
    try:
        # Note: Reset functionality may not be available in MCP tools yet
        # TODO: Add reset action to device discovery MCP tools
        result = await call_mcp_tool("discover_devices", {"reset": True})
        if result.get("success"):
            return result.get(
                "data", {"status": "success", "message": "Onboarding process reset successfully"}
            )
        return {
            "status": "error",
            "message": result.get(
                "error", "Failed to reset onboarding - feature not available via MCP"
            ),
            "note": "Reset functionality may not be implemented in MCP tools yet",
        }

    except Exception as e:
        logger.exception("Failed to reset onboarding via MCP")
        raise HTTPException(status_code=500, detail=f"Failed to reset onboarding: {e!s}")


@router.get("/recommendations", response_model=Dict[str, Any])
async def get_setup_recommendations() -> Dict[str, Any]:
    """Get smart setup recommendations based on discovered devices via MCP."""
    try:
        result = await call_mcp_tool("discover_devices", {"get_recommendations": True})
        if result.get("success"):
            data = result.get("data", {})
            return {
                "status": "success",
                "recommendations": data.get("recommendations", []),
                "total_recommendations": data.get("total_recommendations", 0),
            }
        return {
            "status": "error",
            "recommendations": [],
            "total_recommendations": 0,
            "error": result.get("error", "Failed to get setup recommendations"),
        }

    except Exception as e:
        logger.exception("Failed to get setup recommendations via MCP")
        raise HTTPException(status_code=500, detail=f"Failed to get setup recommendations: {e!s}")
