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

        # Test CameraConfig creation
        CameraConfig(
            name="test_camera",
            type=CameraType.TAPO,
            params={"host": "192.168.1.100", "username": "test", "password": "test"},
        )

        # Test TapoCameraConfig
        TapoCameraConfig(host="192.168.1.100", username="test", password="test")
        return True
    except Exception:
        import traceback

        traceback.print_exc()
        return False


def test_camera_manager():
    """Test camera manager functionality."""
    try:
        from tapo_camera_mcp.camera.manager import CameraManager

        manager = CameraManager()

        # Test that manager is properly initialized
        assert hasattr(manager, "cameras")
        assert hasattr(manager, "groups")
        assert isinstance(manager.cameras, dict)

        return True
    except Exception:
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
        TapoCameraError("Test error")

        ConnectionError("Connection failed")
        AuthenticationError("Auth failed")

        return True
    except Exception:
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


    if passed == total:
        sys.exit(0)
    else:
        sys.exit(1)
