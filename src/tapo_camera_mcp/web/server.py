"""
Web server module for Tapo Camera MCP.

This module provides the web server implementation using FastAPI.
"""

import logging
from pathlib import Path
from typing import Generator, Optional

from fastapi import FastAPI, Form, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import (
    HTMLResponse,
    JSONResponse,
    RedirectResponse,
    Response,
    StreamingResponse,
)
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException

from ..config import SecuritySettings, WebUISettings, get_config, get_model
from ..utils.logging import setup_logging

# Setup logging
logger = logging.getLogger(__name__)


class WebServer:
    """Web server for Tapo Camera MCP."""

    def __init__(self, config_path: Optional[str] = None):  # noqa: ARG002
        """Initialize the web server.

        Args:
            config_path: Optional path to the configuration file.
        """
        self.config = get_config()
        self.web_config = get_model(WebUISettings)
        self.security_config = get_model(SecuritySettings)

        # Initialize FastAPI app
        self.app = FastAPI(
            title="Tapo Camera MCP",
            description="Management and Control Platform for Tapo Cameras",
            version="1.0.0",
            docs_url="/api/docs" if self.web_config.enable_swagger else None,
            redoc_url="/api/redoc" if self.web_config.enable_redoc else None,
            debug=self.config.get("debug", False),
        )

        # Setup middleware
        self._setup_middleware()

        # Setup exception handlers
        self._setup_exception_handlers()

        # Setup routes
        self._setup_routes()

        # Setup templates
        self.templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
        self.templates.env.globals.update(
            {
                "app_title": self.web_config.title,
                "app_version": "1.0.0",
                "theme": self.web_config.theme,
            }
        )

    def _setup_middleware(self) -> None:
        """Setup middleware for the FastAPI app."""
        # CORS middleware
        if self.web_config.enable_cors:
            self.app.add_middleware(
                CORSMiddleware,
                allow_origins=self.web_config.cors_origins,
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )

        # GZip middleware
        self.app.add_middleware(GZipMiddleware, minimum_size=1000)

        # Security headers middleware
        @self.app.middleware("http")
        async def add_security_headers(request: Request, call_next):
            response = await call_next(request)
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:;"
            )
            return response

    def _setup_exception_handlers(self) -> None:
        """Setup exception handlers for the FastAPI app."""

        @self.app.exception_handler(StarletteHTTPException)
        async def http_exception_handler(request: Request, exc: StarletteHTTPException):
            if request.url.path.startswith("/api/"):
                return JSONResponse(
                    status_code=exc.status_code,
                    content={"detail": exc.detail},
                )

            # For non-API routes, show a nice error page
            return self.templates.TemplateResponse(
                "error.html",
                {
                    "request": request,
                    "status_code": exc.status_code,
                    "detail": exc.detail,
                },
                status_code=exc.status_code,
            )

        @self.app.exception_handler(RequestValidationError)
        async def validation_exception_handler(request: Request, exc: RequestValidationError):
            if request.url.path.startswith("/api/"):
                return JSONResponse(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    content={"detail": exc.errors(), "body": exc.body},
                )

            # For non-API routes, redirect to home with error message
            return RedirectResponse(
                url="/?error=invalid_request", status_code=status.HTTP_303_SEE_OTHER
            )

    async def cameras_page(self, request: Request):
        """Serve the cameras page with detailed camera information."""
        cameras_data = []

        try:
            from tapo_camera_mcp.core.server import TapoCameraServer

            server = await TapoCameraServer.get_instance()

            # Get cameras list with detailed information
            cameras_list = await server.camera_manager.list_cameras()

            # Enhance each camera with additional details
            for camera in cameras_list:
                camera_info = dict(camera)  # Copy base info

                # Try to get detailed camera information
                try:
                    if camera.get("status") == "online":
                        # Get detailed camera info if available
                        camera_obj = await server.camera_manager.get_camera(camera["name"])
                        if camera_obj:
                            # Get detailed status including capabilities
                            detailed_status = await camera_obj.get_status()

                            # Add resolution info (mock for now, would come from camera)
                            camera_info["resolution"] = detailed_status.get("resolution", "Unknown")

                            # Add PTZ capability
                            camera_info["ptz_capable"] = detailed_status.get("ptz_capable", False)

                            # Add audio capability
                            camera_info["audio_capable"] = detailed_status.get(
                                "audio_capable", False
                            )

                            # Add model and firmware
                            camera_info["model"] = detailed_status.get("model", "Unknown")
                            camera_info["firmware"] = detailed_status.get("firmware", "Unknown")

                            # Add streaming capability
                            camera_info["streaming_capable"] = detailed_status.get(
                                "streaming", False
                            )
                        else:
                            camera_info.update(
                                {
                                    "resolution": "Unknown",
                                    "ptz_capable": False,
                                    "audio_capable": False,
                                    "model": "Unknown",
                                    "firmware": "Unknown",
                                    "streaming_capable": False,
                                }
                            )
                    else:
                        # Offline camera - set defaults
                        camera_info.update(
                            {
                                "resolution": "N/A",
                                "ptz_capable": False,
                                "audio_capable": False,
                                "model": "N/A",
                                "firmware": "N/A",
                                "streaming_capable": False,
                            }
                        )
                except Exception as e:
                    logger.warning(
                        f"Could not get detailed info for camera {camera.get('name', 'unknown')}: {e}"
                    )
                    camera_info.update(
                        {
                            "resolution": "Error",
                            "ptz_capable": False,
                            "audio_capable": False,
                            "model": "Error",
                            "firmware": "Error",
                            "streaming_capable": False,
                        }
                    )

                cameras_data.append(camera_info)

        except Exception:
            logger.exception("Error getting cameras data")
            cameras_data = []

        return self.templates.TemplateResponse(
            "cameras.html",
            {
                "request": request,
                "active_page": "cameras",
                "cameras": cameras_data,
                "total_cameras": len(cameras_data),
                "online_cameras": sum(1 for cam in cameras_data if cam.get("status") == "online"),
            },
        )

    async def settings_page(self, request: Request):
        """Serve the settings page."""
        # Get camera count
        try:
            from tapo_camera_mcp.core.server import TapoCameraServer

            server = await TapoCameraServer.get_instance()
            cameras = await server.camera_manager.list_cameras()
            total_cameras = len(cameras)
        except Exception as e:
            logger.warning(f"Error getting camera count for settings: {e}")
            total_cameras = 0

        return self.templates.TemplateResponse(
            "settings.html",
            {
                "request": request,
                "active_page": "settings",
                "config": self.config,
                "total_cameras": total_cameras,
            },
        )

    def _setup_routes(self) -> None:
        """Setup routes for the FastAPI app."""
        # Mount static files
        static_dir = Path(__file__).parent / "static"
        self.app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

        # API routes
        @self.app.get("/api/status")
        async def get_status():
            """Get server status."""
            return {
                "status": "ok",
                "version": "1.0.0",
                "debug": self.config.get("debug", False),
            }

        @self.app.get("/api/cameras")
        async def get_cameras():
            """Get list of cameras."""
            try:
                from tapo_camera_mcp.core.server import TapoCameraServer

                server = await TapoCameraServer.get_instance()
                return await server.list_cameras()
            except Exception as e:
                return {"success": False, "error": str(e), "cameras": []}

        @self.app.get("/api/cameras/{camera_id}/stream")
        async def get_camera_stream(camera_id: str):
            """Get camera video stream."""
            try:
                from tapo_camera_mcp.core.server import TapoCameraServer

                server = await TapoCameraServer.get_instance()

                if hasattr(server, "camera_manager") and server.camera_manager:
                    camera = server.camera_manager.cameras.get(camera_id)
                    if camera:
                        # Get camera type as string
                        camera_type = camera.config.type
                        if hasattr(camera_type, "value"):
                            camera_type = camera_type.value

                        # For webcam, return MJPEG stream
                        if camera_type == "webcam":
                            return StreamingResponse(
                                self._generate_webcam_stream(camera),
                                media_type="multipart/x-mixed-replace; boundary=frame",
                            )
                        # For Tapo cameras, return RTSP stream URL
                        if camera_type == "tapo":
                            stream_url = await camera.get_stream_url()
                            if stream_url:
                                return {"stream_url": stream_url, "type": "rtsp"}

                return {"error": "Camera not found or not supported"}
            except Exception as e:
                return {"error": str(e)}

        @self.app.get("/api/cameras/{camera_id}/snapshot")
        async def get_camera_snapshot(camera_id: str):
            """Get camera snapshot."""
            try:
                from tapo_camera_mcp.core.server import TapoCameraServer

                server = await TapoCameraServer.get_instance()

                if hasattr(server, "camera_manager") and server.camera_manager:
                    camera = server.camera_manager.cameras.get(camera_id)
                    if camera:
                        image = await camera.capture_still()

                        # Convert to bytes
                        import io

                        buffer = io.BytesIO()
                        image.save(buffer, format="JPEG", quality=75)
                        image_bytes = buffer.getvalue()

                        return Response(content=image_bytes, media_type="image/jpeg")

                return Response(content="Camera not found", status_code=404)
            except Exception as e:
                return Response(content=f"Error: {e!s}", status_code=500)

        # Camera control endpoints
        @self.app.post("/api/cameras/{camera_id}/control")
        async def control_camera(camera_id: str, action: str = Form(...)):
            """Control camera actions (start_stream, stop_stream, start_audio, stop_audio)."""
            try:
                from tapo_camera_mcp.core.server import TapoCameraServer

                server = await TapoCameraServer.get_instance()

                if hasattr(server, "camera_manager") and server.camera_manager:
                    camera = server.camera_manager.cameras.get(camera_id)
                    if camera:
                        if action == "start_stream":
                            # Start streaming
                            stream_url = await camera.get_stream_url()
                            return {"success": True, "stream_url": stream_url}

                        if action == "stop_stream":
                            # Stop streaming
                            await camera.disconnect()
                            return {"success": True}

                        if action == "start_audio":
                            # Start audio recording (this is client-side)
                            return {
                                "success": True,
                                "message": "Audio recording started on client",
                            }

                        if action == "stop_audio":
                            # Stop audio recording (this is client-side)
                            return {
                                "success": True,
                                "message": "Audio recording stopped on client",
                            }

                        if action == "snapshot":
                            # Take snapshot
                            image = await camera.capture_still()
                            import io

                            buffer = io.BytesIO()
                            image.save(buffer, format="JPEG", quality=75)
                            image_bytes = buffer.getvalue()

                            return Response(content=image_bytes, media_type="image/jpeg")

                return {"error": "Camera not found"}
            except Exception as e:
                return {"error": str(e)}

        # Web UI routes
        @self.app.get("/", response_class=HTMLResponse, name="dashboard")
        async def index(request: Request):
            """Serve the main dashboard page."""
            # Initialize variables to avoid undefined errors in template
            cameras = []
            online_cameras = 0
            total_cameras = 0
            security_devices = []
            security_alerts = []
            security_overview = {}

            try:
                # Get real camera data from the MCP server
                from tapo_camera_mcp.core.server import TapoCameraServer

                server = await TapoCameraServer.get_instance()

                # Get camera list from camera manager
                cameras = await server.camera_manager.list_cameras()
                total_cameras = len(cameras)
                online_cameras = sum(1 for cam in cameras if cam.get("status") == "online")

                # If no cameras configured, try to auto-add USB webcam
                if total_cameras == 0:
                    try:
                        logger.info("No cameras configured, attempting to auto-add USB webcam...")
                        config = {
                            "name": "usb_webcam_0",
                            "type": "webcam",
                            "params": {"device_id": 0},
                        }
                        success = await server.camera_manager.add_camera(config)
                        if success:
                            logger.info("Successfully auto-added USB webcam")
                            # Refresh camera list
                            cameras = await server.camera_manager.list_cameras()
                            total_cameras = len(cameras)
                            online_cameras = sum(
                                1 for cam in cameras if cam.get("status") == "online"
                            )
                        else:
                            logger.warning(
                                "Failed to auto-add webcam: camera manager returned False"
                            )
                    except Exception as e:
                        logger.warning(f"Error auto-adding webcam: {e}")

                # Get security system data
                security_devices = []
                security_alerts = []
                security_overview = {}

                try:
                    from tapo_camera_mcp.security import security_manager

                    # Initialize security integrations if not already done
                    if not hasattr(security_manager, "_initialized"):
                        security_config = (
                            self.security_config.integrations.dict() if self.security_config else {}
                        )
                        await security_manager.initialize(security_config)
                        security_manager._initialized = True

                    # Get security data
                    security_devices = await security_manager.get_all_devices()
                    security_alerts = await security_manager.get_all_alerts()
                    security_overview = await security_manager.get_system_overview()

                except Exception as e:
                    logger.warning(f"Failed to get security data for dashboard: {e}")
                    # Variables already initialized above, just log the error

            except Exception as e:
                logger.warning(f"Failed to get camera data for dashboard: {e}")
                # Variables already initialized above

            return self.templates.TemplateResponse(
                "simple_dashboard.html",
                {
                    "request": request,
                    "active_page": "dashboard",
                    "online_cameras": online_cameras,
                    "total_cameras": total_cameras,
                    "storage_used": 45,  # Mock data for now
                    "active_alerts": len(security_alerts),
                    "active_recordings": 0,
                    "cameras": cameras,
                    "security_devices": [device.__dict__ for device in security_devices],
                    "security_alerts": [alert.__dict__ for alert in security_alerts],
                    "security_overview": security_overview,
                },
            )

        @self.app.get("/list_cameras", response_class=HTMLResponse, name="list_cameras")
        async def list_cameras(request: Request):
            """Serve the cameras list page."""
            return self.templates.TemplateResponse(
                "dashboard.html", {"request": request, "active_page": "cameras"}
            )

        @self.app.get("/recordings", response_class=HTMLResponse, name="recordings")
        async def recordings(request: Request):
            """Serve the recordings page."""
            # Mock data for demonstration - in a real implementation, this would come from a database
            recordings = []  # Empty for now since we don't have actual recordings
            total_recordings = 0
            today_recordings = 0
            storage_used = "0GB"
            storage_free = "50GB"  # Mock data

            return self.templates.TemplateResponse(
                "recordings.html",
                {
                    "request": request,
                    "active_page": "recordings",
                    "recordings": recordings,
                    "total_recordings": total_recordings,
                    "today_recordings": today_recordings,
                    "storage_used": storage_used,
                    "storage_free": storage_free,
                },
            )

        @self.app.get("/events", response_class=HTMLResponse, name="events")
        async def events(request: Request):
            """Serve the events page."""
            return self.templates.TemplateResponse(
                "dashboard.html", {"request": request, "active_page": "events"}
            )

        @self.app.get("/help", response_class=HTMLResponse, name="help")
        async def help_page(request: Request):
            """Serve the help and documentation page."""
            return self.templates.TemplateResponse(
                "help.html", {"request": request, "active_page": "help"}
            )

        # 404 handler
        @self.app.exception_handler(404)
        async def not_found(request: Request, exc: StarletteHTTPException):  # noqa: ARG001
            if request.url.path.startswith("/api/"):
                return JSONResponse(
                    status_code=404,
                    content={"detail": "Not Found"},
                )

            return self.templates.TemplateResponse(
                "404.html", {"request": request}, status_code=404
            )

        # Register the page routes (defined as class methods)
        self.app.add_api_route(
            "/cameras",
            self.cameras_page,
            methods=["GET"],
            response_class=HTMLResponse,
            name="cameras",
        )
        self.app.add_api_route(
            "/settings",
            self.settings_page,
            methods=["GET"],
            response_class=HTMLResponse,
            name="settings",
        )

        # Settings API endpoints
        @self.app.get("/api/settings")
        async def get_settings():
            """Get current settings."""
            try:
                from tapo_camera_mcp.config import get_config

                config = get_config()

                # Get camera count
                camera_count = 0
                try:
                    from tapo_camera_mcp.core.server import TapoCameraServer

                    server = await TapoCameraServer.get_instance()
                    cameras = await server.camera_manager.list_cameras()
                    camera_count = len(cameras)
                except Exception as exc:
                    logger.debug("Failed to get camera count: %s", exc)

                return {
                    "status": "success",
                    "settings": {
                        "server_port": config.get("server", {}).get("port", 8000),
                        "debug": config.get("debug", False),
                        "log_level": config.get("log_level", "INFO"),
                        "web_enabled": config.get("web", {}).get("enabled", True),
                        "web_port": config.get("web", {}).get("port", 7777),
                        "theme": config.get("web", {}).get("theme", "dark"),
                        "cors_enabled": config.get("web", {}).get("enable_cors", True),
                        "auth_enabled": config.get("auth", {}).get("enabled", False),
                        "total_cameras": camera_count,
                    },
                }
            except Exception as e:
                return {"status": "error", "message": str(e)}

        @self.app.post("/api/settings")
        async def save_settings(settings: dict):
            """Save settings."""
            try:
                # For now, just acknowledge the settings
                # In a real implementation, this would save to config file
                logger.info(f"Settings update requested: {settings}")
                return {"status": "success", "message": "Settings saved successfully"}
            except Exception as e:
                logger.exception("Error saving settings")
                return {"status": "error", "message": str(e)}

    async def _generate_webcam_stream(self, camera) -> Generator[bytes, None, None]:
        """Generate MJPEG stream from webcam."""
        try:
            import asyncio

            import cv2

            # Ensure camera is connected
            if not await camera.is_connected():
                await camera.connect()

            # Get OpenCV VideoCapture from webcam
            if hasattr(camera, "_cap") and camera._cap:
                cap = camera._cap

                while True:
                    ret, frame = cap.read()
                    if not ret:
                        break

                    # Encode frame as JPEG
                    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 80]
                    result, encoded_img = cv2.imencode(".jpg", frame, encode_param)

                    if result:
                        # Create MJPEG frame
                        yield (
                            b"--frame\r\n"
                            b"Content-Type: image/jpeg\r\n\r\n" + encoded_img.tobytes() + b"\r\n"
                        )

                    # Control frame rate
                    await asyncio.sleep(0.033)  # ~30 FPS

        except Exception:
            logger.exception("Error generating webcam stream")
            # Send error frame
            error_frame = (
                b"--frame\r\nContent-Type: image/jpeg\r\n\r\n"
                + b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.' \",#\x1c\x1c(7),01444\x1f'9=82<.342\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x01\x01\x11\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00\x3f\x00\xaa\xff\xd9"
                + b"\r\n"
            )
            yield error_frame

    def run(self, host: Optional[str] = None, port: Optional[int] = None):
        """Run the web server.

        Args:
            host: Host to bind to. Defaults to config value.
            port: Port to bind to. Defaults to config value.
        """
        import uvicorn

        host = host or self.web_config.host
        port = port or self.web_config.port

        logger.info(f"Starting web server on http://{host}:{port}")

        uvicorn.run(
            self.app,
            host=host,
            port=port,
            log_level=self.config.get("log_level", "info").lower(),
            reload=self.config.get("debug", False),
            workers=1,  # Running with multiple workers can cause issues with in-memory state
        )


# For running the server directly
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Tapo Camera MCP Web Server")
    parser.add_argument(
        "--host", default=None, help="Host to bind the server to (default: from config)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Port to bind the server to (default: from config)",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    args = parser.parse_args()

    # Setup logging
    setup_logging()

    # Create and run the server
    server = WebServer()

    # Override config with command line args if provided
    host = args.host
    port = args.port

    server.run(host=host, port=port)
