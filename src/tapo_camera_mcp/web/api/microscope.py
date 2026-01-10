"""USB Microscope API endpoints."""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from tapo_camera_mcp.mcp_client import call_mcp_tool

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/microscope", tags=["microscope"])


class MagnificationRequest(BaseModel):
    """Request to set magnification."""

    camera_name: str
    magnification: float


class LEDRequest(BaseModel):
    """Request to set LED brightness."""

    camera_name: str
    brightness: int


class CalibrationRequest(BaseModel):
    """Request to calibrate microscope."""

    camera_name: str
    known_distance_pixels: int
    actual_distance_mm: float


class MeasurementRequest(BaseModel):
    """Request to measure distance."""

    camera_name: str
    pixel_distance: int


class StartTimelapseRequest(BaseModel):
    """Request to start a timelapse session."""

    camera_name: str
    session_name: str
    interval_minutes: int = 10  # Every 10 minutes
    duration_hours: int = 24  # For 24 hours (adjust for multi-day)
    auto_focus: bool = True


class CreateVideoRequest(BaseModel):
    """Request to create a timelapse video."""

    session_dir: str
    output_path: Optional[str] = None
    fps: int = 30
    add_timestamp: bool = True


class AnalyzeGrowthRequest(BaseModel):
    """Request to analyze plant growth."""

    session_dir: str


async def _check_microscope_device(camera_name: str):
    """Check if microscope device exists and is available."""
    # Check if device exists via MCP
    device_status = await call_mcp_tool(
        "medical_management", {"action": "get_device_status", "device_id": camera_name}
    )

    if not device_status.get("success"):
        raise HTTPException(status_code=404, detail=f"Microscope device not found: {camera_name}")

    device_data = device_status.get("data", {})
    if device_data.get("type") != "microscope":
        raise HTTPException(
            status_code=400,
            detail=f"Device {camera_name} is not a microscope (type: {device_data.get('type')})",
        )

    return device_data


@router.post("/magnification")
async def set_magnification(request: MagnificationRequest):
    """Set microscope magnification."""
    try:
        await _check_microscope_device(request.camera_name)

        result = await call_mcp_tool(
            "medical_management",
            {
                "action": "adjust_microscope",
                "device_id": request.camera_name,
                "magnification": request.magnification,
            },
        )

        if result.get("success"):
            return {
                "success": True,
                "message": f"Set magnification to {request.magnification}x",
                "magnification": request.magnification,
            }
        raise HTTPException(status_code=500, detail="Failed to set magnification")

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to set magnification")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/led")
async def set_led_brightness(request: LEDRequest):
    """Set microscope LED brightness."""
    try:
        await _check_microscope_device(request.camera_name)

        result = await call_mcp_tool(
            "medical_management",
            {
                "action": "adjust_microscope",
                "device_id": request.camera_name,
                "led_brightness": request.brightness,
            },
        )

        if result.get("success"):
            return {
                "success": True,
                "message": f"Set LED brightness to {request.brightness}%",
                "brightness": request.brightness,
            }
        raise HTTPException(status_code=500, detail="Failed to set LED brightness")

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to set LED brightness")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/calibrate")
async def calibrate_microscope(request: CalibrationRequest):
    """Calibrate microscope for measurements."""
    try:
        await _check_microscope_device(request.camera_name)

        result = await call_mcp_tool(
            "medical_management",
            {
                "action": "calibrate_device",
                "device_id": request.camera_name,
                "known_distance_pixels": request.known_distance_pixels,
                "actual_distance_mm": request.actual_distance_mm,
            },
        )

        if result.get("success"):
            calibration_factor = request.actual_distance_mm / request.known_distance_pixels
            return {
                "success": True,
                "message": "Microscope calibrated successfully",
                "calibration_factor": calibration_factor,
                "units": "mm/pixel",
            }
        raise HTTPException(status_code=500, detail="Failed to calibrate microscope")

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to calibrate microscope")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/measure")
async def measure_distance(request: MeasurementRequest):
    """Convert pixel distance to actual distance."""
    try:
        await _check_microscope_device(request.camera_name)

        result = await call_mcp_tool(
            "medical_management",
            {
                "action": "get_readings",
                "device_id": request.camera_name,
                "measurement_type": "distance",
                "pixel_distance": request.pixel_distance,
            },
        )

        if result.get("success") and "actual_distance" in result.get("data", {}):
            actual_distance = result["data"]["actual_distance"]
            return {
                "success": True,
                "pixel_distance": request.pixel_distance,
                "actual_distance": actual_distance,
                "units": "mm",
            }
        raise HTTPException(
            status_code=500, detail="Microscope not calibrated or measurement failed"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to measure distance")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/autofocus/{camera_name}")
async def auto_focus(camera_name: str):
    """Perform auto-focus on microscope."""
    try:
        await _check_microscope_device(camera_name)

        result = await call_mcp_tool(
            "medical_management",
            {"action": "adjust_microscope", "device_id": camera_name, "focus_mode": "auto"},
        )

        if result.get("success"):
            return {"success": True, "message": "Auto-focus completed successfully"}
        return {"success": False, "message": "Auto-focus not supported or failed"}

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to auto-focus")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/info/{camera_name}")
async def get_microscope_info(camera_name: str):
    """Get detailed microscope information."""
    try:
        device_data = await _check_microscope_device(camera_name)

        return {"success": True, "camera_name": camera_name, "info": device_data}

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to get microscope info")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/timelapse/start")
async def start_timelapse(request: StartTimelapseRequest):
    """Start a timelapse photography session for plant growth monitoring."""
    try:
        await _check_microscope_device(request.camera_name)

        result = await call_mcp_tool(
            "medical_management",
            {
                "action": "start_timelapse",
                "device_id": request.camera_name,
                "session_name": request.session_name,
                "interval_minutes": request.interval_minutes,
                "duration_hours": request.duration_hours,
                "auto_focus": request.auto_focus,
            },
        )

        if result.get("success"):
            return {
                "success": True,
                "message": f"Timelapse session '{request.session_name}' started",
                "session_info": result.get("data", {}),
            }
        raise HTTPException(status_code=500, detail="Failed to start timelapse")

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to start timelapse")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/timelapse/stop/{camera_name}")
async def stop_timelapse(camera_name: str, session_name: str):
    """Stop a running timelapse session."""
    try:
        await _check_microscope_device(camera_name)

        result = await call_mcp_tool(
            "medical_management",
            {"action": "stop_timelapse", "device_id": camera_name, "session_name": session_name},
        )

        if result.get("success"):
            return {
                "success": True,
                "message": f"Timelapse session '{session_name}' stop requested",
                "result": result.get("data", {}),
            }
        raise HTTPException(status_code=500, detail="Failed to stop timelapse")

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to stop timelapse")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/timelapse/status/{camera_name}")
async def get_timelapse_status(camera_name: str):
    """Get status of timelapse sessions for a camera."""
    try:
        await _check_microscope_device(camera_name)

        result = await call_mcp_tool(
            "medical_management", {"action": "get_timelapse_status", "device_id": camera_name}
        )

        if result.get("success"):
            return {"success": True, "camera_name": camera_name, "status": result.get("data", {})}
        raise HTTPException(status_code=500, detail="Failed to get timelapse status")

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to get timelapse status")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/timelapse/video")
async def create_timelapse_video(request: CreateVideoRequest):
    """Create a time-lapse video from captured images."""
    try:
        # Find the first available microscope device
        devices_result = await call_mcp_tool("medical_management", {"action": "list_devices"})

        if not devices_result.get("success"):
            raise HTTPException(status_code=404, detail="No microscope devices found")

        microscope_device = None
        for device in devices_result.get("data", {}).get("devices", []):
            if device.get("type") == "microscope":
                microscope_device = device
                break

        if not microscope_device:
            raise HTTPException(status_code=404, detail="No microscope device available")

        result = await call_mcp_tool(
            "medical_management",
            {
                "action": "create_timelapse_video",
                "session_dir": request.session_dir,
                "output_path": request.output_path,
                "fps": request.fps,
                "add_timestamp": request.add_timestamp,
            },
        )

        if result.get("success"):
            video_path = result.get("data", {}).get("video_path", request.output_path)
            return {
                "success": True,
                "message": f"Timelapse video created: {video_path}",
                "video_path": video_path,
                "fps": request.fps,
                "timestamp_overlay": request.add_timestamp,
            }
        raise HTTPException(status_code=500, detail="Failed to create timelapse video")

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to create timelapse video")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/analyze-growth")
async def analyze_growth(request: AnalyzeGrowthRequest):
    """Analyze plant growth patterns from timelapse images."""
    try:
        # Find the first available microscope device
        devices_result = await call_mcp_tool("medical_management", {"action": "list_devices"})

        if not devices_result.get("success"):
            raise HTTPException(status_code=404, detail="No microscope devices found")

        microscope_device = None
        for device in devices_result.get("data", {}).get("devices", []):
            if device.get("type") == "microscope":
                microscope_device = device
                break

        if not microscope_device:
            raise HTTPException(status_code=404, detail="No microscope device available")

        result = await call_mcp_tool(
            "medical_management", {"action": "analyze_growth", "session_dir": request.session_dir}
        )

        if result.get("success"):
            return {
                "success": True,
                "message": f"Growth analysis completed for {request.session_dir}",
                "analysis": result.get("data", {}),
            }
        raise HTTPException(status_code=500, detail="Failed to analyze growth")

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to analyze growth")
        raise HTTPException(status_code=500, detail=str(e)) from e
