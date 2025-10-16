"""
Tapo Camera MCP Utilities

This package contains utility functions and classes used throughout the application.
"""

from .camera import CameraManager
from .config import load_config, save_config
from .exceptions import (
    CameraAuthError,
    CameraConnectionError,
    CameraNotSupportedError,
    TapoCameraError,
)
from .logging import get_logger, setup_logging

__all__ = [
    "setup_logging",
    "get_logger",
    "load_config",
    "save_config",
    "CameraManager",
    "TapoCameraError",
    "CameraConnectionError",
    "CameraAuthError",
    "CameraNotSupportedError",
]
