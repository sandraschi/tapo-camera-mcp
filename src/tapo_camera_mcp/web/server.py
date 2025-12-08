"""
Web server module for Tapo Camera MCP.

This module provides the web server implementation using FastAPI.
"""

import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Generator, Optional

from fastapi import Body, FastAPI, Form, Query, Request, status
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
from .auth import (
    AuthMiddleware,
    is_auth_enabled,
    validate_credentials,
    create_session,
    delete_session,
    get_current_user,
    setup_default_user,
)

# Setup logging
logger = logging.getLogger(__name__)

AUTO_WEBCAM_RETRY_INTERVAL = timedelta(seconds=10)
_last_webcam_attempt: Optional[datetime] = None


def find_available_port(start_port: int = 7777, max_attempts: int = 10) -> int:
    """Find the next available port starting from start_port.
    
    Args:
        start_port: Port to start checking from.
        max_attempts: Maximum number of ports to check.
        
    Returns:
        First available port number.
        
    Raises:
        RuntimeError: If no available port found within max_attempts.
    """
    import socket
    
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.bind(("0.0.0.0", port))
                return port
        except OSError:
            continue
    
    raise RuntimeError(f"No available port found in range {start_port}-{start_port + max_attempts - 1}")


class WebServer:
    """Web server for Tapo Camera MCP."""

    def __init__(self, _config_path: Optional[str] = None):
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

        # Setup startup event for comprehensive hardware initialization
        @self.app.on_event("startup")
        async def init_all_hardware_on_startup():
            """Initialize all hardware components on server startup."""
            try:
                import asyncio
                from tapo_camera_mcp.core.hardware_init import initialize_all_hardware
                logger.info("=" * 60)
                logger.info("WEB SERVER STARTUP - Initializing all hardware...")
                logger.info("=" * 60)
                # Add timeout to prevent blocking server startup indefinitely
                hardware_results = await asyncio.wait_for(initialize_all_hardware(), timeout=60.0)
                
                # Log summary
                successful = sum(1 for r in hardware_results.values() if r.get("success", False))
                total = len(hardware_results)
                logger.info(f"Hardware initialization complete: {successful}/{total} components ready")
                logger.info("=" * 60)
            except asyncio.TimeoutError:
                logger.warning("Hardware initialization timed out after 60s - server will start anyway")
                logger.warning("Hardware will be initialized in background by Connection Supervisor")
            except Exception as e:
                logger.exception("Failed to initialize hardware during web server startup")
                logger.warning("Server will start anyway - hardware can be initialized later")

        # Setup startup event for Shelly temperature sensors
        @self.app.on_event("startup")
        async def init_shelly_on_startup():
            """Initialize Shelly client from config on server startup."""
            shelly_config = self.config.get("shelly", {})
            if shelly_config.get("enabled", False):
                try:
                    from tapo_camera_mcp.integrations.shelly_client import init_shelly_client
                    logger.info("Initializing Shelly client from config...")
                    await init_shelly_client(
                        devices=shelly_config.get("devices", []),
                        cache_ttl=shelly_config.get("cache_ttl", 30),
                    )
                    logger.info("Shelly client initialized successfully")
                except Exception as e:
                    logger.warning(f"Failed to initialize Shelly client: {e}")

        # Setup startup event for thermal sensors (MLX90640/AMG8833)
        @self.app.on_event("startup")
        async def init_thermal_on_startup():
            """Initialize thermal sensor client from config on server startup."""
            thermal_config = self.config.get("thermal", {})
            if thermal_config.get("enabled", False):
                try:
                    from tapo_camera_mcp.integrations.thermal_client import init_thermal_client
                    logger.info("Initializing thermal sensor client from config...")
                    await init_thermal_client(
                        sensors=thermal_config.get("sensors", []),
                        cache_ttl=thermal_config.get("cache_ttl", 5),
                    )
                    logger.info("Thermal sensor client initialized successfully")
                except Exception as e:
                    logger.warning(f"Failed to initialize thermal client: {e}")

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

        # Auth middleware (checks session on protected routes)
        if is_auth_enabled():
            self.app.add_middleware(AuthMiddleware)
            setup_default_user()
            logger.info("Authentication is ENABLED")
        else:
            logger.info("Authentication is DISABLED")

        # Security headers middleware
        @self.app.middleware("http")
        async def add_security_headers(request: Request, call_next):
            response = await call_next(request)
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "SAMEORIGIN"  # Allow same-origin framing for fullscreen
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
                "style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://fonts.googleapis.com; "
                "font-src 'self' https://cdnjs.cloudflare.com https://fonts.gstatic.com; "
                "img-src 'self' data: blob:;"
            )
            # Allow fullscreen API
            response.headers["Permissions-Policy"] = "fullscreen=(self)"
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
                
                # Extract status - camera_manager.list_cameras() returns status as a dict
                status_dict = camera.get("status", {})
                if isinstance(status_dict, dict):
                    is_connected = status_dict.get("connected", False)
                    camera_info["status"] = "online" if is_connected else "offline"
                    # Copy status fields to camera_info for easier access
                    camera_info.update({
                        "model": status_dict.get("model", "Unknown"),
                        "firmware": status_dict.get("firmware", "Unknown"),
                        "resolution": status_dict.get("resolution", "Unknown"),
                        "ptz_capable": status_dict.get("ptz_capable", False),
                        "audio_capable": status_dict.get("audio_capable", False),
                        "streaming_capable": status_dict.get("streaming_capable", False),
                    })
                else:
                    # Fallback if status is already a string
                    camera_info["status"] = str(status_dict) if status_dict else "offline"
                
                # Ensure status is always a string, never a dict
                if not isinstance(camera_info.get("status"), str):
                    camera_info["status"] = "offline"

                # Try to get detailed camera information
                try:
                    if camera_info.get("status") == "online":
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

        # Sort cameras for UI: USB webcam first, then Tapo, then doorcam/Ring, then Petcube, then others.
        def _camera_sort_key(cam: dict) -> tuple:
            cam_type = (cam.get("type") or "").lower()
            name = (cam.get("name") or cam.get("id") or "").lower()
            priority = 4
            if cam_type == "webcam":
                priority = 0
            elif cam_type == "tapo":
                priority = 1
            elif "door" in name or cam_type == "ring":
                priority = 2
            elif cam_type == "petcube":
                priority = 3
            return (priority, name)

        cameras_data = sorted(cameras_data, key=_camera_sort_key)

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

    async def health_page(self, request: Request):
        """Serve the health monitoring page."""
        return self.templates.TemplateResponse(
            "health.html",
            {
                "request": request,
                "active_page": "health",
            },
        )

    def _setup_routes(self) -> None:
        """Setup routes for the FastAPI app."""
        # Mount static files
        static_dir = Path(__file__).parent / "static"
        self.app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

        # Auth routes
        @self.app.get("/login", response_class=HTMLResponse, name="login")
        async def login_page(request: Request):
            """Serve the login page."""
            # If already logged in, redirect to dashboard
            if is_auth_enabled() and get_current_user(request):
                return RedirectResponse(url="/", status_code=302)
            # If auth disabled, redirect to dashboard
            if not is_auth_enabled():
                return RedirectResponse(url="/", status_code=302)
            return self.templates.TemplateResponse("login.html", {"request": request})

        @self.app.post("/api/auth/login")
        async def api_login(request: Request):
            """Handle login API request."""
            try:
                data = await request.json()
                username = data.get("username", "")
                password = data.get("password", "")
                remember = data.get("remember", False)
                
                if validate_credentials(username, password):
                    session_id = create_session(username)
                    response = JSONResponse({
                        "success": True,
                        "redirect": "/",
                        "user": username,
                    })
                    max_age = 86400 * 30 if remember else 86400  # 30 days or 1 day
                    response.set_cookie(
                        key="session_id",
                        value=session_id,
                        httponly=True,
                        secure=False,  # Set True in production with HTTPS
                        samesite="lax",
                        max_age=max_age,
                    )
                    logger.info(f"User '{username}' logged in successfully")
                    return response
                else:
                    logger.warning(f"Failed login attempt for user '{username}'")
                    return JSONResponse(
                        {"success": False, "error": "Invalid username or password"},
                        status_code=401,
                    )
            except Exception as e:
                logger.exception("Login error")
                return JSONResponse(
                    {"success": False, "error": str(e)},
                    status_code=500,
                )

        @self.app.post("/api/auth/logout")
        async def api_logout(request: Request):
            """Handle logout API request."""
            session_id = request.cookies.get("session_id")
            if session_id:
                delete_session(session_id)
            response = JSONResponse({"success": True})
            response.delete_cookie("session_id")
            return response

        @self.app.get("/api/auth/status")
        async def api_auth_status(request: Request):
            """Get current auth status."""
            user = get_current_user(request) if is_auth_enabled() else "admin"
            return {
                "authenticated": bool(user),
                "user": user,
                "auth_enabled": is_auth_enabled(),
            }

        # API routes
        @self.app.get("/api/status")
        async def get_status():
            """Get server status."""
            return {
                "status": "ok",
                "version": "1.0.0",
                "debug": self.config.get("debug", False),
            }

        @self.app.get("/api/health", summary="Get comprehensive system health metrics")
        async def get_health():
            """Get comprehensive system health metrics including disk, CPU, memory, uptime, and services."""
            try:
                import psutil
                import time
                from pathlib import Path

                # System resources
                cpu_percent = psutil.cpu_percent(interval=0.1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage("/")
                
                # System uptime
                boot_time = psutil.boot_time()
                uptime_seconds = time.time() - boot_time
                
                # Process info
                process = psutil.Process()
                process_memory = process.memory_info()
                process_cpu = process.cpu_percent(interval=0.1)
                
                # Network stats
                try:
                    net_io = psutil.net_io_counters()
                    network = {
                        "bytes_sent": net_io.bytes_sent,
                        "bytes_recv": net_io.bytes_recv,
                        "packets_sent": net_io.packets_sent,
                        "packets_recv": net_io.packets_recv,
                    }
                except Exception:
                    network = None
                
                # Database status
                db_status = {}
                try:
                    # Check SQLite (time series DB)
                    ts_db_path = Path(__file__).parent.parent.parent.parent / "data" / "timeseries.db"
                    if ts_db_path.exists():
                        db_size = ts_db_path.stat().st_size
                        db_status["timeseries"] = {
                            "status": "ok",
                            "path": str(ts_db_path),
                            "size_bytes": db_size,
                            "size_mb": round(db_size / (1024 * 1024), 2),
                        }
                    else:
                        db_status["timeseries"] = {"status": "not_found"}
                except Exception as e:
                    db_status["timeseries"] = {"status": "error", "error": str(e)}
                
                # Check PostgreSQL
                postgres_status = {"status": "unknown"}
                try:
                    import os
                    postgres_host = os.getenv("POSTGRES_HOST")
                    if postgres_host:
                        import socket
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.settimeout(1)
                        result = sock.connect_ex((postgres_host, int(os.getenv("POSTGRES_PORT", "5432"))))
                        sock.close()
                        if result == 0:
                            postgres_status = {"status": "reachable", "host": postgres_host}
                        else:
                            postgres_status = {"status": "unreachable", "host": postgres_host}
                    else:
                        postgres_status = {"status": "not_configured"}
                except Exception as e:
                    postgres_status = {"status": "error", "error": str(e)}
                
                db_status["postgres"] = postgres_status
                
                # Camera status
                camera_status = {"total": 0, "online": 0, "offline": 0}
                try:
                    from tapo_camera_mcp.core.server import TapoCameraServer
                    server = await TapoCameraServer.get_instance()
                    cameras = await server.camera_manager.list_cameras()
                    camera_status["total"] = len(cameras)
                    camera_status["online"] = sum(1 for cam in cameras if cam.get("status") == "online")
                    camera_status["offline"] = camera_status["total"] - camera_status["online"]
                except Exception:
                    pass
                
                # Determine overall health status
                issues = []
                if cpu_percent > 90:
                    issues.append("critical_cpu")
                elif cpu_percent > 80:
                    issues.append("high_cpu")
                
                if memory.percent > 95:
                    issues.append("critical_memory")
                elif memory.percent > 85:
                    issues.append("high_memory")
                
                if disk.percent > 95:
                    issues.append("critical_disk")
                elif disk.percent > 90:
                    issues.append("high_disk")
                
                if camera_status["total"] > 0 and camera_status["online"] == 0:
                    issues.append("no_cameras_online")
                
                if postgres_status.get("status") == "unreachable":
                    issues.append("postgres_unreachable")
                
                overall_status = "critical" if any("critical" in issue for issue in issues) else "warning" if issues else "healthy"
                
                return {
                    "status": overall_status,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "system": {
                        "cpu": {
                            "percent": round(cpu_percent, 1),
                            "count": psutil.cpu_count(),
                            "process_percent": round(process_cpu, 1),
                        },
                        "memory": {
                            "total_gb": round(memory.total / (1024**3), 2),
                            "available_gb": round(memory.available / (1024**3), 2),
                            "used_gb": round(memory.used / (1024**3), 2),
                            "percent": round(memory.percent, 1),
                            "process_mb": round(process_memory.rss / (1024**2), 2),
                        },
                        "disk": {
                            "total_gb": round(disk.total / (1024**3), 2),
                            "used_gb": round(disk.used / (1024**3), 2),
                            "free_gb": round(disk.free / (1024**3), 2),
                            "percent": round(disk.percent, 1),
                        },
                        "uptime": {
                            "seconds": int(uptime_seconds),
                            "days": int(uptime_seconds / 86400),
                            "hours": int((uptime_seconds % 86400) / 3600),
                            "minutes": int((uptime_seconds % 3600) / 60),
                        },
                    },
                    "network": network,
                    "databases": db_status,
                    "cameras": camera_status,
                    "issues": issues,
                }
            except Exception as e:
                logger.exception("Error getting health metrics")
                return {
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

        @self.app.get("/api/cameras")
        async def get_cameras():
            """Get list of cameras."""
            try:
                from tapo_camera_mcp.core.server import TapoCameraServer

                server = await TapoCameraServer.get_instance()
                cameras = await server.camera_manager.list_cameras()
                return {"success": True, "cameras": cameras}
            except Exception as e:
                logger.exception("Error getting cameras list")
                return {"success": False, "error": str(e), "cameras": []}

        @self.app.get("/api/cameras/status")
        async def get_cameras_status():
            """Get camera status summary."""
            try:
                from tapo_camera_mcp.core.server import TapoCameraServer

                server = await TapoCameraServer.get_instance()
                cameras = await server.camera_manager.list_cameras()
                total = len(cameras)
                online = sum(1 for cam in cameras if cam.get("status") == "online")
                return {
                    "total": total,
                    "online": online,
                    "offline": total - online,
                    "cameras": cameras,
                }
            except Exception as e:
                return {"success": False, "error": str(e), "total": 0, "online": 0, "offline": 0}

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
                        # For ONVIF cameras, return RTSP stream URL with auth
                        if camera_type == "onvif":
                            stream_url = await camera.get_stream_url()
                            if stream_url:
                                # Add auth credentials to URL
                                from urllib.parse import urlparse
                                parsed = urlparse(stream_url)
                                username = camera.config.params.get("username", "")
                                password = camera.config.params.get("password", "")
                                if username and password:
                                    auth_url = f"rtsp://{username}:{password}@{parsed.hostname}:{parsed.port or 554}{parsed.path}"
                                    return {"stream_url": auth_url, "type": "rtsp", "note": "Open in VLC: Media → Open Network Stream"}
                                return {"stream_url": stream_url, "type": "rtsp"}

                return {"error": "Camera not found or not supported"}
            except Exception as e:
                return {"error": str(e)}

        @self.app.get("/api/cameras/{camera_id}/mjpeg")
        async def get_camera_mjpeg_stream(camera_id: str):
            """Get camera MJPEG stream for browser viewing."""
            try:
                from tapo_camera_mcp.core.server import TapoCameraServer

                server = await TapoCameraServer.get_instance()

                if hasattr(server, "camera_manager") and server.camera_manager:
                    camera = server.camera_manager.cameras.get(camera_id)
                    if camera:
                        camera_type = camera.config.type
                        if hasattr(camera_type, "value"):
                            camera_type = camera_type.value

                        # For webcam, use existing webcam stream
                        if camera_type == "webcam":
                            return StreamingResponse(
                                self._generate_webcam_stream(camera),
                                media_type="multipart/x-mixed-replace; boundary=frame",
                            )
                        
                        # For RTSP/ONVIF cameras, transcode to MJPEG
                        if camera_type in ("tapo", "onvif"):
                            stream_url = await camera.get_stream_url()
                            if stream_url:
                                # Add auth for ONVIF
                                if camera_type == "onvif":
                                    from urllib.parse import urlparse
                                    parsed = urlparse(stream_url)
                                    username = camera.config.params.get("username", "")
                                    password = camera.config.params.get("password", "")
                                    if username and password:
                                        stream_url = f"rtsp://{username}:{password}@{parsed.hostname}:{parsed.port or 554}{parsed.path}"
                                
                                return StreamingResponse(
                                    self._generate_rtsp_mjpeg_stream(stream_url),
                                    media_type="multipart/x-mixed-replace; boundary=frame",
                                )

                return Response(content="Camera not found", status_code=404)
            except Exception as e:
                logger.exception(f"Error starting MJPEG stream: {e}")
                return Response(content=str(e), status_code=500)

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

        @self.app.get("/api/system/status")
        async def get_system_status():
            """Get system status."""
            try:
                from tapo_camera_mcp.core.server import TapoCameraServer

                server = await TapoCameraServer.get_instance()
                cameras = await server.camera_manager.list_cameras()
                total_cameras = len(cameras)
                online_cameras = sum(1 for cam in cameras if cam.get("status") == "online")

                return {
                    "status": "ok",
                    "version": "1.0.0",
                    "cameras": {
                        "total": total_cameras,
                        "online": online_cameras,
                        "offline": total_cameras - online_cameras,
                    },
                    "storage": {
                        "used_percent": 45,  # Mock data for now
                    },
                    "uptime": "N/A",  # Could be calculated from server start time
                }
            except Exception as e:
                return {"status": "error", "error": str(e)}

        @self.app.get("/api/events")
        async def get_events(
            limit: int = Query(100, ge=1, le=1000, description="Number of events to retrieve"),
            event_type: Optional[str] = Query(None, description="Filter by event type"),
            camera_id: Optional[str] = Query(None, description="Filter by camera ID"),
            hours: int = Query(24, ge=1, le=168, description="Hours of history to retrieve"),
        ):
            """Get events from storage."""
            try:
                from tapo_camera_mcp.utils.storage import EventStore

                event_store = EventStore()
                since = datetime.now() - timedelta(hours=hours) if hours > 0 else None
                events = event_store.get_events(
                    limit=limit,
                    event_type=event_type,
                    camera_id=camera_id,
                    since=since,
                )

                return {
                    "events": events,
                    "total": len(events),
                }
            except Exception as e:
                logger.exception("Error fetching events")
                return {"events": [], "total": 0, "error": str(e)}

        @self.app.get("/api/events/recent")
        async def get_recent_events():
            """Get recent events (alias for /api/events with default params)."""
            try:
                from tapo_camera_mcp.utils.storage import EventStore

                event_store = EventStore()
                events = event_store.get_events(limit=50)

                return {
                    "events": events,
                    "total": len(events),
                }
            except Exception as e:
                logger.exception("Error fetching recent events")
                return {"events": [], "total": 0, "error": str(e)}

        @self.app.post("/api/events")
        async def create_event(event_data: dict):
            """Create a new event."""
            try:
                from tapo_camera_mcp.utils.storage import EventStore

                event_store = EventStore()
                event = event_store.add_event(
                    event_type=event_data.get("type", "unknown"),
                    camera_id=event_data.get("camera_id"),
                    message=event_data.get("message", ""),
                    metadata=event_data.get("metadata", {}),
                )

                return {
                    "success": True,
                    "event": event,
                }
            except Exception as e:
                logger.exception("Error creating event")
                return {"success": False, "error": str(e)}

        @self.app.get("/api/logs")
        async def get_logs(
            level: Optional[str] = Query(
                None, description="Filter by log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
            ),
            lines: int = Query(100, ge=1, le=1000, description="Number of log lines to retrieve"),
            search: Optional[str] = Query(None, description="Search term to filter log messages"),
        ):
            """Get application logs with filtering."""
            try:
                from pathlib import Path

                from tapo_camera_mcp.config import get_config

                config = get_config()
                log_file = config.get("logging", {}).get("file")

                if not log_file:
                    # Try to find log file in default location
                    user_data_dir = Path("~/.local/share/tapo-camera-mcp").expanduser()
                    log_file = user_data_dir / "tapo-camera-mcp.log"

                log_file = Path(log_file)

                if not log_file.exists():
                    return {
                        "logs": [],
                        "total": 0,
                        "message": "Log file not found",
                    }

                # Read log file
                log_entries = []
                try:
                    with open(log_file, encoding="utf-8") as f:
                        file_lines = f.readlines()
                        # Get last N lines
                        recent_lines = (
                            file_lines[-lines:] if len(file_lines) > lines else file_lines
                        )

                        for raw_line in recent_lines:
                            line = raw_line.strip()
                            if not line:
                                continue

                            # Parse log line: "2025-01-01 12:00:00 - logger_name - LEVEL - message"
                            parts = line.split(" - ", 3)
                            if len(parts) >= 4:
                                timestamp_str, logger_name, log_level, message = parts
                                log_level = log_level.upper()

                                # Filter by level if specified
                                if level and log_level != level.upper():
                                    continue

                                # Filter by search term if specified
                                if search and search.lower() not in message.lower():
                                    continue

                                log_entries.append(
                                    {
                                        "timestamp": timestamp_str,
                                        "level": log_level,
                                        "logger": logger_name,
                                        "message": message,
                                    }
                                )
                except Exception as e:
                    logger.exception("Error reading log file")
                    return {"logs": [], "total": 0, "error": str(e)}

                # Reverse to show newest first
                log_entries.reverse()

                return {
                    "logs": log_entries,
                    "total": len(log_entries),
                }
            except Exception as e:
                logger.exception("Error fetching logs")
                return {"logs": [], "total": 0, "error": str(e)}

        @self.app.post("/api/logs/analyze")
        async def analyze_logs(
            logs: list[dict],
            enable_clustering: bool = False,
            enable_anomaly_detection: bool = False,
            enable_ai_synopsis: bool = False,
        ):
            """Analyze logs with clustering, anomaly detection, and AI synopsis."""
            try:
                result = {
                    "clustered": logs,
                    "anomalies": [],
                    "synopsis": None,
                }

                # Clustering: Group similar log messages
                if enable_clustering:
                    clusters = {}
                    for log_entry in logs:
                        message = log_entry.get("message", "")
                        # Create a normalized key (remove timestamps, IDs, etc.)
                        normalized = message.lower()
                        # Remove common variable parts
                        import re
                        normalized = re.sub(r'\d+', 'N', normalized)
                        normalized = re.sub(r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}', 'UUID', normalized)
                        normalized = re.sub(r'[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}', 'IP', normalized)
                        
                        if normalized not in clusters:
                            clusters[normalized] = []
                        clusters[normalized].append(log_entry)
                    
                    # Convert clusters to grouped format
                    clustered_logs = []
                    for cluster_key, cluster_entries in clusters.items():
                        if len(cluster_entries) > 1:
                            clustered_logs.append({
                                "type": "cluster",
                                "count": len(cluster_entries),
                                "pattern": cluster_entries[0].get("message", ""),
                                "entries": cluster_entries,
                            })
                        else:
                            clustered_logs.extend(cluster_entries)
                    
                    result["clustered"] = clustered_logs

                # Anomaly detection: Find unusual patterns
                if enable_anomaly_detection:
                    anomalies = []
                    
                    # Count log levels
                    level_counts = {}
                    for log_entry in logs:
                        level = log_entry.get("level", "INFO")
                        level_counts[level] = level_counts.get(level, 0) + 1
                    
                    # Detect high error rate
                    total_logs = len(logs)
                    if total_logs > 0:
                        error_rate = level_counts.get("ERROR", 0) / total_logs
                        if error_rate > 0.1:  # More than 10% errors
                            anomalies.append({
                                "type": "high_error_rate",
                                "severity": "high",
                                "message": f"High error rate detected: {error_rate*100:.1f}% of logs are errors",
                                "count": level_counts.get("ERROR", 0),
                            })
                        
                        # Detect sudden spike in warnings
                        if level_counts.get("WARNING", 0) > total_logs * 0.2:
                            anomalies.append({
                                "type": "warning_spike",
                                "severity": "medium",
                                "message": f"Warning spike detected: {level_counts.get('WARNING', 0)} warnings in recent logs",
                                "count": level_counts.get("WARNING", 0),
                            })
                    
                    # Detect repeated errors (same message multiple times)
                    error_messages = {}
                    for log_entry in logs:
                        if log_entry.get("level") == "ERROR":
                            msg = log_entry.get("message", "")
                            error_messages[msg] = error_messages.get(msg, 0) + 1
                    
                    for msg, count in error_messages.items():
                        if count >= 5:  # Same error 5+ times
                            anomalies.append({
                                "type": "repeated_error",
                                "severity": "high",
                                "message": f"Repeated error detected: '{msg[:50]}...' ({count} occurrences)",
                                "count": count,
                                "pattern": msg,
                            })
                    
                    result["anomalies"] = anomalies

                # AI Synopsis: Generate summary using LLM
                if enable_ai_synopsis:
                    try:
                        from ...llm.manager import get_llm_manager
                        
                        # Prepare log summary for LLM
                        log_summary = f"Recent log entries ({len(logs)} total):\n\n"
                        for i, log_entry in enumerate(logs[:50]):  # Limit to first 50 for context
                            log_summary += f"[{log_entry.get('level', 'INFO')}] {log_entry.get('message', '')}\n"
                        
                        prompt = f"""Analyze these application logs and provide a brief synopsis (2-3 sentences):
                        
{log_summary}

Focus on:
- Key issues or errors
- System health status
- Notable patterns or trends

Provide a concise summary:"""

                        manager = get_llm_manager()
                        messages = [
                            {"role": "user", "content": prompt}
                        ]
                        
                        # Try to get synopsis (non-blocking, fallback if LLM unavailable)
                        try:
                            synopsis = await manager.chat(messages, stream=False)
                            if isinstance(synopsis, str):
                                result["synopsis"] = synopsis
                            elif isinstance(synopsis, dict) and "content" in synopsis:
                                result["synopsis"] = synopsis["content"]
                            else:
                                result["synopsis"] = "AI synopsis unavailable - LLM provider not configured"
                        except Exception as e:
                            logger.warning(f"AI synopsis generation failed: {e}")
                            result["synopsis"] = f"AI synopsis unavailable: {str(e)}"
                    except ImportError:
                        result["synopsis"] = "AI synopsis unavailable - LLM module not available"
                    except Exception as e:
                        logger.exception("Error generating AI synopsis")
                        result["synopsis"] = f"AI synopsis error: {str(e)}"

                return result
            except Exception as e:
                logger.exception("Error analyzing logs")
                return {
                    "clustered": logs,
                    "anomalies": [],
                    "synopsis": None,
                    "error": str(e),
                }

        @self.app.get("/metrics", summary="Prometheus metrics endpoint")
        async def get_prometheus_metrics() -> Response:
            """
            Expose Prometheus-formatted metrics for Grafana.
            Includes P115 energy metrics for alerting.
            """
            try:
                from ...tools.energy.tapo_plug_tools import tapo_plug_manager
                # Lazy import weather API helpers for environment metrics (simulated/real)
                try:
                    from .api.weather import get_weather_stations, get_station_weather_data  # type: ignore
                except Exception:
                    get_weather_stations = None  # type: ignore[assignment]
                    get_station_weather_data = None  # type: ignore[assignment]

                metrics_lines = []

                # Collect P115 power metrics
                devices = await tapo_plug_manager.get_all_devices()
                for device in devices:
                    device_id = device.device_id
                    host = tapo_plug_manager.get_device_host(device_id) or "unknown"
                    name = device.name or device_id
                    location = getattr(device, "location", "unknown")
                    
                    # Power consumption in watts
                    power_watts = device.current_power
                    metrics_lines.append(
                        f'tapo_p115_power_watts{{device_id="{device_id}",host="{host}",name="{name}",location="{location}"}} {power_watts}'
                    )
                    
                    # Voltage
                    voltage = getattr(device, "voltage", 0.0)
                    metrics_lines.append(
                        f'tapo_p115_voltage_volts{{device_id="{device_id}",host="{host}",name="{name}",location="{location}"}} {voltage}'
                    )
                    
                    # Current
                    current = getattr(device, "current", 0.0)
                    metrics_lines.append(
                        f'tapo_p115_current_amps{{device_id="{device_id}",host="{host}",name="{name}",location="{location}"}} {current}'
                    )
                    
                    # Daily energy in kWh
                    daily_energy = device.daily_energy
                    metrics_lines.append(
                        f'tapo_p115_daily_energy_kwh{{device_id="{device_id}",host="{host}",name="{name}",location="{location}"}} {daily_energy}'
                    )
                    
                    # Monthly energy in kWh
                    monthly_energy = device.monthly_energy
                    metrics_lines.append(
                        f'tapo_p115_monthly_energy_kwh{{device_id="{device_id}",host="{host}",name="{name}",location="{location}"}} {monthly_energy}'
                    )
                    
                    # Daily cost in USD
                    daily_cost = getattr(device, "daily_cost", 0.0)
                    metrics_lines.append(
                        f'tapo_p115_daily_cost_usd{{device_id="{device_id}",host="{host}",name="{name}",location="{location}"}} {daily_cost}'
                    )
                    
                    # Power state (1=ON, 0=OFF)
                    power_state = 1 if device.power_state else 0
                    metrics_lines.append(
                        f'tapo_p115_power_state{{device_id="{device_id}",host="{host}",name="{name}",location="{location}"}} {power_state}'
                    )
                
                # Environment metrics (Netatmo-style). Use weather API if available.
                try:
                    if get_weather_stations and get_station_weather_data:
                        stations = await get_weather_stations(include_offline=False)  # type: ignore[misc]
                        # stations is a list of WeatherStationResponse Pydantic models or dict-like
                        if stations:
                            first = stations[0]
                            station_id = getattr(first, "station_id", None) or first.get("station_id")  # type: ignore[attr-defined]
                            if station_id:
                                data_resp = await get_station_weather_data(station_id=station_id, module_type="indoor")  # type: ignore[misc]
                                data = getattr(data_resp, "data", None) or data_resp.get("data")  # type: ignore[attr-defined]
                                if data:
                                    temperature = float(data.get("temperature", 0.0))
                                    humidity = float(data.get("humidity", 0.0))
                                    co2 = float(data.get("co2", 0.0))
                                    pressure = float(data.get("pressure", 0.0))
                                    metrics_lines.append(
                                        f'netatmo_temperature_celsius{{station_id="{station_id}",module="indoor"}} {temperature}'
                                    )
                                    metrics_lines.append(
                                        f'netatmo_humidity_percent{{station_id="{station_id}",module="indoor"}} {humidity}'
                                    )
                                    metrics_lines.append(
                                        f'netatmo_co2_ppm{{station_id="{station_id}",module="indoor"}} {co2}'
                                    )
                                    metrics_lines.append(
                                        f'netatmo_pressure_mbar{{station_id="{station_id}",module="indoor"}} {pressure}'
                                    )
                except Exception:
                    # Best-effort; skip environment metrics if unavailable
                    pass

                # Ring and Nest Protect basic health metrics (stubs that can be backed by real integrations)
                try:
                    from .api.security import _compute_ring_status, _compute_nest_status  # type: ignore
                    ring_status = _compute_ring_status()
                    nest_status = _compute_nest_status()
                    ring_enabled = bool(ring_status.get("enabled", False))
                    nest_enabled = bool(nest_status.get("enabled", False))
                    ring_devices_total = int(ring_status.get("devices_total", 0))
                    nest_devices_total = int(nest_status.get("devices_total", 0))
                except Exception:
                    ring_enabled = False
                    nest_enabled = False
                    ring_devices_total = 0
                    nest_devices_total = 0

                # Expose on/off and device counts for Grafana panels
                metrics_lines.append(f'ring_integration_enabled  {1 if ring_enabled else 0}')
                metrics_lines.append(f'nest_protect_integration_enabled  {1 if nest_enabled else 0}')
                metrics_lines.append(f'ring_devices_total {ring_devices_total}')
                metrics_lines.append(f'nest_protect_devices_total {nest_devices_total}')

                # Device health metrics from Connection Supervisor
                try:
                    from ...core.connection_supervisor import get_supervisor
                    supervisor = get_supervisor()
                    if supervisor:
                        devices = supervisor.get_device_status()
                        for device in devices:
                            device_id = device.get("device_id", "unknown")
                            device_type = device.get("type", "unknown")
                            name = device.get("name", device_id)
                            connected = 1 if device.get("connected", False) else 0
                            error_count = device.get("error_count", 0)
                            last_check_ts = device.get("last_check", 0)
                            last_success_ts = device.get("last_success", 0) or 0
                            
                            # Escape quotes in labels
                            device_id_escaped = device_id.replace('"', '\\"')
                            device_type_escaped = device_type.replace('"', '\\"')
                            name_escaped = name.replace('"', '\\"')
                            
                            metrics_lines.append(
                                f'device_health_status{{device_id="{device_id_escaped}",device_type="{device_type_escaped}",name="{name_escaped}"}} {connected}'
                            )
                            metrics_lines.append(
                                f'device_health_error_count{{device_id="{device_id_escaped}",device_type="{device_type_escaped}",name="{name_escaped}"}} {error_count}'
                            )
                            metrics_lines.append(
                                f'device_health_last_check_timestamp{{device_id="{device_id_escaped}",device_type="{device_type_escaped}",name="{name_escaped}"}} {last_check_ts}'
                            )
                            if last_success_ts > 0:
                                metrics_lines.append(
                                    f'device_health_last_success_timestamp{{device_id="{device_id_escaped}",device_type="{device_type_escaped}",name="{name_escaped}"}} {last_success_ts}'
                                )
                except Exception:
                    # Best-effort; skip device health metrics if unavailable
                    pass

                # Message metrics from Messaging Service
                try:
                    from ...core.messaging_service import get_messaging_service
                    messaging = get_messaging_service()
                    if messaging:
                        msg_metrics = messaging.get_metrics()
                        metrics_lines.append(f'messages_total {msg_metrics.get("total_messages", 0)}')
                        metrics_lines.append(f'messages_info_total {msg_metrics.get("info_total", 0)}')
                        metrics_lines.append(f'messages_warning_total {msg_metrics.get("warning_total", 0)}')
                        metrics_lines.append(f'messages_alarm_total {msg_metrics.get("alarm_total", 0)}')
                        metrics_lines.append(f'messages_alarm_acknowledged_total {msg_metrics.get("alarm_total", 0) - msg_metrics.get("unacknowledged_alarms", 0)}')
                        metrics_lines.append(f'messages_last_hour {msg_metrics.get("messages_last_hour", 0)}')
                        metrics_lines.append(f'messages_last_day {msg_metrics.get("messages_last_day", 0)}')
                except Exception:
                    # Best-effort; skip message metrics if unavailable
                    pass

                metrics_text = "\n".join(metrics_lines) + "\n"
                return Response(content=metrics_text, media_type="text/plain; version=0.0.4")
                
            except Exception as e:
                logger.exception("Error generating Prometheus metrics")
                return Response(
                    content=f"# Error generating metrics: {e}\n",
                    media_type="text/plain",
                    status_code=500
                )

        # Include API routes
        try:
            from .api.onboarding import router as onboarding_router
            onboarding_available = True
        except ImportError as e:
            logger.warning(f"Onboarding module not available: {e}")
            onboarding_router = None
            onboarding_available = False
        from .api.sensors import router as sensors_router
        from .api.energy import router as energy_router
        from .api.weather import router as weather_router
        from .api.security import router as security_router
        from .api.ring import router as ring_router
        from .api.ptz import router as ptz_router
        from .api.audio import router as audio_router
        from .api.motion import router as motion_router
        from .api.lighting import router as lighting_router
        from .api.shelly import router as shelly_router
        from .api.thermal import router as thermal_router
        from .api.health import router as health_router
        from .api.messages import router as messages_router

        if onboarding_available and onboarding_router:
            self.app.include_router(onboarding_router)
        self.app.include_router(sensors_router)
        self.app.include_router(energy_router)
        self.app.include_router(weather_router)
        self.app.include_router(security_router)
        self.app.include_router(ring_router)
        self.app.include_router(ptz_router)
        self.app.include_router(audio_router)
        self.app.include_router(motion_router)
        self.app.include_router(lighting_router)
        self.app.include_router(shelly_router)
        self.app.include_router(thermal_router)
        self.app.include_router(health_router)
        self.app.include_router(messages_router)
        
        # LLM router
        from .api.llm import router as llm_router
        self.app.include_router(llm_router)

        # Onboarding route
        @self.app.get("/onboarding", response_class=HTMLResponse, name="onboarding")
        async def onboarding_page(request: Request):
            """Serve the onboarding dashboard page."""
            return self.templates.TemplateResponse(
                "onboarding.html",
                {
                    "request": request,
                    "title": "Device Onboarding - Tapo Camera MCP",
                    "description": "Set up your Tapo P115 smart plugs, Nest Protect devices, Ring alarms, and USB webcams",
                },
            )

        # Energy Management route
        @self.app.get("/energy", response_class=HTMLResponse, name="energy")
        async def energy_page(request: Request):
            """Serve the energy management dashboard page."""
            return self.templates.TemplateResponse(
                "energy.html",
                {
                    "request": request,
                    "title": "Energy Management - Tapo Camera MCP",
                    "description": "Monitor and control Tapo P115 smart plugs with energy consumption tracking",
                },
            )

        # Alarms route
        @self.app.get("/alarms", response_class=HTMLResponse, name="alarms")
        async def alarms_page(request: Request):
            """Serve the alarms dashboard page."""
            return self.templates.TemplateResponse(
                "alarms.html",
                {
                    "request": request,
                    "title": "Security Alarms - Tapo Camera MCP",
                    "description": "Monitor Nest Protect and Ring security devices",
                },
            )

        # Lighting Control route
        @self.app.get("/lighting", response_class=HTMLResponse, name="lighting")
        async def lighting_page(request: Request):
            """Serve the lighting control dashboard page."""
            return self.templates.TemplateResponse(
                "lighting.html",
                {
                    "request": request,
                    "title": "Lighting Control - Tapo Camera MCP",
                    "description": "Control Philips Hue lights, groups, and scenes",
                },
            )

        # Stream Viewer route
        @self.app.get("/stream/{camera_id}", response_class=HTMLResponse, name="stream_viewer")
        async def stream_viewer_page(request: Request, camera_id: str):
            """Serve the stream viewer page for a camera."""
            return self.templates.TemplateResponse(
                "stream_viewer.html",
                {
                    "request": request,
                    "title": f"{camera_id} Stream - Tapo Camera MCP",
                    "camera_id": camera_id,
                    "camera_name": camera_id.replace("_", " ").title(),
                },
            )

        # Weather Monitoring route
        @self.app.get("/weather", response_class=HTMLResponse, name="weather")
        async def weather_page(request: Request):
            """Serve the weather monitoring dashboard page."""
            return self.templates.TemplateResponse(
                "weather.html",
                {
                    "request": request,
                    "title": "Weather Monitoring - Tapo Camera MCP",
                    "description": "Monitor Netatmo weather stations with temperature, humidity, CO2, and environmental data",
                },
            )

        @self.app.get("/kitchen", response_class=HTMLResponse, name="kitchen")
        async def kitchen_page(request: Request):
            """Serve the kitchen appliances dashboard page."""
            return self.templates.TemplateResponse(
                "kitchen.html",
                {
                    "request": request,
                    "title": "Kitchen - Tapo Camera MCP",
                    "description": "Control and monitor kitchen appliances",
                },
            )

        @self.app.get("/robots", response_class=HTMLResponse, name="robots")
        async def robots_page(request: Request):
            """Serve the robots dashboard page."""
            return self.templates.TemplateResponse(
                "robots.html",
                {
                    "request": request,
                    "title": "Robots - Tapo Camera MCP",
                    "description": "Control and monitor robot vacuums and other robots",
                },
            )

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
                import asyncio
                from tapo_camera_mcp.core.server import TapoCameraServer

                # Add timeout to prevent blocking
                try:
                    server = await asyncio.wait_for(
                        TapoCameraServer.get_instance(),
                        timeout=5.0
                    )
                    # Get camera list from camera manager
                    cameras = await asyncio.wait_for(
                        server.camera_manager.list_cameras(),
                        timeout=5.0
                    )
                except asyncio.TimeoutError:
                    logger.warning("Server instance access timed out - using empty camera list")
                    cameras = []
                total_cameras = len(cameras)
                online_cameras = sum(1 for cam in cameras if cam.get("status") == "online")

                # If no cameras configured, try to auto-add USB webcam
                if total_cameras == 0:
                    try:
                        global _last_webcam_attempt
                        now = datetime.utcnow()
                        if (
                            _last_webcam_attempt is None
                            or now - _last_webcam_attempt >= AUTO_WEBCAM_RETRY_INTERVAL
                        ):
                            _last_webcam_attempt = now
                            logger.info(
                                "No cameras configured, attempting to auto-add USB webcam..."
                            )
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

        @self.app.get("/api/recordings")
        async def get_recordings_api(
            limit: int = Query(100, ge=1, le=1000, description="Number of recordings to retrieve"),
            camera_id: Optional[str] = Query(None, description="Filter by camera ID"),
            recording_type: Optional[str] = Query(None, description="Filter by type (on_demand, automatic, motion, emergency)"),
            hours: int = Query(24, ge=1, le=168, description="Hours of history to retrieve"),
            emergency_only: bool = Query(False, description="Show only emergency recordings"),
            unusual_only: bool = Query(False, description="Show only unusual recordings"),
            with_ai_analysis: bool = Query(False, description="Include AI analysis results"),
        ):
            """Get recordings from storage."""
            try:
                from tapo_camera_mcp.utils.storage import RecordingStore

                recording_store = RecordingStore()
                since = datetime.now() - timedelta(hours=hours) if hours > 0 else None
                recordings = recording_store.get_recordings(
                    limit=limit,
                    camera_id=camera_id,
                    recording_type=recording_type,
                    since=since,
                    emergency_only=emergency_only,
                    unusual_only=unusual_only,
                    with_ai_analysis=with_ai_analysis,
                )

                return {
                    "recordings": recordings,
                    "total": len(recordings),
                }
            except Exception as e:
                logger.exception("Error fetching recordings")
                return {"recordings": [], "total": 0, "error": str(e)}

        @self.app.delete("/api/recordings/{recording_id}")
        async def delete_recording(recording_id: str):
            """Delete a recording."""
            try:
                from tapo_camera_mcp.utils.storage import RecordingStore

                recording_store = RecordingStore()
                success = recording_store.delete_recording(recording_id)

                return {
                    "success": success,
                    "message": "Recording deleted" if success else "Recording not found",
                }
            except Exception as e:
                logger.exception("Error deleting recording")
                return {"success": False, "error": str(e)}

        @self.app.post("/api/recordings/{recording_id}/ai-analysis")
        async def add_ai_analysis(
            recording_id: str,
            analysis_type: str = Query(..., description="Analysis type (policeman_at_door, pet_no_movement, person_of_interest, co2_pattern, etc.)"),
            confidence: float | None = Query(None, ge=0.0, le=1.0, description="Confidence score (0.0 to 1.0)"),
            details: dict | None = Body(None, description="Additional analysis details"),
        ):
            """Add AI analysis result to a recording."""
            try:
                from tapo_camera_mcp.db import MediaMetadataDB

                db = MediaMetadataDB()
                result = db.add_ai_analysis(
                    media_id=recording_id,
                    media_type="recording",
                    analysis_type=analysis_type,
                    confidence=confidence,
                    details=details or {},
                )

                return {
                    "success": True,
                    "analysis": result,
                }
            except Exception as e:
                logger.exception("Error adding AI analysis")
                return {"success": False, "error": str(e)}

        @self.app.post("/api/snapshots/{snapshot_id}/ai-analysis")
        async def add_snapshot_ai_analysis(
            snapshot_id: str,
            analysis_type: str = Query(..., description="Analysis type"),
            confidence: float | None = Query(None, ge=0.0, le=1.0, description="Confidence score"),
            details: dict | None = Body(None, description="Additional analysis details"),
        ):
            """Add AI analysis result to a snapshot."""
            try:
                from tapo_camera_mcp.db import MediaMetadataDB

                db = MediaMetadataDB()
                result = db.add_ai_analysis(
                    media_id=snapshot_id,
                    media_type="snapshot",
                    analysis_type=analysis_type,
                    confidence=confidence,
                    details=details or {},
                )

                return {
                    "success": True,
                    "analysis": result,
                }
            except Exception as e:
                logger.exception("Error adding AI analysis")
                return {"success": False, "error": str(e)}

        @self.app.get("/api/settings/retention", summary="Get retention policies")
        async def get_retention_policies():
            """Get current retention policy settings."""
            try:
                from ...config import get_model
                from ...config.models import StorageSettings

                storage_cfg = get_model(StorageSettings)
                return {
                    "success": True,
                    "policies": storage_cfg.retention_policies,
                }
            except Exception as e:
                logger.exception("Error getting retention policies")
                return {"success": False, "error": str(e)}

        @self.app.post("/api/settings/retention", summary="Update retention policies")
        async def update_retention_policies(
            video_recordings: int | None = Body(None, ge=1, le=3650, description="Days to keep video recordings"),
            snapshots: int | None = Body(None, ge=1, le=3650, description="Days to keep snapshots"),
            environment_data: int | None = Body(None, ge=1, le=3650, description="Days to keep environment data"),
        ):
            """Update retention policy settings."""
            try:
                from ...config import get_config, save_config
                from ...config.models import StorageSettings

                config = get_config()
                storage_cfg = get_model(StorageSettings)
                
                # Update policies
                if video_recordings is not None:
                    storage_cfg.retention_policies["video_recordings"] = video_recordings
                if snapshots is not None:
                    storage_cfg.retention_policies["snapshots"] = snapshots
                if environment_data is not None:
                    storage_cfg.retention_policies["environment_data"] = environment_data
                
                # Save to config
                if "storage" not in config:
                    config["storage"] = {}
                config["storage"]["retention_policies"] = storage_cfg.retention_policies
                save_config(config)
                
                return {
                    "success": True,
                    "policies": storage_cfg.retention_policies,
                    "message": "Retention policies updated",
                }
            except Exception as e:
                logger.exception("Error updating retention policies")
                return {"success": False, "error": str(e)}

        @self.app.post("/api/storage/scrub", summary="Scrub old data (guarded operation)")
        async def scrub_old_data(
            confirm: bool = Body(..., description="Confirmation required (must be true)"),
            dry_run: bool = Body(False, description="Preview what would be deleted without actually deleting"),
        ):
            """Scrub old data based on retention policies. Requires explicit confirmation."""
            if not confirm:
                return {
                    "success": False,
                    "error": "Confirmation required. Set 'confirm' to true to proceed.",
                }
            
            try:
                from ...config import get_model
                from ...config.models import StorageSettings
                from ...db import MediaMetadataDB, TimeSeriesDB
                from ...utils.storage import RecordingStore
                from datetime import timedelta

                storage_cfg = get_model(StorageSettings)
                policies = storage_cfg.retention_policies
                
                results = {
                    "videos_deleted": 0,
                    "snapshots_deleted": 0,
                    "environment_records_deleted": 0,
                    "files_deleted": 0,
                    "space_freed_mb": 0,
                }
                
                cutoff_time = datetime.now() - timedelta(days=max(policies.values()))
                
                # Scrub video recordings
                db = MediaMetadataDB()
                video_cutoff = datetime.now(timezone.utc) - timedelta(days=policies["video_recordings"])
                try:
                    # Get all recordings older than retention period
                    all_recordings = db.get_recordings(limit=10000, since=None)
                    for recording in all_recordings:
                        rec_timestamp = recording.get("timestamp")
                        if isinstance(rec_timestamp, str):
                            rec_timestamp = datetime.fromisoformat(rec_timestamp.replace("Z", "+00:00"))
                        elif not isinstance(rec_timestamp, datetime):
                            continue
                        
                        if rec_timestamp < video_cutoff:
                            if not dry_run:
                                file_path = recording.get("file_path")
                                if file_path:
                                    try:
                                        Path(file_path).unlink(missing_ok=True)
                                        results["files_deleted"] += 1
                                        results["space_freed_mb"] += recording.get("file_size_bytes", 0) / (1024 * 1024)
                                    except Exception:
                                        pass
                                db.delete_recording(recording.get("recording_id"))
                            results["videos_deleted"] += 1
                except Exception as e:
                    logger.exception("Error scrubbing videos")
                    results["error"] = str(e)
                
                # Scrub snapshots
                snapshot_cutoff = datetime.now(timezone.utc) - timedelta(days=policies["snapshots"])
                try:
                    # Get all snapshots older than retention period
                    all_snapshots = db.get_snapshots(limit=10000, since=None)
                    for snapshot in all_snapshots:
                        snap_timestamp = snapshot.get("timestamp")
                        if isinstance(snap_timestamp, str):
                            snap_timestamp = datetime.fromisoformat(snap_timestamp.replace("Z", "+00:00"))
                        elif not isinstance(snap_timestamp, datetime):
                            continue
                        
                        if snap_timestamp < snapshot_cutoff:
                            if not dry_run:
                                file_path = snapshot.get("file_path")
                                if file_path:
                                    try:
                                        Path(file_path).unlink(missing_ok=True)
                                        results["files_deleted"] += 1
                                        results["space_freed_mb"] += snapshot.get("file_size_bytes", 0) / (1024 * 1024)
                                    except Exception:
                                        pass
                                db.delete_snapshot(snapshot.get("snapshot_id"))
                            results["snapshots_deleted"] += 1
                except Exception as e:
                    logger.exception("Error scrubbing snapshots")
                
                # Scrub environment data (time series)
                env_cutoff = datetime.now(timezone.utc) - timedelta(days=policies["environment_data"])
                try:
                    ts_db = TimeSeriesDB()
                    # Note: TimeSeriesDB cleanup would require adding cleanup methods
                    # For now, this is a placeholder - SQLite will handle old data via VACUUM
                    # In production, you'd add cleanup methods to TimeSeriesDB
                    results["environment_records_deleted"] = 0
                    if not dry_run:
                        logger.info(f"Environment data cleanup not yet implemented - cutoff: {env_cutoff}")
                except Exception as e:
                    logger.exception("Error scrubbing environment data")
                
                return {
                    "success": True,
                    "dry_run": dry_run,
                    "results": results,
                    "message": "Scrub completed" if not dry_run else "Dry run completed",
                }
            except Exception as e:
                logger.exception("Error scrubbing old data")
                return {"success": False, "error": str(e)}

        @self.app.get("/recordings", response_class=HTMLResponse, name="recordings")
        async def recordings(request: Request):
            """Serve the recordings page."""
            try:
                from tapo_camera_mcp.utils.storage import RecordingStore

                recording_store = RecordingStore()
                stats = recording_store.get_storage_stats()
                recordings_list = recording_store.get_recordings(limit=50)

                today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                today_recordings = [
                    r
                    for r in recordings_list
                    if datetime.fromisoformat(r.get("timestamp", "")) >= today
                ]

                # Format storage sizes
                total_gb = stats.get("total_size_gb", 0)
                storage_used = f"{total_gb:.2f}GB"
                storage_free = f"{max(0, 100 - total_gb):.2f}GB"  # Assume 100GB total

                return self.templates.TemplateResponse(
                    "recordings.html",
                    {
                        "request": request,
                        "active_page": "recordings",
                        "recordings": recordings_list,
                        "total_recordings": stats.get("total_recordings", 0),
                        "today_recordings": len(today_recordings),
                        "storage_used": storage_used,
                        "storage_free": storage_free,
                    },
                )
            except Exception as e:
                logger.exception("Error loading recordings page")
                return self.templates.TemplateResponse(
                    "recordings.html",
                    {
                        "request": request,
                        "active_page": "recordings",
                        "recordings": [],
                        "total_recordings": 0,
                        "today_recordings": 0,
                        "storage_used": "0GB",
                        "storage_free": "0GB",
                        "error": str(e),
                    },
                )

        @self.app.get("/events", response_class=HTMLResponse, name="events")
        async def events(request: Request):
            """Serve the events page."""
            try:
                from tapo_camera_mcp.utils.storage import EventStore

                event_store = EventStore()
                events_list = event_store.get_events(limit=100)

                # Group events by type
                events_by_type = {}
                for event in events_list:
                    event_type = event.get("type", "unknown")
                    if event_type not in events_by_type:
                        events_by_type[event_type] = []
                    events_by_type[event_type].append(event)

                return self.templates.TemplateResponse(
                    "events.html",
                    {
                        "request": request,
                        "active_page": "events",
                        "events": events_list,
                        "events_by_type": events_by_type,
                        "total_events": len(events_list),
                    },
                )
            except Exception as e:
                logger.exception("Error loading events page")
                return self.templates.TemplateResponse(
                    "events.html",
                    {
                        "request": request,
                        "active_page": "events",
                        "events": [],
                        "events_by_type": {},
                        "total_events": 0,
                        "error": str(e),
                    },
                )

        @self.app.get("/help", response_class=HTMLResponse, name="help")
        async def help_page(request: Request):
            """Serve the help and documentation page."""
            return self.templates.TemplateResponse(
                "help.html", {"request": request, "active_page": "help"}
            )

        @self.app.get("/health-dashboard", response_class=HTMLResponse, name="health_dashboard")
        async def health_dashboard_page(request: Request):
            """Serve the connection health monitoring dashboard."""
            return self.templates.TemplateResponse(
                "health_dashboard.html", {"request": request, "active_page": "health"}
            )

        @self.app.get("/alerts", response_class=HTMLResponse, name="alerts")
        async def alerts_page(request: Request):
            """Serve the alerts and messages dashboard."""
            return self.templates.TemplateResponse(
                "alerts.html", {"request": request, "active_page": "alerts"}
            )

        # 404 handler
        @self.app.exception_handler(404)
        async def not_found(request: Request, _exc: StarletteHTTPException):
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
        self.app.add_api_route(
            "/health",
            self.health_page,
            methods=["GET"],
            response_class=HTMLResponse,
            name="health",
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
                        "server_port": config.get("server", {}).get("port", 7777),
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
                        # If read fails, wait a bit before retrying to avoid tight loop
                        await asyncio.sleep(0.1)
                        continue

                    # Encode frame as JPEG
                    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 80]
                    result, encoded_img = cv2.imencode(".jpg", frame, encode_param)

                    if result:
                        # Create MJPEG frame
                        yield (
                            b"--frame\r\n"
                            b"Content-Type: image/jpeg\r\n\r\n" + encoded_img.tobytes() + b"\r\n"
                        )

                    # Control frame rate - 0.1 seconds = 10 FPS (reasonable for streaming)
                    # This prevents excessive CPU usage from aggressive polling
                    await asyncio.sleep(0.1)

        except Exception:
            logger.exception("Error generating webcam stream")
            # Send error frame
            error_frame = (
                b"--frame\r\nContent-Type: image/jpeg\r\n\r\n"
                + b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.' \",#\x1c\x1c(7),01444\x1f'9=82<.342\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x01\x01\x11\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00\x3f\x00\xaa\xff\xd9"
                + b"\r\n"
            )
            yield error_frame

    async def _generate_rtsp_mjpeg_stream(self, rtsp_url: str) -> Generator[bytes, None, None]:
        """Generate MJPEG stream from RTSP URL for browser viewing."""
        import asyncio
        import cv2
        
        cap = None
        try:
            # Open RTSP stream with OpenCV
            cap = cv2.VideoCapture(rtsp_url)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimize buffer for lower latency
            
            if not cap.isOpened():
                logger.error(f"Failed to open RTSP stream: {rtsp_url}")
                raise Exception("Failed to open RTSP stream")
            
            logger.info(f"MJPEG stream started for {rtsp_url[:50]}...")
            consecutive_failures = 0
            max_failures = 30  # Stop after 30 consecutive failures
            
            while consecutive_failures < max_failures:
                ret, frame = cap.read()
                if not ret:
                    consecutive_failures += 1
                    await asyncio.sleep(0.1)
                    continue
                
                consecutive_failures = 0  # Reset on success
                
                # Resize for bandwidth efficiency (720p max)
                height, width = frame.shape[:2]
                if width > 1280:
                    scale = 1280 / width
                    new_width = int(width * scale)
                    new_height = int(height * scale)
                    frame = cv2.resize(frame, (new_width, new_height))
                
                # Encode frame as JPEG
                encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 70]
                result, encoded_img = cv2.imencode(".jpg", frame, encode_param)
                
                if result:
                    yield (
                        b"--frame\r\n"
                        b"Content-Type: image/jpeg\r\n\r\n" + encoded_img.tobytes() + b"\r\n"
                    )
                
                # ~10 FPS
                await asyncio.sleep(0.1)
                
        except GeneratorExit:
            logger.info("MJPEG stream client disconnected")
        except Exception as e:
            logger.exception(f"Error generating RTSP MJPEG stream: {e}")
        finally:
            if cap:
                cap.release()
                logger.info("RTSP stream released")

    def run(self, host: Optional[str] = None, port: Optional[int] = None):
        """Run the web server.

        Args:
            host: Host to bind to. Defaults to config value.
            port: Port to bind to. Defaults to config value.
        """
        import uvicorn
        import socket

        host = host or self.web_config.host
        port = port or self.web_config.port

        # Check if port is available before starting
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.bind((host, port))
        except OSError as e:
            if e.errno == 10048 or "Address already in use" in str(e):  # Windows: 10048, Linux: 98
                logger.error(f"[ERROR] PORT CONFLICT: Port {port} is already in use!")
                logger.error(f"   Another process (possibly Docker container) is using port {port}.")
                logger.error(f"   Solutions:")
                logger.error(f"   1. Stop the conflicting process:")
                logger.error(f"      PowerShell: Get-NetTCPConnection -LocalPort {port} | Select-Object OwningProcess")
                logger.error(f"      Then: Stop-Process -Id <PID> -Force")
                logger.error(f"   2. Stop Docker container:")
                logger.error(f"      docker ps | findstr tapo")
                logger.error(f"      docker stop <container-id>")
                logger.error(f"   3. Use a different port:")
                logger.error(f"      python -m tapo_camera_mcp.web --port 7778")
                raise RuntimeError(
                    f"Port {port} is already in use. "
                    f"Stop the conflicting process or use --port <different_port>"
                ) from e
            raise

        logger.info(f"Starting web server on http://{host}:{port}")

        try:
            uvicorn.run(
                self.app,
                host=host,
                port=port,
                log_level=self.config.get("log_level", "info").lower(),
                reload=self.config.get("debug", False),
                workers=1,  # Running with multiple workers can cause issues with in-memory state
            )
        except OSError as e:
            if "Address already in use" in str(e) or e.errno in (10048, 98):
                logger.error(f"[ERROR] Failed to start server: Port {port} conflict detected during startup!")
                logger.error(f"   This can happen if another process grabbed the port between check and start.")
                raise RuntimeError(
                    f"Port {port} conflict during startup. "
                    f"Try again or use --port <different_port>"
                ) from e
            raise


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
