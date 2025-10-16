#!/usr/bin/env python3
"""
Test camera functionality and models.
"""

import os
import sys

# Add the src path to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))


def test_camera_models():
    """Test camera model definitions."""
    try:
        from tapo_camera_mcp.camera.base import CameraConfig, CameraType
        from tapo_camera_mcp.core.models import TapoCameraConfig

        # Test CameraType enum
        camera_types = [
            CameraType.TAPO,
            CameraType.WEBCAM,
            CameraType.RING,
            CameraType.FURBO,
        ]
        print(f"✅ Camera types: {[ct.value for ct in camera_types]}")

        # Test CameraConfig creation
        config = CameraConfig(
            name="test_camera",
            type=CameraType.TAPO,
            params={"host": "192.168.1.100", "username": "test", "password": "test"},
        )
        print(f"✅ Camera config created: {config.name}")

        # Test TapoCameraConfig
        tapo_config = TapoCameraConfig(host="192.168.1.100", username="test", password="test")
        print("✅ TapoCamera config created")
        return True
    except Exception as e:
        print(f"❌ Camera models test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_camera_manager():
    """Test camera manager functionality."""
    try:
        from tapo_camera_mcp.camera.manager import CameraManager

        manager = CameraManager()
        print("✅ Camera manager created")

        # Test that manager is properly initialized
        assert hasattr(manager, "cameras")
        assert hasattr(manager, "groups")
        assert isinstance(manager.cameras, dict)

        print("✅ Camera manager structure test passed")
        return True
    except Exception as e:
        print(f"❌ Camera manager test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_exceptions():
    """Test exception classes."""
    try:
        from tapo_camera_mcp.exceptions import (
            AuthenticationError,
            ConnectionError,
            TapoCameraError,
        )

        # Test exception creation
        error = TapoCameraError("Test error")
        print(f"✅ Exception created: {error}")

        connection_error = ConnectionError("Connection failed")
        auth_error = AuthenticationError("Auth failed")

        print("✅ All exception types created successfully")
        return True
    except Exception as e:
        print(f"❌ Exception test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    tests = [
        test_camera_models,
        test_camera_manager,
        test_exceptions,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1
        print()

    print(f"📊 Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All camera tests passed!")
        sys.exit(0)
    else:
        print("❌ Some camera tests failed")
        sys.exit(1)
