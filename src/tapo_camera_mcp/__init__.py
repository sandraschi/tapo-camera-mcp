"""
Tapo-Camera-MCP - A FastMCP 2.10 server for controlling TP-Link Tapo cameras.

This package provides a FastMCP 2.10 compliant server for interacting with
TP-Link Tapo cameras, including features like live streaming, PTZ control,
motion detection, and more.
"""

__version__ = "0.1.0"
__author__ = "Your Name <your.email@example.com>"
__license__ = "MIT"

# Import core components
from .server import TapoCameraMCP  # noqa: F401
from .exceptions import TapoCameraError  # noqa: F401
from .models import CameraConfig  # noqa: F401

# Define public API
__all__ = ["TapoCameraMCP", "TapoCameraError", "CameraConfig"]
