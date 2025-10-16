"""
Tapo-Camera-MCP - A FastMCP 2.12+ server for controlling TP-Link Tapo cameras.

This package provides a FastMCP 2.12+ compliant server for interacting with
TP-Link Tapo cameras, including features like live streaming, PTZ control,
motion detection, image capture, and multimodal analysis.
"""

__version__ = "1.1.0"
__author__ = "Tapo Camera MCP Team <tapo-camera-mcp@example.com>"
__license__ = "MIT"

from . import presets

# Import core components
from .core import (
    CameraInfo,
    CameraModel,
    CameraStatus,
    MotionDetectionSensitivity,
    MotionEvent,
    PTZDirection,
    PTZPosition,
    StreamType,
    TapoCameraServer,
    VideoQuality,
    get_server,
)

# For backward compatibility
from .core.server import TapoCameraServer as Server
from .core.server import TapoCameraServer as TapoCameraMCP
from .exceptions import TapoCameraError

__all__ = [
    "CameraInfo",
    # Models
    "CameraModel",
    "CameraStatus",
    "MotionDetectionSensitivity",
    "MotionEvent",
    "PTZDirection",
    "PTZPosition",
    "StreamType",
    "TapoCameraError",
    "TapoCameraMCP",  # For backward compatibility
    # Core components
    "TapoCameraServer",
    "TapoWebServer",
    "VideoQuality",
    "get_server",
    "presets",
]
