#!/usr/bin/env python3
"""
Comprehensive tests for web dashboard and API endpoints.
"""

import os
import sys
from unittest.mock import AsyncMock, Mock, patch

# Add the src path to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))


def test_web_server_initialization():
    """Test web server initialization and setup."""
    try:
        from tapo_camera_mcp.web.server import WebServer

        # Mock the config functions
        with patch("tapo_camera_mcp.web.server.get_config") as mock_get_config, patch(
            "tapo_camera_mcp.web.server.get_model"
        ) as mock_get_model:
            mock_config = {"debug": False, "log_level": "info"}
            mock_web_config = Mock()
            mock_web_config.title = "Test Server"
            mock_web_config.theme = "light"
            mock_web_config.enable_cors = True
            mock_web_config.cors_origins = ["*"]
            mock_web_config.enable_swagger = True
            mock_web_config.enable_redoc = True
            mock_web_config.host = "127.0.0.1"
            mock_web_config.port = 8080

            mock_security_config = Mock()

            mock_get_config.return_value = mock_config
            mock_get_model.side_effect = lambda cls: (
                mock_web_config if cls.__name__ == "WebUISettings" else mock_security_config
            )

            # Create web server instance
            server = WebServer()

            # Test that FastAPI app is created
            assert hasattr(server, "app")
            assert server.app.title == "Tapo Camera MCP"

            # Test that middleware is set up
            assert len(server.app.user_middleware) > 0

            # Test that templates are configured
            assert hasattr(server, "templates")

            print("✅ Web server initialization test passed")
            return True
    except Exception as e:
        print(f"❌ Web server initialization test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_api_status_endpoint():
    """Test the /api/status endpoint."""
    try:
        from fastapi.testclient import TestClient

        from tapo_camera_mcp.web.server import WebServer

        # Mock config
        with patch("tapo_camera_mcp.web.server.get_config") as mock_get_config, patch(
            "tapo_camera_mcp.web.server.get_model"
        ):
            mock_get_config.return_value = {"debug": False}
            mock_get_model.return_value = Mock()

            server = WebServer()
            client = TestClient(server.app)

            # Test GET /api/status
            response = client.get("/api/status")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"
            assert "version" in data
            assert "debug" in data

            print("✅ API status endpoint test passed")
            return True
    except Exception as e:
        print(f"❌ API status endpoint test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_api_cameras_endpoint():
    """Test the /api/cameras endpoint."""
    try:
        from fastapi.testclient import TestClient

        from tapo_camera_mcp.web.server import WebServer

        # Mock config and server
        with patch("tapo_camera_mcp.web.server.get_config") as mock_get_config, patch(
            "tapo_camera_mcp.web.server.get_model"
        ), patch("tapo_camera_mcp.web.server.TapoCameraServer") as mock_server_class:
            mock_get_config.return_value = {"debug": False}
            mock_get_model.return_value = Mock()

            # Mock server instance
            mock_server_instance = AsyncMock()
            mock_server_instance.list_cameras.return_value = {"cameras": ["camera1", "camera2"]}
            mock_server_class.get_instance.return_value = mock_server_instance

            server = WebServer()
            client = TestClient(server.app)

            # Test GET /api/cameras
            response = client.get("/api/cameras")

            assert response.status_code == 200
            data = response.json()
            assert "cameras" in data

            print("✅ API cameras endpoint test passed")
            return True
    except Exception as e:
        print(f"❌ API cameras endpoint test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_api_camera_stream_endpoint():
    """Test the /api/cameras/{camera_id}/stream endpoint."""
    try:
        from fastapi.testclient import TestClient

        from tapo_camera_mcp.web.server import WebServer

        # Mock config and server
        with patch("tapo_camera_mcp.web.server.get_config") as mock_get_config, patch(
            "tapo_camera_mcp.web.server.get_model"
        ), patch("tapo_camera_mcp.web.server.TapoCameraServer") as mock_server_class:
            mock_get_config.return_value = {"debug": False}
            mock_get_model.return_value = Mock()

            # Mock server instance
            mock_server_instance = AsyncMock()
            mock_camera_manager = AsyncMock()
            mock_camera = AsyncMock()
            mock_camera.config.type.value = "tapo"
            mock_camera.get_stream_url.return_value = "rtsp://test.url"
            mock_camera_manager.cameras = {"test_camera": mock_camera}
            mock_server_instance.camera_manager = mock_camera_manager
            mock_server_class.get_instance.return_value = mock_server_instance

            server = WebServer()
            client = TestClient(server.app)

            # Test GET /api/cameras/test_camera/stream
            response = client.get("/api/cameras/test_camera/stream")

            assert response.status_code == 200
            data = response.json()
            assert "stream_url" in data
            assert data["type"] == "rtsp"

            print("✅ API camera stream endpoint test passed")
            return True
    except Exception as e:
        print(f"❌ API camera stream endpoint test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_api_camera_snapshot_endpoint():
    """Test the /api/cameras/{camera_id}/snapshot endpoint."""
    try:
        from fastapi.testclient import TestClient

        from tapo_camera_mcp.web.server import WebServer

        # Mock config and server
        with patch("tapo_camera_mcp.web.server.get_config") as mock_get_config, patch(
            "tapo_camera_mcp.web.server.get_model"
        ), patch("tapo_camera_mcp.web.server.TapoCameraServer") as mock_server_class:
            mock_get_config.return_value = {"debug": False}
            mock_get_model.return_value = Mock()

            # Mock server instance
            mock_server_instance = AsyncMock()
            mock_camera_manager = AsyncMock()
            mock_camera = AsyncMock()
            mock_camera.capture_still.return_value = Mock()  # Mock PIL Image
            mock_camera_manager.cameras = {"test_camera": mock_camera}
            mock_server_instance.camera_manager = mock_camera_manager
            mock_server_class.get_instance.return_value = mock_server_instance

            server = WebServer()
            client = TestClient(server.app)

            # Test GET /api/cameras/test_camera/snapshot
            response = client.get("/api/cameras/test_camera/snapshot")

            assert response.status_code == 200
            assert response.headers["content-type"] == "image/jpeg"

            print("✅ API camera snapshot endpoint test passed")
            return True
    except Exception as e:
        print(f"❌ API camera snapshot endpoint test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_dashboard_pages():
    """Test dashboard page routes."""
    try:
        from fastapi.testclient import TestClient

        from tapo_camera_mcp.web.server import WebServer

        # Mock config
        with patch("tapo_camera_mcp.web.server.get_config") as mock_get_config, patch(
            "tapo_camera_mcp.web.server.get_model"
        ):
            mock_get_config.return_value = {"debug": False}
            mock_get_model.return_value = Mock()

            server = WebServer()
            client = TestClient(server.app)

            # Test main dashboard page
            response = client.get("/")
            assert response.status_code == 200
            assert "dashboard" in response.text.lower()

            # Test cameras page
            response = client.get("/cameras")
            assert response.status_code == 200

            # Test settings page
            response = client.get("/settings")
            assert response.status_code == 200

            # Test help page
            response = client.get("/help")
            assert response.status_code == 200

            print("✅ Dashboard pages test passed")
            return True
    except Exception as e:
        print(f"❌ Dashboard pages test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_error_handling():
    """Test error handling for API and web routes."""
    try:
        from fastapi.testclient import TestClient

        from tapo_camera_mcp.web.server import WebServer

        # Mock config
        with patch("tapo_camera_mcp.web.server.get_config") as mock_get_config, patch(
            "tapo_camera_mcp.web.server.get_model"
        ):
            mock_get_config.return_value = {"debug": False}
            mock_get_model.return_value = Mock()

            server = WebServer()
            client = TestClient(server.app)

            # Test API 404
            response = client.get("/api/nonexistent")
            assert response.status_code == 404
            data = response.json()
            assert "detail" in data

            # Test web 404
            response = client.get("/nonexistent")
            assert response.status_code == 404

            print("✅ Error handling test passed")
            return True
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_middleware_functionality():
    """Test middleware functionality (CORS, security headers, etc.)."""
    try:
        from fastapi.testclient import TestClient

        from tapo_camera_mcp.web.server import WebServer

        # Mock config with CORS enabled
        with patch("tapo_camera_mcp.web.server.get_config") as mock_get_config, patch(
            "tapo_camera_mcp.web.server.get_model"
        ) as mock_get_model:
            mock_config = {"debug": False}
            mock_web_config = Mock()
            mock_web_config.enable_cors = True
            mock_web_config.cors_origins = ["http://localhost:3000"]
            mock_security_config = Mock()

            mock_get_config.return_value = mock_config
            mock_get_model.side_effect = lambda cls: (
                mock_web_config if cls.__name__ == "WebUISettings" else mock_security_config
            )

            server = WebServer()
            client = TestClient(server.app)

            # Test CORS preflight request
            response = client.options(
                "/api/status",
                headers={
                    "Origin": "http://localhost:3000",
                    "Access-Control-Request-Method": "GET",
                    "Access-Control-Request-Headers": "Content-Type",
                },
            )

            # CORS headers should be present
            assert "Access-Control-Allow-Origin" in response.headers

            # Test security headers on normal request
            response = client.get("/api/status")
            assert "X-Content-Type-Options" in response.headers
            assert "X-Frame-Options" in response.headers
            assert "X-XSS-Protection" in response.headers

            print("✅ Middleware functionality test passed")
            return True
    except Exception as e:
        print(f"❌ Middleware functionality test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_template_rendering():
    """Test template rendering with context variables."""
    try:
        from fastapi.testclient import TestClient

        from tapo_camera_mcp.web.server import WebServer

        # Mock config
        with patch("tapo_camera_mcp.web.server.get_config") as mock_get_config, patch(
            "tapo_camera_mcp.web.server.get_model"
        ) as mock_get_model:
            mock_config = {"debug": False}
            mock_web_config = Mock()
            mock_web_config.title = "Test Camera MCP"
            mock_web_config.theme = "dark"
            mock_security_config = Mock()

            mock_get_config.return_value = mock_config
            mock_get_model.side_effect = lambda cls: (
                mock_web_config if cls.__name__ == "WebUISettings" else mock_security_config
            )

            server = WebServer()
            client = TestClient(server.app)

            # Test that templates have the correct global variables
            response = client.get("/")
            assert response.status_code == 200

            # Check that template globals are available (this is harder to test directly,
            # but we can check that the response contains expected content)
            content = response.text.lower()
            assert "test camera mcp" in content or "tapo camera mcp" in content

            print("✅ Template rendering test passed")
            return True
    except Exception as e:
        print(f"❌ Template rendering test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    tests = [
        test_web_server_initialization,
        test_api_status_endpoint,
        test_api_cameras_endpoint,
        test_api_camera_stream_endpoint,
        test_api_camera_snapshot_endpoint,
        test_dashboard_pages,
        test_error_handling,
        test_middleware_functionality,
        test_template_rendering,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1
        print()

    print(f"📊 Results: {passed}/{total} web dashboard and API tests passed")

    if passed == total:
        print("🎉 All web dashboard and API tests passed!")
        sys.exit(0)
    else:
        print("❌ Some web dashboard and API tests failed")
        sys.exit(1)
