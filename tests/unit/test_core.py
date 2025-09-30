#!/usr/bin/env python3
"""
Focused test for core MCP server functionality and coverage.
"""
import sys
import os

# Add the src path to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

def test_core_imports():
    """Test core module imports."""
    try:
        from tapo_camera_mcp.core.server import TapoCameraServer
        from tapo_camera_mcp.core.models import TapoCameraConfig
        from tapo_camera_mcp.exceptions import TapoCameraError
        print("✅ Core imports successful")
        return True
    except Exception as e:
        print(f"❌ Core import failed: {e}")
        return False

def test_tools_discovery():
    """Test tools discovery."""
    try:
        from tapo_camera_mcp.tools.discovery import discover_tools
        tools = discover_tools('tapo_camera_mcp.tools')
        print(f"✅ Tools discovery successful - found {len(tools)} tools")
        return True
    except Exception as e:
        print(f"❌ Tools discovery failed: {e}")
        return False

def test_camera_types():
    """Test camera type definitions."""
    try:
        from tapo_camera_mcp.camera.base import CameraType, CameraConfig
        print(f"✅ Camera types available: {[ct.value for ct in CameraType]}")
        return True
    except Exception as e:
        print(f"❌ Camera types test failed: {e}")
        return False

def test_basic_server_creation():
    """Test basic server creation (without running it)."""
    try:
        from tapo_camera_mcp.core.server import TapoCameraServer
        # Just test that we can create the class, don't initialize
        server_class = TapoCameraServer
        print("✅ Server class creation successful")
        return True
    except Exception as e:
        print(f"❌ Server creation failed: {e}")
        return False

if __name__ == "__main__":
    tests = [
        test_core_imports,
        test_tools_discovery,
        test_camera_types,
        test_basic_server_creation,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1
        print()

    print(f"📊 Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed")
        sys.exit(1)
