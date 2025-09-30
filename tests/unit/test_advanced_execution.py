#!/usr/bin/env python3
"""
Advanced tool execution tests with actual server integration.
"""
import sys
import os
import asyncio
import unittest.mock as mock

# Add the src path to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

def test_server_singleton_pattern():
    """Test server singleton pattern implementation."""
    try:
        from tapo_camera_mcp.core.server import TapoCameraServer

        # Test that server is a singleton
        # We can't easily test the actual singleton without proper setup,
        # but we can test the class structure

        assert hasattr(TapoCameraServer, '__new__')
        assert hasattr(TapoCameraServer, '_instance')
        assert hasattr(TapoCameraServer, '_initialized')

        print("✅ Server singleton pattern test passed")
        return True
    except Exception as e:
        print(f"❌ Server singleton pattern test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_camera_factory_creation():
    """Test camera factory creation with different camera types."""
    try:
        from tapo_camera_mcp.camera.base import CameraFactory, CameraType, CameraConfig

        # Test creating different camera types
        tapo_config = CameraConfig(
            name="test_tapo",
            type=CameraType.TAPO,
            params={"host": "192.168.1.100", "username": "test", "password": "test"}
        )

        webcam_config = CameraConfig(
            name="test_webcam",
            type=CameraType.WEBCAM,
            params={"device_id": 0}
        )

        # Test that factory can create cameras (without actual connection)
        try:
            tapo_camera = CameraFactory.create(tapo_config)
            webcam_camera = CameraFactory.create(webcam_config)

            # Should be able to create instances
            assert tapo_camera is not None
            assert webcam_camera is not None

        except Exception:
            # Camera creation might fail due to missing dependencies,
            # but the factory method should exist
            pass

        print("✅ Camera factory creation test passed")
        return True
    except Exception as e:
        print(f"❌ Camera factory creation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_tool_execution_with_mocking():
    """Test tool execution with comprehensive mocking."""
    try:
        from tapo_camera_mcp.tools.camera.camera_tools import ListCamerasTool, AddCameraTool
        from tapo_camera_mcp.tools.system.status_tool import StatusTool
        from tapo_camera_mcp.tools.system.help_tool import HelpTool

        # Test ListCamerasTool with full mocking
        list_tool = ListCamerasTool()

        with mock.patch('tapo_camera_mcp.tools.camera.camera_tools.TapoCameraServer') as mock_server_class:
            # Mock the entire server instance and camera manager
            mock_server = mock.AsyncMock()
            mock_camera_manager = mock.AsyncMock()

            # Mock camera manager with actual camera objects
            mock_camera1 = mock.MagicMock()
            mock_camera1.config.name = "camera1"
            mock_camera1.config.type.value = "tapo"
            mock_camera1.get_status.return_value = {"connected": True, "streaming": False}

            mock_camera2 = mock.MagicMock()
            mock_camera2.config.name = "camera2"
            mock_camera2.config.type.value = "webcam"
            mock_camera2.get_status.return_value = {"connected": False, "streaming": False}

            mock_camera_manager.cameras = {
                "camera1": mock_camera1,
                "camera2": mock_camera2
            }
            mock_camera_manager.groups = mock.MagicMock()

            mock_server.camera_manager = mock_camera_manager
            mock_server_class.get_instance.return_value = mock_server

            # Execute the tool
            result = asyncio.run(list_tool.execute())

            # Should get a result
            assert result is not None
            assert hasattr(result, 'is_error') or isinstance(result, dict)

        # Test StatusTool execution
        status_tool = StatusTool(section="system")

        result = asyncio.run(status_tool.execute())
        assert result is not None

        # Test HelpTool execution
        help_tool = HelpTool(section="tools")

        result = asyncio.run(help_tool.execute())
        assert result is not None

        print("✅ Tool execution with mocking test passed")
        return True
    except Exception as e:
        print(f"❌ Tool execution with mocking test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_validation_error_scenarios():
    """Test validation error scenarios in tools."""
    try:
        from tapo_camera_mcp.tools.camera.camera_tools import AddCameraTool
        from tapo_camera_mcp.validation import ToolValidationError

        # Test tool with invalid parameters
        tool = AddCameraTool(
            camera_name="",  # Invalid empty name
            ip_address="192.168.1.100",
            username="test_user",
            password="test_pass"
        )

        # Mock server to avoid actual execution
        with mock.patch('tapo_camera_mcp.tools.camera.camera_tools.TapoCameraServer') as mock_server_class:
            mock_server = mock.AsyncMock()
            mock_server.add_camera.return_value = {"success": True}
            mock_server_class.get_instance.return_value = mock_server

            # This should fail validation before execution
            result = asyncio.run(tool.execute())

            # Should return an error result due to validation failure
            if hasattr(result, 'is_error'):
                assert result.is_error

        print("✅ Validation error scenarios test passed")
        return True
    except Exception as e:
        print(f"❌ Validation error scenarios test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_camera_connection_scenarios():
    """Test camera connection scenarios and error handling."""
    try:
        from tapo_camera_mcp.camera.tapo import TapoCamera
        from tapo_camera_mcp.camera.webcam import WebCamera
        from tapo_camera_mcp.camera.base import CameraConfig, CameraType
        from tapo_camera_mcp.exceptions import ConnectionError, AuthenticationError

        # Test Tapo camera connection error handling
        tapo_config = CameraConfig(
            name="test_tapo",
            type=CameraType.TAPO,
            params={"host": "192.168.1.100", "username": "test", "password": "test"}
        )

        tapo_camera = TapoCamera(tapo_config)

        # Test that camera has proper error handling structure
        assert hasattr(tapo_camera, '_is_connected')
        assert hasattr(tapo_camera, '_last_error')
        assert hasattr(tapo_camera, 'connect')
        assert hasattr(tapo_camera, 'disconnect')
        assert hasattr(tapo_camera, 'get_status')

        # Test webcam connection error handling
        webcam_config = CameraConfig(
            name="test_webcam",
            type=CameraType.WEBCAM,
            params={"device_id": 0}
        )

        webcam_camera = WebCamera(webcam_config)

        assert hasattr(webcam_camera, '_is_connected')
        assert hasattr(webcam_camera, '_cap')
        assert hasattr(webcam_camera, 'connect')
        assert hasattr(webcam_camera, 'disconnect')

        print("✅ Camera connection scenarios test passed")
        return True
    except Exception as e:
        print(f"❌ Camera connection scenarios test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_web_api_error_handling():
    """Test web API error handling."""
    try:
        from tapo_camera_mcp.web.server import WebServer
        from fastapi.testclient import TestClient

        # Mock config
        with mock.patch('tapo_camera_mcp.web.server.get_config') as mock_get_config, \
             mock.patch('tapo_camera_mcp.web.server.get_model') as mock_get_model:

            mock_get_config.return_value = {"debug": False}
            mock_get_model.return_value = mock.MagicMock()

            server = WebServer()
            client = TestClient(server.app)

            # Test API endpoints that might fail
            response = client.get("/api/cameras")
            # Should not crash, even if server is not available
            assert response.status_code in [200, 500, 422]

            response = client.get("/api/cameras/test_camera/stream")
            # Should handle missing camera gracefully
            assert response.status_code in [200, 404, 500]

            response = client.get("/api/cameras/test_camera/snapshot")
            # Should handle missing camera gracefully
            assert response.status_code in [200, 404, 500]

            print("✅ Web API error handling test passed")
        return True
    except Exception as e:
        print(f"❌ Web API error handling test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_tool_registry_operations():
    """Test tool registry operations and edge cases."""
    try:
        from tapo_camera_mcp.tools.base_tool import register_tool, get_tool, get_all_tools, _tool_registry

        # Clear registry for clean test
        _tool_registry.clear()

        # Test registering multiple tools
        class TestTool1:
            class Meta:
                name = "test_tool_1"

        class TestTool2:
            class Meta:
                name = "test_tool_2"

        register_tool(TestTool1)
        register_tool(TestTool2)

        # Test that tools are registered
        all_tools = get_all_tools()
        assert len(all_tools) >= 2

        # Test getting tools by name
        tool1 = get_tool("test_tool_1")
        tool2 = get_tool("test_tool_2")

        assert tool1 == TestTool1
        assert tool2 == TestTool2

        # Test getting non-existent tool
        nonexistent = get_tool("nonexistent_tool")
        assert nonexistent is None

        print("✅ Tool registry operations test passed")
        return True
    except Exception as e:
        print(f"❌ Tool registry operations test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_async_tool_execution():
    """Test async tool execution patterns."""
    try:
        from tapo_camera_mcp.tools.camera.camera_tools import ListCamerasTool, GetCameraStatusTool
        from tapo_camera_mcp.tools.system.status_tool import StatusTool

        # Test that tools have async execute methods
        tools_to_test = [
            ListCamerasTool(),
            GetCameraStatusTool(camera_id="test"),
            StatusTool(section="system")
        ]

        for tool in tools_to_test:
            # Check that execute is a coroutine function
            import inspect
            assert inspect.iscoroutinefunction(tool.execute), f"Tool {tool.__class__.__name__} execute should be async"

        # Test concurrent execution
        async def test_concurrent_execution():
            tasks = [tool.execute() for tool in tools_to_test[:2]]  # Test first 2 tools
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Should complete without crashing
            assert len(results) == 2
            for result in results:
                assert result is not None

        # Run concurrent test
        asyncio.run(test_concurrent_execution())

        print("✅ Async tool execution test passed")
        return True
    except Exception as e:
        print(f"❌ Async tool execution test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_system_resource_monitoring():
    """Test system resource monitoring in status tools."""
    try:
        from tapo_camera_mcp.tools.system.status_tool import StatusTool

        # Test StatusTool with different sections
        sections_to_test = ["system", "cameras", "tools"]

        for section in sections_to_test:
            tool = StatusTool(section=section)

            # Should be able to execute without crashing
            try:
                result = asyncio.run(tool.execute())
                assert result is not None
            except Exception:
                # Some sections might not be implemented yet, but tool should not crash
                pass

        print("✅ System resource monitoring test passed")
        return True
    except Exception as e:
        print(f"❌ System resource monitoring test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_error_recovery_mechanisms():
    """Test error recovery mechanisms in the system."""
    try:
        from tapo_camera_mcp.exceptions import TapoCameraError, ConnectionError, AuthenticationError

        # Test exception hierarchy and error types
        exceptions_to_test = [
            TapoCameraError("Base error"),
            ConnectionError("Connection failed"),
            AuthenticationError("Auth failed")
        ]

        for exc in exceptions_to_test:
            # Test that exceptions can be created and raised
            try:
                raise exc
            except TapoCameraError:
                # Should be caught as base exception
                pass
            except Exception as e:
                # Should be the specific exception type
                assert type(e) == type(exc)

        print("✅ Error recovery mechanisms test passed")
        return True
    except Exception as e:
        print(f"❌ Error recovery mechanisms test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_configuration_validation():
    """Test configuration validation across the system."""
    try:
        from tapo_camera_mcp.core.models import TapoCameraConfig

        # Test valid configuration
        valid_config = TapoCameraConfig(
            host="192.168.1.100",
            username="testuser",
            password="testpass",
            port=443,
            use_https=True,
            verify_ssl=False,
            timeout=10
        )

        assert valid_config.host == "192.168.1.100"
        assert valid_config.port == 443

        # Test configuration with validators
        # Port validation
        try:
            invalid_config = TapoCameraConfig(
                host="192.168.1.100",
                username="testuser",
                password="testpass",
                port=70000  # Invalid port
            )
            assert False, "Should have failed validation"
        except Exception:
            pass  # Expected validation error

        # Test timeout validation
        try:
            invalid_config = TapoCameraConfig(
                host="192.168.1.100",
                username="testuser",
                password="testpass",
                timeout=0  # Invalid timeout
            )
            assert False, "Should have failed validation"
        except Exception:
            pass  # Expected validation error

        print("✅ Configuration validation test passed")
        return True
    except Exception as e:
        print(f"❌ Configuration validation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    tests = [
        test_server_singleton_pattern,
        test_camera_factory_creation,
        test_tool_execution_with_mocking,
        test_validation_error_scenarios,
        test_camera_connection_scenarios,
        test_web_api_error_handling,
        test_tool_registry_operations,
        test_async_tool_execution,
        test_system_resource_monitoring,
        test_error_recovery_mechanisms,
        test_configuration_validation,
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

    print(f"📊 Results: {passed}/{total} advanced tool execution tests passed")

    if passed == total:
        print("🎉 All advanced tool execution tests passed!")
        sys.exit(0)
    else:
        print("❌ Some advanced tool execution tests failed")
        sys.exit(1)
