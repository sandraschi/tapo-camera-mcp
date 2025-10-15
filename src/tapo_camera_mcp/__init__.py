"""
Tapo-Camera-MCP - A FastMCP 2.12+ server for controlling TP-Link Tapo cameras.

This package provides a FastMCP 2.12+ compliant server for interacting with
TP-Link Tapo cameras, including features like live streaming, PTZ control,
motion detection, image capture, and multimodal analysis.
"""

__version__ = "1.1.0"
__author__ = "Tapo Camera MCP Team <tapo-camera-mcp@example.com>"
__license__ = "MIT"

# Import core components
from .core import (
    TapoCameraServer,
    get_server,
    CameraModel,
    StreamType,
    VideoQuality,
    PTZDirection,
    MotionDetectionSensitivity,
    CameraStatus,
    PTZPosition,
    MotionEvent,
    CameraInfo
)

from .exceptions import TapoCameraError
from . import presets

# For backward compatibility
from .core.server import TapoCameraServer as Server  # noqa: F401
from .core.server import TapoCameraServer as TapoCameraMCP  # noqa: F401
__all__ = [
    # Core components
    "TapoCameraServer",
    "TapoCameraMCP",  # For backward compatibility
    "get_server",
    "TapoWebServer",
    "TapoCameraError",
    "presets",
    
    # Models
    "CameraModel",
    "StreamType",
    "VideoQuality",
    "PTZDirection",
    "MotionDetectionSensitivity",
    "CameraStatus",
    "PTZPosition",
    "MotionEvent",
    "CameraInfo"
]
