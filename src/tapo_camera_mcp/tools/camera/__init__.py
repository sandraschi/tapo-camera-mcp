"""
Camera-related tools for Tapo Camera MCP.

This module contains tools for managing and controlling Tapo cameras.
"""

from .camera_tools import (
    CameraStatus,
    ListCamerasTool,
    AddCameraTool,
    RemoveCameraTool,
    SetActiveCameraTool,
    GetCameraStatusTool
)

__all__ = [
    'CameraStatus',
    'ListCamerasTool',
    'AddCameraTool',
    'RemoveCameraTool',
    'SetActiveCameraTool',
    'GetCameraStatusTool',
    'ConnectCameraTool',
    'DisconnectCameraTool',
    'GetCameraInfoTool',
    'ManageCameraGroupsTool'
]
