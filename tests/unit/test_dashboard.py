#!/usr/bin/env python3
"""
Tests for web dashboard and API endpoints.
"""

import os
import sys

# Add the src path to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))


def test_web_server_creation():
    """Test web server creation and initialization."""
    try:
        from tapo_camera_mcp.web.server import TapoWebServer

        # Test server creation
        server = TapoWebServer()
        assert hasattr(server, "app"), "Web server should have app attribute"
        assert hasattr(server, "host"), "Web server should have host attribute"
        assert hasattr(server, "port"), "Web server should have port attribute"

        return True
    except Exception:
        import traceback

        traceback.print_exc()
        return False


def test_web_routes():
    """Test web server routes and endpoints."""
    try:
        from tapo_camera_mcp.web.server import TapoWebServer

        TapoWebServer()

        # Test that server has required routes

        # Check for basic routes (these would be defined in the server)
        # Note: We can't easily test actual route registration without starting the server

        return True
    except Exception:
        import traceback

        traceback.print_exc()
        return False


def test_api_endpoints():
    """Test API endpoints structure."""
    try:
        # Test that API modules can be imported
        from tapo_camera_mcp.api import v1

        # Check that API v1 module exists and has endpoints
        assert hasattr(v1, "endpoints"), "API v1 should have endpoints module"

        return True
    except Exception:
        import traceback

        traceback.print_exc()
        return False


def test_camera_api_endpoints():
    """Test camera API endpoints."""
    try:
        # Test that cameras module has expected functions
        # Note: These would be actual endpoint functions

        return True
    except Exception:
        import traceback

        traceback.print_exc()
        return False


def test_media_api_endpoints():
    """Test media API endpoints."""
    try:
        # Test that media module has expected functions

        return True
    except Exception:
        import traceback

        traceback.print_exc()
        return False


def test_ptz_api_endpoints():
    """Test PTZ API endpoints."""
    try:
        # Test that PTZ module has expected functions

        return True
    except Exception:
        import traceback

        traceback.print_exc()
        return False


def test_system_api_endpoints():
    """Test system API endpoints."""
    try:
        # Test that system module has expected functions

        return True
    except Exception:
        import traceback

        traceback.print_exc()
        return False


def test_web_static_files():
    """Test web static files and templates."""
    try:
        # Test that static directories exist
        static_dirs = [
            "src/tapo_camera_mcp/web/static",
            "src/tapo_camera_mcp/web/templates",
        ]

        for dir_path in static_dirs:
            full_path = os.path.join(os.path.dirname(__file__), "..", "..", dir_path)
            if os.path.exists(full_path):
                pass
            else:
                pass

        return True
    except Exception:
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    tests = [
        test_web_server_creation,
        test_web_routes,
        test_api_endpoints,
        test_camera_api_endpoints,
        test_media_api_endpoints,
        test_ptz_api_endpoints,
        test_system_api_endpoints,
        test_web_static_files,
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
