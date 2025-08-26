"""
Tapo-Camera-MCP - A FastMCP 2.10 server for controlling TP-Link Tapo cameras.

This package provides a FastMCP 2.10 compliant server for interacting with
TP-Link Tapo cameras, including features like live streaming, PTZ control,
motion detection, image capture, and multimodal analysis.
"""

__version__ = "0.4.0"
__author__ = "Tapo Camera MCP Team <tapo-camera-mcp@example.com>"
__license__ = "MIT"

# Import core components
from .server_v2 import TapoCameraServer  # noqa: F401
from .web_server import TapoWebServer  # noqa: F401
from .exceptions import TapoCameraError  # noqa: F401
from .models import CameraConfig  # noqa: F401
from . import presets  # noqa: F401

# Define public API
__all__ = [
    "TapoCameraServer", 
    "TapoWebServer",
    "TapoCameraError", 
    "CameraConfig",
    "presets"
]
