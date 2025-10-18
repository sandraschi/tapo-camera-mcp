#!/usr/bin/env python3
"""
Tests for camera implementations (Tapo, Webcam, Ring, Furbo).
"""

import os
import sys

# Add the src path to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))


def test_base_camera():
    try:
        from tapo_camera_mcp.camera.base import CameraConfig, CameraType

        # Test CameraType enum
        list(CameraType)

        # Test CameraConfig creation
        config = CameraConfig(
            name="test_camera",
            type=CameraType.TAPO,
        )

        assert config.name == "test_camera"
        assert config.type == CameraType.TAPO
        assert config.enabled is True

        return True
    except Exception:
        import traceback

        traceback.print_exc()
        return False


def test_tapo_camera():
    """Test Tapo camera implementation."""
    try:
        from tapo_camera_mcp.camera.tapo import TapoCamera
        from tapo_camera_mcp.core.models import TapoCameraConfig

        # Test TapoCameraConfig creation
        TapoCameraConfig(
            host="192.168.1.100", username="test_user", password="test_pass", port=443
        )


        # Test that TapoCamera class exists and has required methods
        assert hasattr(TapoCamera, "__init__"), "TapoCamera should have __init__"
        assert hasattr(TapoCamera, "connect"), "TapoCamera should have connect method"
        assert hasattr(TapoCamera, "get_status"), "TapoCamera should have get_status method"

        return True
    except Exception:
        import traceback

        traceback.print_exc()
        return False


def test_webcam_camera():
    """Test webcam camera implementation."""
    try:
        from tapo_camera_mcp.camera.webcam import WebCamera

        # Test that WebCamera class exists and has required methods
        assert hasattr(WebCamera, "__init__"), "WebCamera should have __init__"
        assert hasattr(WebCamera, "connect"), "WebCamera should have connect method"
        assert hasattr(WebCamera, "start_stream"), "WebCamera should have start_stream method"
        assert hasattr(WebCamera, "get_status"), "WebCamera should have get_status method"

        return True
    except Exception:
        import traceback

        traceback.print_exc()
        return False


def test_camera_manager():
    """Test camera manager functionality."""
    try:
        from tapo_camera_mcp.camera.base import CameraConfig, CameraType
        from tapo_camera_mcp.camera.manager import CameraManager

        # Test CameraManager creation
        manager = CameraManager()
        assert hasattr(manager, "cameras"), "CameraManager should have cameras dict"
        assert hasattr(manager, "groups"), "CameraManager should have groups"

        # Test that cameras dict is initially empty
        assert len(manager.cameras) == 0, "CameraManager should start with no cameras"

        # Test adding camera config (without actual connection)
        CameraConfig(
            name="test_camera", type=CameraType.TAPO, params={"host": "192.168.1.100"}
        )

        # Note: We can't actually add cameras without proper setup, but we can test the structure
        return True
    except Exception:
        import traceback

        traceback.print_exc()
        return False


def test_camera_groups():
    """Test camera groups functionality."""
    try:
        from tapo_camera_mcp.camera.groups import CameraGroupManager

        # Test CameraGroupManager creation
        group_manager = CameraGroupManager()
        assert hasattr(group_manager, "groups"), "CameraGroupManager should have groups"

        return True
    except Exception:
        import traceback

        traceback.print_exc()
        return False


def test_camera_factory():
    """Test camera factory pattern."""
    try:
        from tapo_camera_mcp.camera.base import CameraFactory

        # Test that CameraFactory exists
        assert hasattr(CameraFactory, "create_camera"), (
            "CameraFactory should have create_camera method"
        )

        return True
    except Exception:
        import traceback

        traceback.print_exc()
        return False


def test_camera_exceptions():
    """Test camera exception classes."""
    try:
        from tapo_camera_mcp.exceptions import (
            AuthenticationError,
            CameraNotFoundError,
            ConnectionError,
            StreamError,
            TapoCameraError,
        )

        # Test exception creation
        error = TapoCameraError("Test error")
        connection_error = ConnectionError("Connection failed")
        AuthenticationError("Auth failed")
        CameraNotFoundError("Camera not found")
        StreamError("Stream failed")

        # Test exception hierarchy
        assert isinstance(error, Exception), "TapoCameraError should be Exception"
        assert isinstance(connection_error, TapoCameraError), (
            "ConnectionError should inherit from TapoCameraError"
        )

        return True
    except Exception:
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    tests = [
        test_base_camera,
        test_tapo_camera,
        test_webcam_camera,
        test_camera_manager,
        test_camera_groups,
        test_camera_factory,
        test_camera_exceptions,
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
