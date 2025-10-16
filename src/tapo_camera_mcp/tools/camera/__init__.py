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
    GetCameraStatusTool,
    ConnectCameraTool,
    DisconnectCameraTool,
    GetCameraInfoTool,
    ManageCameraGroupsTool,
)

# Export all tools for discovery
__all__ = [
    "CameraStatus",
    "ListCamerasTool",
    "AddCameraTool",
    "RemoveCameraTool",
    "SetActiveCameraTool",
    "GetCameraStatusTool",
    "ConnectCameraTool",
    "DisconnectCameraTool",
    "GetCameraInfoTool",
    "ManageCameraGroupsTool",
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
