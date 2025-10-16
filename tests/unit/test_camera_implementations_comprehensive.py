#!/usr/bin/env python3
"""
Comprehensive tests for camera implementations (Tapo, Webcam, Ring, Furbo).
"""

import asyncio
import os
import sys
from unittest import mock

# Add the src path to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))


def test_camera_implementations_creation():
    """Test creation of all camera implementation classes."""
    try:
        from tapo_camera_mcp.camera.base import CameraConfig, CameraType
        from tapo_camera_mcp.camera.tapo import TapoCamera
        from tapo_camera_mcp.camera.webcam import WebCamera

        # Test Tapo camera creation
        tapo_config = CameraConfig(
            name="test_tapo",
            type=CameraType.TAPO,
            params={"host": "192.168.1.100", "username": "test", "password": "test"},
        )
        tapo_camera = TapoCamera(tapo_config)
        assert tapo_camera.config == tapo_config
        assert not tapo_camera._is_connected
        assert not tapo_camera._is_streaming

        # Test Webcam creation
        webcam_config = CameraConfig(
            name="test_webcam", type=CameraType.WEBCAM, params={"device_id": 0}
        )
        webcam_camera = WebCamera(webcam_config)
        assert webcam_camera.config == webcam_config
        assert not webcam_camera._is_connected
        assert not webcam_camera._is_streaming
        assert webcam_camera._device_id == 0

        print("✅ Camera implementation creation tests passed")
        return True
    except Exception as e:
        print(f"❌ Camera implementation creation tests failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_camera_factory_registration():
    """Test camera factory registration system."""
    try:
        from tapo_camera_mcp.camera.base import CameraFactory, CameraType

        # Test that camera types are registered
        assert CameraType.TAPO in CameraFactory._camera_classes
        assert CameraType.WEBCAM in CameraFactory._camera_classes

        # Test creating cameras via factory
        tapo_config = {
            "name": "factory_tapo",
            "type": CameraType.TAPO,
            "params": {"host": "192.168.1.100", "username": "test", "password": "test"},
        }

        webcam_config = {
            "name": "factory_webcam",
            "type": CameraType.WEBCAM,
            "params": {"device_id": 0},
        }

        from tapo_camera_mcp.camera.tapo import TapoCamera
        from tapo_camera_mcp.camera.webcam import WebCamera

        tapo_camera = CameraFactory.create(tapo_config)
        webcam_camera = CameraFactory.create(webcam_config)

        assert isinstance(tapo_camera, TapoCamera)
        assert isinstance(webcam_camera, WebCamera)

        print("✅ Camera factory registration tests passed")
        return True
    except Exception as e:
        print(f"❌ Camera factory registration tests failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_camera_connection_handling():
    """Test camera connection handling with mocked dependencies."""
    try:
        from tapo_camera_mcp.camera.base import CameraConfig, CameraType
        from tapo_camera_mcp.camera.tapo import TapoCamera
        from tapo_camera_mcp.camera.webcam import WebCamera
        from tapo_camera_mcp.exceptions import ConnectionError

        # Test Tapo camera connection (mocked to fail)
        tapo_config = CameraConfig(
            name="test_tapo_connect",
            type=CameraType.TAPO,
            params={"host": "invalid_host", "username": "test", "password": "test"},
        )
        tapo_camera = TapoCamera(tapo_config)

        # Mock the Tapo class to raise an exception
        with mock.patch("tapo_camera_mcp.camera.tapo.Tapo") as mock_tapo_class:
            mock_tapo_instance = mock_tapo_class.return_value
            mock_tapo_instance.getBasicInfo.side_effect = Exception("Connection failed")

            # Test connection failure
            try:
                asyncio.run(tapo_camera.connect())
                assert False, "Should have raised ConnectionError"
            except ConnectionError:
                pass  # Expected

        # Test webcam connection (mocked to fail)
        webcam_config = CameraConfig(
            name="test_webcam_connect",
            type=CameraType.WEBCAM,
            params={"device_id": 999},  # Invalid device
        )
        webcam_camera = WebCamera(webcam_config)

        # Mock cv2.VideoCapture to fail
        with mock.patch("cv2.VideoCapture") as mock_cap:
            mock_cap_instance = mock_cap.return_value
            mock_cap_instance.isOpened.return_value = False

            try:
                asyncio.run(webcam_camera.connect())
                assert False, "Should have raised ConnectionError"
            except ConnectionError:
                pass  # Expected

        print("✅ Camera connection handling tests passed")
        return True
    except Exception as e:
        print(f"❌ Camera connection handling tests failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_camera_status_reporting():
    """Test camera status reporting functionality."""
    try:
        from tapo_camera_mcp.camera.base import CameraConfig, CameraType
        from tapo_camera_mcp.camera.tapo import TapoCamera
        from tapo_camera_mcp.camera.webcam import WebCamera

        # Test Tapo camera status when disconnected
        tapo_config = CameraConfig(
            name="test_tapo_status",
            type=CameraType.TAPO,
            params={"host": "192.168.1.100", "username": "test", "password": "test"},
        )
        tapo_camera = TapoCamera(tapo_config)

        status = asyncio.run(tapo_camera.get_status())
        assert not status["connected"]
        assert not status["streaming"]
        assert status["type"] == "tapo"
        assert not status["enabled"]
        assert "last_error" in status

        # Test Webcam status when disconnected
        webcam_config = CameraConfig(
            name="test_webcam_status", type=CameraType.WEBCAM, params={"device_id": 0}
        )
        webcam_camera = WebCamera(webcam_config)

        status = asyncio.run(webcam_camera.get_status())
        assert not status["connected"]
        assert not status["streaming"]
        assert status["type"] == "webcam"
        assert not status["enabled"]
        assert "last_error" in status

        print("✅ Camera status reporting tests passed")
        return True
    except Exception as e:
        print(f"❌ Camera status reporting tests failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_camera_streaming_functionality():
    """Test camera streaming functionality (mocked)."""
    try:
        from tapo_camera_mcp.camera.base import CameraConfig, CameraType
        from tapo_camera_mcp.camera.tapo import TapoCamera

        # Test Tapo camera streaming URL when not connected
        tapo_config = CameraConfig(
            name="test_tapo_stream",
            type=CameraType.TAPO,
            params={"host": "192.168.1.100", "username": "test", "password": "test"},
        )
        tapo_camera = TapoCamera(tapo_config)

        stream_url = asyncio.run(tapo_camera.get_stream_url())
        assert stream_url is None  # Should be None when not connected

        print("✅ Camera streaming functionality tests passed")
        return True
    except Exception as e:
        print(f"❌ Camera streaming functionality tests failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_ring_camera_implementation():
    """Test Ring camera implementation (if available)."""
    try:
        from tapo_camera_mcp.camera.base import CameraConfig, CameraType
        from tapo_camera_mcp.camera.ring import RingCamera

        # Create Ring camera config
        ring_config = CameraConfig(
            name="test_ring",
            type=CameraType.RING,
            params={
                "device_id": "test_device",
                "api_key": "test_key",
                "refresh_token": "test_token",
            },
        )

        # Create camera instance
        ring_camera = RingCamera(ring_config)

        # Test basic properties
        assert ring_camera.config == ring_config
        assert not ring_camera._is_connected
        assert not ring_camera._is_streaming

        print("✅ Ring camera implementation tests passed")
        return True
    except ImportError:
        print("⚠️ Ring camera implementation not available, skipping test")
        return True
    except Exception as e:
        print(f"❌ Ring camera implementation tests failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_furbo_camera_implementation():
    """Test Furbo camera implementation (if available)."""
    try:
        from tapo_camera_mcp.camera.base import CameraConfig, CameraType
        from tapo_camera_mcp.camera.furbo import FurboCamera

        # Create Furbo camera config
        furbo_config = CameraConfig(
            name="test_furbo",
            type=CameraType.FURBO,
            params={"device_id": "test_device", "api_key": "test_key"},
        )

        # Create camera instance
        furbo_camera = FurboCamera(furbo_config)

        # Test basic properties
        assert furbo_camera.config == furbo_config
        assert not furbo_camera._is_connected
        assert not furbo_camera._is_streaming

        print("✅ Furbo camera implementation tests passed")
        return True
    except ImportError:
        print("⚠️ Furbo camera implementation not available, skipping test")
        return True
    except Exception as e:
        print(f"❌ Furbo camera implementation tests failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_camera_error_handling():
    """Test camera error handling and exception raising."""
    try:
        from tapo_camera_mcp.camera.base import CameraConfig, CameraType
        from tapo_camera_mcp.camera.tapo import TapoCamera

        # Test that cameras properly handle errors
        tapo_config = CameraConfig(
            name="test_error_handling",
            type=CameraType.TAPO,
            params={"host": "192.168.1.100", "username": "test", "password": "test"},
        )
        tapo_camera = TapoCamera(tapo_config)

        # Test that calling methods on disconnected camera doesn't crash
        try:
            # These should not raise exceptions, just return appropriate values
            status = asyncio.run(tapo_camera.get_status())
            assert isinstance(status, dict)

            stream_url = asyncio.run(tapo_camera.get_stream_url())
            assert stream_url is None

        except Exception as unexpected_error:
            assert False, f"Unexpected error: {unexpected_error}"

        print("✅ Camera error handling tests passed")
        return True
    except Exception as e:
        print(f"❌ Camera error handling tests failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    tests = [
        test_camera_implementations_creation,
        test_camera_factory_registration,
        test_camera_connection_handling,
        test_camera_status_reporting,
        test_camera_streaming_functionality,
        test_ring_camera_implementation,
        test_furbo_camera_implementation,
        test_camera_error_handling,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1
        print()

    print(f"📊 Results: {passed}/{total} camera implementation tests passed")

    if passed == total:
        print("🎉 All camera implementation tests passed!")
        sys.exit(0)
    else:
        print("❌ Some camera implementation tests failed")
        sys.exit(1)
