#!/usr/bin/env python3
"""
Tests for camera implementations (Tapo, Webcam, Ring, Furbo).
"""

import sys
import os

# Add the src path to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))


def test_base_camera():
    try:
        from tapo_camera_mcp.camera.base import CameraConfig, CameraType

        # Test CameraType enum
        camera_types = list(CameraType)
        print(
            f"✅ RingCamera not available, skipping test. Available camera types: {[ct.value for ct in camera_types]}"
        )

        # Test CameraConfig creation
        config = CameraConfig(
            name="test_camera",
            type=CameraType.TAPO,
        )

        assert config.name == "test_camera"
        assert config.type == CameraType.TAPO
        assert config.enabled is True

        print("✅ Base camera configuration test passed")
        return True
    except Exception as e:
        print(f"❌ Base camera test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_tapo_camera():
    """Test Tapo camera implementation."""
    try:
        from tapo_camera_mcp.camera.tapo import TapoCamera
        from tapo_camera_mcp.core.models import TapoCameraConfig

        # Test TapoCameraConfig creation
        config = TapoCameraConfig(
            host="192.168.1.100", username="test_user", password="test_pass", port=443
        )

        print("✅ TapoCameraConfig created successfully")

        # Test that TapoCamera class exists and has required methods
        assert hasattr(TapoCamera, "__init__"), "TapoCamera should have __init__"
        assert hasattr(TapoCamera, "connect"), "TapoCamera should have connect method"
        assert hasattr(TapoCamera, "get_status"), (
            "TapoCamera should have get_status method"
        )

        print("✅ TapoCamera class structure test passed")
        return True
    except Exception as e:
        print(f"❌ Tapo camera test failed: {e}")
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
        assert hasattr(WebCamera, "start_stream"), (
            "WebCamera should have start_stream method"
        )
        assert hasattr(WebCamera, "get_status"), (
            "WebCamera should have get_status method"
        )

        print("✅ WebCamera class structure test passed")
        return True
    except Exception as e:
        print(f"❌ Webcam camera test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_camera_manager():
    """Test camera manager functionality."""
    try:
        from tapo_camera_mcp.camera.manager import CameraManager
        from tapo_camera_mcp.camera.base import CameraConfig, CameraType

        # Test CameraManager creation
        manager = CameraManager()
        assert hasattr(manager, "cameras"), "CameraManager should have cameras dict"
        assert hasattr(manager, "groups"), "CameraManager should have groups"

        # Test that cameras dict is initially empty
        assert len(manager.cameras) == 0, "CameraManager should start with no cameras"

        # Test adding camera config (without actual connection)
        config = CameraConfig(
            name="test_camera", type=CameraType.TAPO, params={"host": "192.168.1.100"}
        )

        # Note: We can't actually add cameras without proper setup, but we can test the structure
        print("✅ CameraManager structure test passed")
        return True
    except Exception as e:
        print(f"❌ Camera manager test failed: {e}")
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

        print("✅ Camera groups structure test passed")
        return True
    except Exception as e:
        print(f"❌ Camera groups test failed: {e}")
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

        print("✅ Camera factory structure test passed")
        return True
    except Exception as e:
        print(f"❌ Camera factory test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_camera_exceptions():
    """Test camera exception classes."""
    try:
        from tapo_camera_mcp.exceptions import (
            TapoCameraError,
            ConnectionError,
            AuthenticationError,
            CameraNotFoundError,
            StreamError,
        )

        # Test exception creation
        error = TapoCameraError("Test error")
        connection_error = ConnectionError("Connection failed")
        auth_error = AuthenticationError("Auth failed")
        not_found_error = CameraNotFoundError("Camera not found")
        stream_error = StreamError("Stream failed")

        # Test exception hierarchy
        assert isinstance(error, Exception), "TapoCameraError should be Exception"
        assert isinstance(connection_error, TapoCameraError), (
            "ConnectionError should inherit from TapoCameraError"
        )

        print("✅ Camera exceptions test passed")
        return True
    except Exception as e:
        print(f"❌ Camera exceptions test failed: {e}")
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
        print()

    print(f"📊 Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All camera implementation tests passed!")
        sys.exit(0)
    else:
        print("❌ Some camera implementation tests failed")
        sys.exit(1)
