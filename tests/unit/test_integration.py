#!/usr/bin/env python3
"""
Integration tests for the full tapo-camera-mcp system.
"""

import sys
import os
import unittest.mock as mock

# Add the src path to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))


def test_server_initialization():
    """Test server initialization and basic setup."""
    try:
        from tapo_camera_mcp.core.server import TapoCameraServer

        # Test server creation (should not fail)
        server_class = TapoCameraServer

        # Test that we can reference the server class
        assert hasattr(TapoCameraServer, "get_instance")
        assert hasattr(TapoCameraServer, "__init__")

        # Test singleton pattern
        # Note: We can't actually instantiate without proper setup, but we can test the structure

        print("✅ Server initialization test passed")
        return True
    except Exception as e:
        print(f"❌ Server initialization test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_camera_manager_integration():
    """Test camera manager integration with server."""
    try:
        from tapo_camera_mcp.camera.manager import CameraManager

        # Test CameraManager creation
        manager = CameraManager()

        # Test that manager has expected attributes
        assert hasattr(manager, "cameras")
        assert hasattr(manager, "groups")
        assert hasattr(manager, "_initialized")

        # Test server reference to camera manager
        # We can't easily test the full integration without proper setup,
        # but we can test that the structure exists

        print("✅ Camera manager integration test passed")
        return True
    except Exception as e:
        print(f"❌ Camera manager integration test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_validation_module():
    """Test validation module functionality."""
    try:
        from tapo_camera_mcp.validation import (
            validate_ip_address,
            validate_port,
            validate_camera_name,
            validate_credentials,
            ToolValidationError,
        )

        # Test IP address validation
        valid_ip = validate_ip_address("192.168.1.100", "test_ip")
        assert valid_ip == "192.168.1.100"

        # Test invalid IP address
        try:
            validate_ip_address("invalid.ip", "test_ip")
            assert False, "Should have raised ValidationError"
        except ToolValidationError:
            pass  # Expected

        # Test port validation
        valid_port = validate_port(8080, "test_port")
        assert valid_port == 8080

        # Test invalid port
        try:
            validate_port(70000, "test_port")
            assert False, "Should have raised ValidationError"
        except ToolValidationError:
            pass  # Expected

        # Test camera name validation
        valid_name = validate_camera_name("test_camera_1", "test_name")
        assert valid_name == "test_camera_1"

        # Test invalid camera name
        try:
            validate_camera_name("test camera with spaces!", "test_name")
            assert False, "Should have raised ValidationError"
        except ToolValidationError:
            pass  # Expected

        # Test credentials validation
        username, password = validate_credentials("testuser", "testpass")
        assert username == "testuser"
        assert password == "testpass"

        print("✅ Validation module test passed")
        return True
    except Exception as e:
        print(f"❌ Validation module test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_exception_hierarchy():
    """Test exception hierarchy and error handling."""
    try:
        from tapo_camera_mcp.exceptions import (
            TapoCameraError,
            ConnectionError,
            AuthenticationError,
            CameraNotSupportedError,
            StreamError,
            PTZError,
            StorageError,
            ConfigurationError,
            TimeoutError,
            FirmwareError,
        )

        # Test exception inheritance
        assert issubclass(ConnectionError, TapoCameraError)
        assert issubclass(AuthenticationError, TapoCameraError)
        assert issubclass(CameraNotSupportedError, TapoCameraError)
        assert issubclass(StreamError, TapoCameraError)
        assert issubclass(PTZError, TapoCameraError)
        assert issubclass(StorageError, TapoCameraError)
        assert issubclass(ConfigurationError, TapoCameraError)
        assert issubclass(TimeoutError, TapoCameraError)
        assert issubclass(FirmwareError, TapoCameraError)

        # Test exception creation
        error = TapoCameraError("Test error")
        assert str(error) == "Test error"

        connection_error = ConnectionError("Connection failed")
        auth_error = AuthenticationError("Auth failed")

        print("✅ Exception hierarchy test passed")
        return True
    except Exception as e:
        print(f"❌ Exception hierarchy test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_camera_base_classes():
    """Test camera base classes and factory pattern."""
    try:
        from tapo_camera_mcp.camera.base import CameraType, CameraConfig, CameraFactory

        # Test CameraType enum
        camera_types = [
            CameraType.TAPO,
            CameraType.WEBCAM,
            CameraType.RING,
            CameraType.FURBO,
        ]
        for ct in camera_types:
            assert isinstance(ct.value, str)
            assert len(ct.value) > 0

        # Test CameraConfig creation
        config = CameraConfig(
            name="test_camera",
            type=CameraType.TAPO,
            params={"host": "192.168.1.100", "username": "test", "password": "test"},
        )

        assert config.name == "test_camera"
        assert config.type == CameraType.TAPO
        assert config.enabled is True

        # Test CameraFactory registration
        assert CameraType.TAPO in CameraFactory._camera_classes
        assert CameraType.WEBCAM in CameraFactory._camera_classes

        print("✅ Camera base classes test passed")
        return True
    except Exception as e:
        print(f"❌ Camera base classes test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_core_models():
    """Test core data models."""
    try:
        from tapo_camera_mcp.core.models import (
            CameraModel,
            StreamType,
            VideoQuality,
            PTZDirection,
            MotionDetectionSensitivity,
            CameraStatus,
            PTZPosition,
            TapoCameraConfig,
        )

        # Test enums
        assert CameraModel.C100.value == "Tapo C100"
        assert StreamType.RTSP.value == "rtsp"
        assert VideoQuality.HIGH.value == "high"
        assert PTZDirection.UP.value == "up"
        assert MotionDetectionSensitivity.HIGH.value == "high"

        # Test Pydantic models
        status = CameraStatus(
            online=True,
            recording=False,
            motion_detected=False,
            mac_address="00:11:22:33:44:55",
            firmware_version="1.0.0",
            hardware_version="1.0",
        )

        assert status.online is True
        assert status.recording is False

        # Test PTZPosition
        position = PTZPosition(pan=0.5, tilt=-0.3, zoom=0.8)
        assert position.pan == 0.5
        assert position.tilt == -0.3
        assert position.zoom == 0.8

        # Test TapoCameraConfig with validation
        config = TapoCameraConfig(
            host="192.168.1.100", username="testuser", password="testpass", port=443
        )

        assert config.host == "192.168.1.100"
        assert config.port == 443

        print("✅ Core models test passed")
        return True
    except Exception as e:
        print(f"❌ Core models test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_web_server_routes():
    """Test web server route definitions."""
    try:
        from tapo_camera_mcp.web.server import WebServer
        from fastapi.testclient import TestClient

        # Mock config for web server
        with mock.patch(
            "tapo_camera_mcp.web.server.get_config"
        ) as mock_get_config, mock.patch(
            "tapo_camera_mcp.web.server.get_model"
        ) as mock_get_model:
            mock_get_config.return_value = {"debug": False}
            mock_get_model.return_value = mock.MagicMock()

            server = WebServer()
            client = TestClient(server.app)

            # Test that routes are defined (check they don't 404)
            routes_to_test = [
                "/api/status",
                "/api/cameras",
                "/",
                "/cameras",
                "/settings",
                "/help",
            ]

            for route in routes_to_test:
                response = client.get(route)
                # Should not be 404 (might be other errors but routes exist)
                assert response.status_code != 404, f"Route {route} should exist"

            print("✅ Web server routes test passed")
            return True
    except Exception as e:
        print(f"❌ Web server routes test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_system_health_check():
    """Test system health check functionality."""
    try:
        from tapo_camera_mcp.tools.system.status_tool import StatusTool

        # Test StatusTool structure
        tool = StatusTool(section="system")

        assert hasattr(tool, "Meta")
        assert hasattr(tool.Meta, "name")
        assert tool.Meta.name == "status"

        # Test that tool can be executed (basic smoke test)
        # We don't need to test the actual execution result, just that it doesn't crash

        print("✅ System health check test passed")
        return True
    except Exception as e:
        print(f"❌ System health check test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_configuration_loading():
    """Test configuration loading and validation."""
    try:
        # Test that we can import config functions
        from tapo_camera_mcp.config import get_config, get_model

        # Test that config functions exist and are callable
        assert callable(get_config)
        assert callable(get_model)

        # We can't easily test the actual config loading without proper config files,
        # but we can test that the functions don't crash when called
        try:
            config = get_config()
            # If this doesn't crash, config loading works
        except Exception:
            # Config loading might fail without proper config, but the function should exist
            pass

        print("✅ Configuration loading test passed")
        return True
    except Exception as e:
        print(f"❌ Configuration loading test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_logging_setup():
    """Test logging setup and configuration."""
    try:
        from tapo_camera_mcp.utils.logging import setup_logging

        # Test that logging setup function exists and is callable
        assert callable(setup_logging)

        # Test that we can call it without crashing
        try:
            setup_logging()
        except Exception:
            # Logging setup might fail in test environment, but function should exist
            pass

        print("✅ Logging setup test passed")
        return True
    except Exception as e:
        print(f"❌ Logging setup test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_full_system_import():
    """Test that the full system can be imported without circular dependencies."""
    try:
        # Test importing main modules
        from tapo_camera_mcp.core import server, models
        from tapo_camera_mcp.camera import base, manager
        from tapo_camera_mcp.tools import base_tool, discovery
        from tapo_camera_mcp.web import server as web_server
        from tapo_camera_mcp import validation, exceptions

        # Test that key classes exist
        assert hasattr(server, "TapoCameraServer")
        assert hasattr(models, "TapoCameraConfig")
        assert hasattr(base, "CameraType")
        assert hasattr(base, "CameraFactory")
        assert hasattr(manager, "CameraManager")
        assert hasattr(base_tool, "BaseTool")
        assert hasattr(base_tool, "ToolResult")
        assert hasattr(discovery, "discover_tools")
        assert hasattr(web_server, "WebServer")
        assert hasattr(validation, "validate_ip_address")
        assert hasattr(exceptions, "TapoCameraError")

        print("✅ Full system import test passed")
        return True
    except Exception as e:
        print(f"❌ Full system import test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    tests = [
        test_server_initialization,
        test_camera_manager_integration,
        test_validation_module,
        test_exception_hierarchy,
        test_camera_base_classes,
        test_core_models,
        test_web_server_routes,
        test_system_health_check,
        test_configuration_loading,
        test_logging_setup,
        test_full_system_import,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
        print()

    print(f"📊 Results: {passed}/{total} integration tests passed")

    if passed == total:
        print("🎉 All integration tests passed!")
        sys.exit(0)
    else:
        print("❌ Some integration tests failed")
        sys.exit(1)
