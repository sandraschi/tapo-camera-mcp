#!/usr/bin/env python3
"""
Comprehensive tests for core server functionality.
"""

import asyncio
import os
import sys

# Add the src path to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))


def test_server_initialization():
    """Test server initialization and basic setup."""
    try:
        from tapo_camera_mcp.core.server import TapoCameraServer

        # Test server creation (should be singleton)
        server1 = TapoCameraServer()
        server2 = TapoCameraServer()

        # Should return the same instance
        assert server1 is server2, "Server should be singleton"

        # Test that server has required attributes
        assert hasattr(server1, "_initialized"), "Server should have _initialized attribute"
        assert hasattr(server1, "camera_manager"), "Server should have camera_manager"
        assert server1._initialized is False, "Server should start uninitialized"

        print("✅ Server initialization test passed")
        return True
    except Exception as e:
        print(f"❌ Server initialization test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_server_singleton_pattern():
    """Test server singleton pattern implementation."""
    try:
        from tapo_camera_mcp.core.server import TapoCameraServer

        # Test singleton via class method
        server = asyncio.run(TapoCameraServer.get_instance())

        # Test that subsequent calls return same instance
        server2 = asyncio.run(TapoCameraServer.get_instance())
        assert server is server2, "get_instance should return same instance"

        print("✅ Server singleton pattern test passed")
        return True
    except Exception as e:
        print(f"❌ Server singleton test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_camera_manager_integration():
    """Test camera manager integration with server."""
    try:
        from tapo_camera_mcp.camera.manager import CameraManager
        from tapo_camera_mcp.core.server import TapoCameraServer

        server = asyncio.run(TapoCameraServer.get_instance())

        # Test camera manager is properly initialized
        assert isinstance(server.camera_manager, CameraManager), (
            "Server should have CameraManager instance"
        )

        # Test camera manager has required methods
        required_methods = [
            "get_cameras",
            "add_camera",
            "remove_camera",
            "get_active_cameras",
        ]
        for method in required_methods:
            assert hasattr(server.camera_manager, method), f"CameraManager missing method: {method}"

        print("✅ Camera manager integration test passed")
        return True
    except Exception as e:
        print(f"❌ Camera manager integration test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_mcp_server_setup():
    """Test MCP server setup and configuration."""
    try:
        from tapo_camera_mcp.core.server import TapoCameraServer

        server = asyncio.run(TapoCameraServer.get_instance())

        # Test that MCP server is initialized
        assert hasattr(server, "mcp"), "Server should have mcp attribute"
        assert server.mcp is not None, "MCP server should be initialized"

        # Test MCP server has required methods
        required_methods = ["list_tools", "run_tool"]
        for method in required_methods:
            assert hasattr(server.mcp, method), f"MCP server missing method: {method}"

        print("✅ MCP server setup test passed")
        return True
    except Exception as e:
        print(f"❌ MCP server setup test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_tools_registration():
    """Test that tools are properly registered with MCP server."""
    try:
        from tapo_camera_mcp.core.server import TapoCameraServer
        from tapo_camera_mcp.tools.discovery import discover_tools

        server = asyncio.run(TapoCameraServer.get_instance())

        # Test tools discovery
        tools = discover_tools("tapo_camera_mcp.tools")
        assert len(tools) > 0, "Should discover tools"

        # Test that tools are registered with MCP server
        registered_tools = server.mcp.list_tools()
        assert len(registered_tools) > 0, "Should have registered tools"

        # Check that we have camera-related tools
        tool_names = [tool["name"] for tool in registered_tools]
        camera_tools = [
            "list_cameras",
            "add_camera",
            "connect_camera",
            "get_camera_status",
        ]
        for tool_name in camera_tools:
            assert tool_name in tool_names, f"Missing camera tool: {tool_name}"

        print(f"✅ Tools registration test passed - {len(registered_tools)} tools registered")
        return True
    except Exception as e:
        print(f"❌ Tools registration test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_server_error_handling():
    """Test server error handling for invalid operations."""
    try:
        from tapo_camera_mcp.core.server import TapoCameraServer

        async def test_error_scenarios():
            server = await TapoCameraServer.get_instance()

            # Test invalid camera operations
            try:
                # This should handle gracefully when no cameras are configured
                result = await server.list_cameras()
                assert "cameras" in result, "Should return cameras list even when empty"
                print("✅ Server handles empty camera list gracefully")
            except Exception as e:
                print(f"❌ Server error handling failed: {e}")
                return False

            return True

        # Run async test
        result = asyncio.run(test_error_scenarios())
        return result

    except Exception as e:
        print(f"❌ Server error handling test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_server_configuration():
    """Test server configuration and setup."""
    try:
        from tapo_camera_mcp.core.server import TapoCameraServer

        server = asyncio.run(TapoCameraServer.get_instance())

        # Test server has configuration attributes
        assert hasattr(server, "_initialized"), "Server should track initialization state"

        # Test server can be configured (basic check)
        assert server._initialized is True, "Server should be initialized after get_instance"

        print("✅ Server configuration test passed")
        return True
    except Exception as e:
        print(f"❌ Server configuration test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    tests = [
        test_server_initialization,
        test_server_singleton_pattern,
        test_camera_manager_integration,
        test_mcp_server_setup,
        test_tools_registration,
        test_server_error_handling,
        test_server_configuration,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1
        print()

    print(f"📊 Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All server tests passed!")
        sys.exit(0)
    else:
        print("❌ Some server tests failed")
        sys.exit(1)
