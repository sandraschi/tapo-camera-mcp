"""
Camera-related tools for Tapo Camera MCP.

This module contains tools for managing and controlling Tapo cameras.
"""

from .camera_tools import (
    AddCameraTool,
    CameraStatus,
    ConnectCameraTool,
    DisconnectCameraTool,
    GetCameraInfoTool,
    GetCameraStatusTool,
    ListCamerasTool,
    ManageCameraGroupsTool,
    RemoveCameraTool,
    SetActiveCameraTool,
)

# Export all tools for discovery
__all__ = [
    "AddCameraTool",
    "CameraStatus",
    "ConnectCameraTool",
    "DisconnectCameraTool",
    "GetCameraInfoTool",
    "GetCameraStatusTool",
    "ListCamerasTool",
    "ManageCameraGroupsTool",
    "RemoveCameraTool",
    "SetActiveCameraTool",
]

# This ensures the tools are registered when the module is imported
from .. import register_tool

for tool in [
    ListCamerasTool,
    AddCameraTool,
    RemoveCameraTool,
    SetActiveCameraTool,
    GetCameraStatusTool,
    ConnectCameraTool,
    DisconnectCameraTool,
    GetCameraInfoTool,
    ManageCameraGroupsTool,
]:
    register_tool(tool)
