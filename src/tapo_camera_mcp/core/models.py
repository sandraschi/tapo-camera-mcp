"""
Core data models for Tapo-Camera-MCP.
"""
from enum import Enum
from typing import Dict, List, Optional, Union
from pydantic import BaseModel, Field, HttpUrl, IPvAnyAddress, field_validator

class CameraModel(str, Enum):
    """Supported Tapo camera models."""
    C100 = "Tapo C100"
    C110 = "Tapo C110"
    C200 = "Tapo C200"
    C210 = "Tapo C210"
    C310 = "Tapo C310"

class StreamType(str, Enum):
    """Supported stream types."""
    RTSP = "rtsp"
    RTMP = "rtmp"
    HLS = "hls"

class VideoQuality(str, Enum):
    """Video quality presets."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class PTZDirection(str, Enum):
    """PTZ movement directions."""
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"
    STOP = "stop"

class MotionDetectionSensitivity(str, Enum):
    """Motion detection sensitivity levels."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    OFF = "off"

class CameraStatus(BaseModel):
    """Current status of the camera."""
    online: bool = Field(..., description="Whether the camera is online")
    recording: bool = Field(False, description="Whether the camera is currently recording")
    motion_detected: bool = Field(False, description="Whether motion is currently detected")
    audio_detected: bool = Field(False, description="Whether audio is currently detected")
    privacy_mode: bool = Field(False, description="Whether privacy mode is enabled")
    led_enabled: bool = Field(True, description="Whether the status LED is enabled")
    firmware_version: str = Field(..., description="Camera firmware version")
    uptime: int = Field(0, description="Uptime in seconds")
    storage: Dict[str, Union[int, str]] = Field(default_factory=dict, 
                                             description="Storage information")

class PTZPosition(BaseModel):
    """PTZ position coordinates."""
    pan: float = Field(0.0, ge=-1.0, le=1.0, description="Pan position (-1.0 to 1.0)")
    tilt: float = Field(0.0, ge=-1.0, le=1.0, description="Tilt position (-1.0 to 1.0)")
    zoom: float = Field(0.0, ge=0.0, le=1.0, description="Zoom level (0.0 to 1.0)")

class MotionEvent(BaseModel):
    """Motion detection event."""
    timestamp: float = Field(..., description="Event timestamp")
    confidence: float = Field(..., description="Detection confidence (0.0 to 1.0)")
    zones: List[Dict] = Field(default_factory=list, description="Triggered zones")
    snapshot_url: Optional[HttpUrl] = Field(None, description="URL to snapshot of the event")
    video_clip_url: Optional[HttpUrl] = Field(None, description="URL to video clip of the event")

class CameraInfo(BaseModel):
    """Camera device information."""
    model: CameraModel
    serial_number: str
    mac_address: str
    firmware_version: str
    hardware_version: str
    uptime: int
    ip_address: IPvAnyAddress
    wifi_signal: int = Field(ge=0, le=100, description="WiFi signal strength (0-100)")
    wifi_ssid: Optional[str] = Field(None, description="Connected WiFi SSID")
