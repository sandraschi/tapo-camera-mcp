"""
System tools for Tapo Camera MCP.

This module contains system-level tools for managing the camera.
"""

from tapo_camera_mcp.tools.system.system_tools import (
    GetSystemInfoTool,
    RebootCameraTool,
    GetLogsTool,
    GetHelpTool,
    SetMotionDetectionTool,
    SetLEDEnabledTool,
    SetPrivacyModeTool,
    HelpTool
)

__all__ = [
    'GetSystemInfoTool',
    'RebootCameraTool',
    'GetLogsTool',
    'GetHelpTool',
    'SetMotionDetectionTool',
    'SetLEDEnabledTool',
    'SetPrivacyModeTool',
    'HelpTool'
]
