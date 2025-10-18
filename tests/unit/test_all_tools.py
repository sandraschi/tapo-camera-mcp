#!/usr/bin/env python3
"""
Comprehensive tests for all camera tools.
"""

import asyncio
import os
import sys
from unittest import mock

# Add the src path to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))


def test_list_cameras_tool():
    """Test ListCamerasTool functionality."""
    try:
        from tapo_camera_mcp.tools.base_tool import ToolResult
        from tapo_camera_mcp.tools.camera.camera_tools import ListCamerasTool

        # Create tool instance
        tool = ListCamerasTool()

        # Test that tool has required attributes
        assert hasattr(tool, "Meta")
        assert hasattr(tool.Meta, "name")
        assert hasattr(tool.Meta, "category")
        assert tool.Meta.name == "list_cameras"
        assert tool.Meta.category.value == "Camera"

        # Mock server and camera manager
        with mock.patch(
            "tapo_camera_mcp.tools.camera.camera_tools.TapoCameraServer"
        ) as mock_server_class:
            mock_server_instance = mock.AsyncMock()
            mock_camera_manager = mock.AsyncMock()
            mock_camera_manager.cameras = {
                "camera1": mock.MagicMock(),
                "camera2": mock.MagicMock(),
            }
            mock_server_instance.camera_manager = mock_camera_manager
            mock_server_class.get_instance.return_value = mock_server_instance

            # Test tool execution
            result = asyncio.run(tool.execute())

            # Should return ToolResult
            assert isinstance(result, ToolResult)
            assert not result.is_error

            # Should have called the server
            mock_server_class.get_instance.assert_called_once()

            return True
    except Exception:
        import traceback

        traceback.print_exc()
        return False


def test_add_camera_tool():
    """Test AddCameraTool functionality."""
    try:
        from tapo_camera_mcp.tools.base_tool import ToolResult
        from tapo_camera_mcp.tools.camera.camera_tools import AddCameraTool

        # Create tool instance
        tool = AddCameraTool(
            camera_name="test_camera",
            ip_address="192.168.1.100",
            username="test_user",
            password="test_pass",
            stream_url="rtsp://test.url",
        )

        # Test that tool has required attributes
        assert hasattr(tool, "Meta")
        assert hasattr(tool.Meta, "name")
        assert tool.Meta.name == "add_camera"

        # Mock server and validation functions
        with mock.patch(
            "tapo_camera_mcp.tools.camera.camera_tools.TapoCameraServer"
        ) as mock_server_class, mock.patch(
            "tapo_camera_mcp.tools.camera.camera_tools.validate_camera_name"
        ) as mock_validate_name, mock.patch(
            "tapo_camera_mcp.tools.camera.camera_tools.validate_ip_address"
        ) as mock_validate_ip, mock.patch(
            "tapo_camera_mcp.tools.camera.camera_tools.validate_credentials"
        ) as mock_validate_creds:
            mock_validate_name.return_value = "test_camera"
            mock_validate_ip.return_value = "192.168.1.100"
            mock_validate_creds.return_value = ("test_user", "test_pass")

            mock_server_instance = mock.AsyncMock()
            mock_server_instance.add_camera.return_value = {"success": True}
            mock_server_class.get_instance.return_value = mock_server_instance

            # Test tool execution
            result = asyncio.run(tool.execute())

            # Should return ToolResult
            assert isinstance(result, ToolResult)
            assert not result.is_error

            return True
    except Exception:
        import traceback

        traceback.print_exc()
        return False


def test_connect_camera_tool():
    """Test ConnectCameraTool functionality."""
    try:
        from tapo_camera_mcp.tools.base_tool import ToolResult
        from tapo_camera_mcp.tools.camera.camera_tools import ConnectCameraTool

        # Create tool instance
        tool = ConnectCameraTool(
            host="192.168.1.100",
            username="test_user",
            password="test_pass",
            verify_ssl=False,
        )

        # Test that tool has required attributes
        assert hasattr(tool, "Meta")
        assert hasattr(tool.Meta, "name")
        assert tool.Meta.name == "connect_camera"

        # Mock server and validation functions
        with mock.patch(
            "tapo_camera_mcp.tools.camera.camera_tools.TapoCameraServer"
        ) as mock_server_class, mock.patch(
            "tapo_camera_mcp.tools.camera.camera_tools.validate_ip_address"
        ) as mock_validate_ip, mock.patch(
            "tapo_camera_mcp.tools.camera.camera_tools.validate_credentials"
        ) as mock_validate_creds:
            mock_validate_ip.return_value = "192.168.1.100"
            mock_validate_creds.return_value = ("test_user", "test_pass")

            mock_server_instance = mock.AsyncMock()
            mock_server_instance.connect_camera.return_value = {"success": True}
            mock_server_class.get_instance.return_value = mock_server_instance

            # Test tool execution
            result = asyncio.run(tool.execute())

            # Should return ToolResult
            assert isinstance(result, ToolResult)
            assert not result.is_error

            return True
    except Exception:
        import traceback

        traceback.print_exc()
        return False


def test_disconnect_camera_tool():
    """Test DisconnectCameraTool functionality."""
    try:
        from tapo_camera_mcp.tools.base_tool import ToolResult
        from tapo_camera_mcp.tools.camera.camera_tools import DisconnectCameraTool

        # Create tool instance
        tool = DisconnectCameraTool(camera_id="test_camera")

        # Test that tool has required attributes
        assert hasattr(tool, "Meta")
        assert hasattr(tool.Meta, "name")
        assert tool.Meta.name == "disconnect_camera"

        # Mock server
        with mock.patch(
            "tapo_camera_mcp.tools.camera.camera_tools.TapoCameraServer"
        ) as mock_server_class:
            mock_server_instance = mock.AsyncMock()
            mock_server_instance.disconnect_camera.return_value = {"success": True}
            mock_server_class.get_instance.return_value = mock_server_instance

            # Test tool execution
            result = asyncio.run(tool.execute())

            # Should return ToolResult
            assert isinstance(result, ToolResult)
            assert not result.is_error

            return True
    except Exception:
        import traceback

        traceback.print_exc()
        return False


def test_get_camera_status_tool():
    """Test GetCameraStatusTool functionality."""
    try:
        from tapo_camera_mcp.tools.base_tool import ToolResult
        from tapo_camera_mcp.tools.camera.camera_tools import GetCameraStatusTool

        # Create tool instance
        tool = GetCameraStatusTool(camera_id="test_camera")

        # Test that tool has required attributes
        assert hasattr(tool, "Meta")
        assert hasattr(tool.Meta, "name")
        assert tool.Meta.name == "get_camera_status"

        # Mock server
        with mock.patch(
            "tapo_camera_mcp.tools.camera.camera_tools.TapoCameraServer"
        ) as mock_server_class:
            mock_server_instance = mock.AsyncMock()
            mock_server_instance.get_camera_status.return_value = {
                "online": True,
                "recording": False,
            }
            mock_server_class.get_instance.return_value = mock_server_instance

            # Test tool execution
            result = asyncio.run(tool.execute())

            # Should return ToolResult
            assert isinstance(result, ToolResult)
            assert not result.is_error

            return True
    except Exception:
        import traceback

        traceback.print_exc()
        return False


def test_capture_snapshot_tool():
    """Test CaptureSnapshotTool functionality."""
    try:
        from tapo_camera_mcp.tools.base_tool import ToolResult
        from tapo_camera_mcp.tools.camera.camera_tools import CaptureSnapshotTool

        # Create tool instance
        tool = CaptureSnapshotTool(camera_id="test_camera")

        # Test that tool has required attributes
        assert hasattr(tool, "Meta")
        assert hasattr(tool.Meta, "name")
        assert tool.Meta.name == "capture_snapshot"

        # Mock server and camera
        with mock.patch(
            "tapo_camera_mcp.tools.camera.camera_tools.TapoCameraServer"
        ) as mock_server_class:
            mock_server_instance = mock.AsyncMock()
            mock_camera_manager = mock.AsyncMock()
            mock_camera = mock.AsyncMock()
            mock_camera.capture_still.return_value = mock.MagicMock()  # Mock PIL Image
            mock_camera_manager.cameras = {"test_camera": mock_camera}
            mock_server_instance.camera_manager = mock_camera_manager
            mock_server_class.get_instance.return_value = mock_server_instance

            # Test tool execution
            result = asyncio.run(tool.execute())

            # Should return ToolResult
            assert isinstance(result, ToolResult)
            assert not result.is_error

            return True
    except Exception:
        import traceback

        traceback.print_exc()
        return False


def test_get_stream_url_tool():
    """Test GetStreamUrlTool functionality."""
    try:
        from tapo_camera_mcp.tools.base_tool import ToolResult
        from tapo_camera_mcp.tools.camera.camera_tools import GetStreamUrlTool

        # Create tool instance
        tool = GetStreamUrlTool(camera_id="test_camera")

        # Test that tool has required attributes
        assert hasattr(tool, "Meta")
        assert hasattr(tool.Meta, "name")
        assert tool.Meta.name == "get_stream_url"

        # Mock server and camera
        with mock.patch(
            "tapo_camera_mcp.tools.camera.camera_tools.TapoCameraServer"
        ) as mock_server_class:
            mock_server_instance = mock.AsyncMock()
            mock_camera_manager = mock.AsyncMock()
            mock_camera = mock.AsyncMock()
            mock_camera.get_stream_url.return_value = "rtsp://test.url"
            mock_camera_manager.cameras = {"test_camera": mock_camera}
            mock_server_instance.camera_manager = mock_camera_manager
            mock_server_class.get_instance.return_value = mock_server_instance

            # Test tool execution
            result = asyncio.run(tool.execute())

            # Should return ToolResult
            assert isinstance(result, ToolResult)
            assert not result.is_error

            return True
    except Exception:
        import traceback

        traceback.print_exc()
        return False


def test_ptz_tools():
    """Test PTZ tools functionality."""
    try:
        # Check if PTZ tools exist
        try:
            from tapo_camera_mcp.tools.ptz.ptz_tools import (
                GetCameraPresetsTool,
                PTZControlTool,
                SetCameraPresetTool,
            )
        except ImportError:
            return True

        # Test SetCameraPresetTool
        tool = SetCameraPresetTool(
            camera_id="test_camera", preset_name="home", position_x=0.0, position_y=0.0
        )
        assert hasattr(tool, "Meta")
        assert tool.Meta.name == "set_camera_preset"

        # Test GetCameraPresetsTool
        tool = GetCameraPresetsTool(camera_id="test_camera")
        assert hasattr(tool, "Meta")
        assert tool.Meta.name == "get_camera_presets"

        # Test PTZControlTool
        tool = PTZControlTool(camera_id="test_camera", direction="up", duration=1.0)
        assert hasattr(tool, "Meta")
        assert tool.Meta.name == "ptz_control"

        return True
    except Exception:
        import traceback

        traceback.print_exc()
        return False


def test_system_tools():
    """Test system tools functionality."""
    try:
        from tapo_camera_mcp.tools.system.help_tool import HelpTool
        from tapo_camera_mcp.tools.system.status_tool import StatusTool

        # Test StatusTool
        tool = StatusTool(section="system")
        assert hasattr(tool, "Meta")
        assert tool.Meta.name == "status"

        # Test HelpTool
        tool = HelpTool(section="tools")
        assert hasattr(tool, "Meta")
        assert tool.Meta.name == "help"

        return True
    except Exception:
        import traceback

        traceback.print_exc()
        return False


def test_all_tools_metadata():
    """Test that all tools have proper metadata."""
    try:
        from tapo_camera_mcp.tools.discovery import discover_tools

        # Discover all tools
        all_tools = discover_tools("tapo_camera_mcp.tools")

        # Test that all tools have proper metadata
        for tool_cls in all_tools:
            assert hasattr(tool_cls, "Meta"), f"Tool {tool_cls.__name__} missing Meta class"
            meta = tool_cls.Meta

            # Required metadata
            assert hasattr(meta, "name"), f"Tool {tool_cls.__name__} missing name"
            assert hasattr(meta, "category"), f"Tool {tool_cls.__name__} missing category"

            # Name should be valid
            assert isinstance(meta.name, str), f"Tool {tool_cls.__name__} name should be string"
            assert len(meta.name) > 0, f"Tool {tool_cls.__name__} name should not be empty"

            # Category should be valid
            from tapo_camera_mcp.tools.base_tool import ToolCategory

            assert isinstance(meta.category, ToolCategory), (
                f"Tool {tool_cls.__name__} category should be ToolCategory"
            )

            # Tool should have execute method
            assert hasattr(tool_cls, "execute"), f"Tool {tool_cls.__name__} missing execute method"
            assert callable(tool_cls.execute), (
                f"Tool {tool_cls.__name__} execute should be callable"
            )

        return True
    except Exception:
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    tests = [
        test_list_cameras_tool,
        test_add_camera_tool,
        test_connect_camera_tool,
        test_disconnect_camera_tool,
        test_get_camera_status_tool,
        test_capture_snapshot_tool,
        test_get_stream_url_tool,
        test_ptz_tools,
        test_system_tools,
        test_all_tools_metadata,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1


    if passed == total:
        sys.exit(0)
    else:
        sys.exit(1)
