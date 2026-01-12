"""
PTZ Control API Endpoints

Provides RESTful API endpoints for PTZ camera control and preset management.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from ...tools.ptz.preset_manager import PTZPresetManager
from ...tools.ptz.ptz_models import PTZMoveDirection, PTZPosition, PTZSpeed

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/cameras/{camera_id}/ptz", tags=["PTZ Control"])


def get_camera_client() -> Any:
    """Dependency to get camera client - placeholder implementation."""
    return None


# In-memory storage for demo purposes
# In production, you'd use a database
ptz_managers: Dict[str, PTZPresetManager] = {}


class PTZMoveRequest(BaseModel):
    """Request model for PTZ movement"""

    direction: PTZMoveDirection
    speed: PTZSpeed = PTZSpeed.MEDIUM
    duration_ms: int = Field(1000, ge=100, le=10000, description="Duration in milliseconds")


class PTZZoomRequest(BaseModel):
    """Request model for PTZ zoom"""

    direction: str = Field(..., regex="^(in|out)$")
    speed: PTZSpeed = PTZSpeed.MEDIUM


class PTZStopRequest(BaseModel):
    """Request model to stop all PTZ movement"""


class PTZPresetCreate(BaseModel):
    """Request model for creating a PTZ preset"""

    name: str
    description: Optional[str] = None
    position: Optional[PTZPosition] = None  # If None, use current position


class PTZPresetUpdate(BaseModel):
    """Request model for updating a PTZ preset"""

    name: Optional[str] = None
    description: Optional[str] = None
    position: Optional[PTZPosition] = None


class PTZPresetResponse(PTZPresetCreate):
    """Response model for PTZ preset"""

    preset_id: int
    created_at: datetime
    updated_at: datetime
    thumbnail_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


@router.post("/move", status_code=status.HTTP_202_ACCEPTED)
async def move_ptz(
    camera_id: str,
    move_request: PTZMoveRequest,
    _camera_client: Any = Depends(get_camera_client),
):
    """
    Move the PTZ camera in the specified direction

    - **direction**: Direction to move (up, down, left, right, up_left, up_right, down_left, down_right)
    - **speed**: Movement speed (SLOW, MEDIUM, FAST)
    - **duration_ms**: How long to move in milliseconds (100-10000)
    """
    try:
        # This would be an actual API call to the camera
        return {
            "status": "success",
            "message": f"Moving camera {camera_id} {move_request.direction}",
        }
    except Exception as e:
        logger.exception("Failed to move PTZ")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/zoom", status_code=status.HTTP_202_ACCEPTED)
async def zoom_ptz(
    _camera_id: str,
    zoom_request: PTZZoomRequest,
    _camera_client: Any = Depends(get_camera_client),
):
    """
    Zoom the camera in or out

    - **direction**: 'in' to zoom in, 'out' to zoom out
    - **speed**: Zoom speed (SLOW, MEDIUM, FAST)
    """
    try:
        # This would be an actual API call to the camera
        return {"status": "success", "message": f"Zooming {zoom_request.direction}"}
    except Exception as e:
        logger.exception("Failed to zoom")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/stop", status_code=status.HTTP_202_ACCEPTED)
async def stop_ptz(_camera_id: str, _camera_client: Any = Depends(get_camera_client)):
    """Stop all PTZ movement"""
    try:
        return {"status": "success", "message": "PTZ movement stopped"}
    except Exception as e:
        logger.exception("Failed to stop PTZ")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/presets", response_model=List[PTZPresetResponse])
async def list_presets(camera_id: str, camera_client: Any = Depends(get_camera_client)):
    """List all PTZ presets for the camera"""
    try:
        if camera_id not in ptz_managers:
            ptz_managers[camera_id] = PTZPresetManager(camera_client)
        return ptz_managers[camera_id].get_presets()
    except Exception as e:
        logger.exception("Failed to list PTZ presets")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/presets", status_code=status.HTTP_201_CREATED, response_model=PTZPresetResponse)
async def create_preset(
    camera_id: str,
    preset_data: PTZPresetCreate,
    camera_client: Any = Depends(get_camera_client),
):
    """Create a new PTZ preset"""
    try:
        if camera_id not in ptz_managers:
            ptz_managers[camera_id] = PTZPresetManager(camera_client)

        # If position is not provided, use current position
        position = preset_data.position
        if position is None:
            position = PTZPosition(pan=0, tilt=0, zoom=0)  # Default for demo

        return await ptz_managers[camera_id].save_preset(
            name=preset_data.name,
            position=position,
            description=preset_data.description,
        )
    except Exception as e:
        logger.exception("Failed to create PTZ preset")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/presets/{preset_id}", response_model=PTZPresetResponse)
async def get_preset(
    camera_id: str, preset_id: int, _camera_client: Any = Depends(get_camera_client)
):
    """Get details of a specific PTZ preset"""
    try:
        if camera_id not in ptz_managers:
            raise HTTPException(status_code=404, detail="No presets found for this camera")

        preset = ptz_managers[camera_id].get_preset(preset_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to get PTZ preset")
        raise HTTPException(status_code=500, detail=str(e)) from e
    else:
        if not preset:
            raise HTTPException(status_code=404, detail=f"Preset {preset_id} not found")

        return preset


@router.put("/presets/{preset_id}", response_model=PTZPresetResponse)
async def update_preset(
    camera_id: str,
    preset_id: int,
    preset_data: PTZPresetUpdate,
    _camera_client: Any = Depends(get_camera_client),
):
    """Update an existing PTZ preset"""
    try:
        if camera_id not in ptz_managers:
            raise HTTPException(status_code=404, detail="No presets found for this camera")

        # If position is provided, use it; otherwise, keep existing position
        position = preset_data.position
        if position is None:
            position = PTZPosition(pan=0, tilt=0, zoom=0)  # Default for demo

        updated_preset = await ptz_managers[camera_id].update_preset(
            preset_id=preset_id,
            name=preset_data.name,
            position=position,
            description=preset_data.description,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to update PTZ preset")
        raise HTTPException(status_code=500, detail=str(e)) from e
    else:
        if not updated_preset:
            raise HTTPException(status_code=404, detail=f"Preset {preset_id} not found")

        return updated_preset


@router.delete("/presets/{preset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_preset(
    camera_id: str, preset_id: int, _camera_client: Any = Depends(get_camera_client)
):
    """Delete a PTZ preset"""
    try:
        if camera_id not in ptz_managers:
            raise HTTPException(status_code=404, detail="No presets found for this camera")

        success = await ptz_managers[camera_id].delete_preset(preset_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to delete PTZ preset")
        raise HTTPException(status_code=500, detail=str(e)) from e
    else:
        if not success:
            raise HTTPException(status_code=404, detail=f"Preset {preset_id} not found")

        return


@router.post("/presets/{preset_id}/recall", status_code=status.HTTP_202_ACCEPTED)
async def recall_preset(
    camera_id: str, preset_id: int, _camera_client: Any = Depends(get_camera_client)
):
    """Move the camera to a saved preset position"""
    try:
        if camera_id not in ptz_managers:
            raise HTTPException(status_code=404, detail="No presets found for this camera")

        success = await ptz_managers[camera_id].recall_preset(preset_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to recall PTZ preset")
        raise HTTPException(status_code=500, detail=str(e)) from e
    else:
        if not success:
            raise HTTPException(status_code=404, detail=f"Preset {preset_id} not found")

        return {"status": "success", "message": f"Recalling preset {preset_id}"}


# Helper function to get camera client (would be implemented in your auth/dependency system)
async def get_camera_client(camera_id: str):
    """Get camera client for the given camera ID"""
    # In a real implementation, this would get an authenticated camera client
    # For now, we'll just return a mock
    return {"id": camera_id, "type": "tapo"}
