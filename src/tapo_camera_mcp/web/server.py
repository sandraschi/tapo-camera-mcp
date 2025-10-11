"""
Web server module for Tapo Camera MCP.

This module provides the web server implementation using FastAPI.
"""
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Union, Generator

from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, StreamingResponse, Response
from fastapi.exceptions import RequestValidationError, HTTPException as FastAPIHTTPException
from starlette.exceptions import HTTPException as StarletteHTTPException

from ..config import get_config, get_model, WebUISettings, SecuritySettings
from ..utils.logging import setup_logging

# Setup logging
logger = logging.getLogger(__name__)

class WebServer:
    """Web server for Tapo Camera MCP."""
    
    def __init__(self, config_path: Optional[str] = None):
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
            debug=self.config.get("debug", False)
        )
        
        # Setup middleware
        self._setup_middleware()
        
        # Setup exception handlers
        self._setup_exception_handlers()
        
        # Setup routes
        self._setup_routes()
        
        # Setup templates
        self.templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
        self.templates.env.globals.update({
            "app_title": self.web_config.title,
            "app_version": "1.0.0",
            "theme": self.web_config.theme
        })
    
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
            response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:;"
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
                url="/?error=invalid_request",
                status_code=status.HTTP_303_SEE_OTHER
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
                cameras_data = await server.list_cameras()
                return cameras_data
            except Exception as e:
                return {"success": False, "error": str(e), "cameras": []}
        
        @self.app.get("/api/cameras/{camera_id}/stream")
        async def get_camera_stream(camera_id: str):
            """Get camera video stream."""
            try:
                from tapo_camera_mcp.core.server import TapoCameraServer
                server = await TapoCameraServer.get_instance()
                
                if hasattr(server, 'camera_manager') and server.camera_manager:
                    camera = server.camera_manager.cameras.get(camera_id)
                    if camera:
                        # For webcam, return MJPEG stream
                        if camera.config.type.value == "webcam":
                            return StreamingResponse(
                                self._generate_webcam_stream(camera),
                                media_type="multipart/x-mixed-replace; boundary=frame"
                            )
                        # For Tapo cameras, return RTSP stream URL
                        elif camera.config.type.value == "tapo":
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
                
                if hasattr(server, 'camera_manager') and server.camera_manager:
                    camera = server.camera_manager.cameras.get(camera_id)
                    if camera:
                        image = await camera.capture_still()
                        
                        # Convert to bytes
                        import io
                        buffer = io.BytesIO()
                        image.save(buffer, format="JPEG", quality=75)
                        image_bytes = buffer.getvalue()
                        
                        return Response(
                            content=image_bytes,
                            media_type="image/jpeg"
                        )
                
                return Response(content="Camera not found", status_code=404)
            except Exception as e:
                return Response(content=f"Error: {str(e)}", status_code=500)
        
        # Web UI routes
        @self.app.get("/", response_class=HTMLResponse, name="dashboard")
        async def index(request: Request):
            """Serve the main dashboard page."""
            try:
                # Get real camera data from the MCP server
                from tapo_camera_mcp.core.server import TapoCameraServer
                server = await TapoCameraServer.get_instance()

                # Get camera list
                cameras_result = await server.list_cameras()
                cameras = cameras_result.get('cameras', [])
                total_cameras = len(cameras)
                online_cameras = sum(1 for cam in cameras if cam.get('status') == 'online')

                # If no cameras configured, try to auto-add USB webcam
                if total_cameras == 0:
                    try:
                        logger.info("No cameras configured, attempting to auto-add USB webcam...")
                        add_result = await server.add_camera(
                            camera_name='usb_webcam_0',
                            camera_type='webcam',
                            device_id=0
                        )
                        if add_result.get('success'):
                            logger.info("Successfully auto-added USB webcam")
                            # Refresh camera list
                            cameras_result = await server.list_cameras()
                            cameras = cameras_result.get('cameras', [])
                            total_cameras = len(cameras)
                            online_cameras = sum(1 for cam in cameras if cam.get('status') == 'online')
                        else:
                            logger.warning(f"Failed to auto-add webcam: {add_result}")
                    except Exception as e:
                        logger.warning(f"Error auto-adding webcam: {e}")

            except Exception as e:
                logger.warning(f"Failed to get camera data for dashboard: {e}")
                cameras = []
                online_cameras = 0
                total_cameras = 0

            return self.templates.TemplateResponse(
                "simple_dashboard.html",
                {
                    "request": request,
                    "active_page": "dashboard",
                    "online_cameras": online_cameras,
                    "total_cameras": total_cameras,
                    "storage_used": 45,  # Mock data for now
                    "active_alerts": 0,
                    "active_recordings": 0,
                    "cameras": cameras
                }
            )
        
        @self.app.get("/cameras", response_class=HTMLResponse, name="cameras")
        async def cameras(request: Request):
            """Serve the cameras page."""
            # TODO: Get actual camera data
            cameras = [
                {"id": "cam1", "name": "Front Door", "status": "online"},
                {"id": "cam2", "name": "Backyard", "status": "offline"},
            ]
            
            return self.templates.TemplateResponse(
                "dashboard.html",
                {
                    "request": request,
                    "active_page": "cameras",
                    "cameras": cameras
                }
            )
        
        @self.app.get("/settings", response_class=HTMLResponse, name="settings")
        async def settings(request: Request):
            """Serve the settings page."""
            return self.templates.TemplateResponse(
                "dashboard.html",
                {
                    "request": request,
                    "active_page": "settings",
                    "config": self.config
                }
            )
        
        @self.app.get("/list_cameras", response_class=HTMLResponse, name="list_cameras")
        async def list_cameras(request: Request):
            """Serve the cameras list page."""
            return self.templates.TemplateResponse(
                "dashboard.html",
                {
                    "request": request,
                    "active_page": "cameras"
                }
            )
        
        @self.app.get("/recordings", response_class=HTMLResponse, name="recordings")
        async def recordings(request: Request):
            """Serve the recordings page."""
            return self.templates.TemplateResponse(
                "dashboard.html",
                {
                    "request": request,
                    "active_page": "recordings"
                }
            )
        
        @self.app.get("/system_settings", response_class=HTMLResponse, name="system_settings")
        async def system_settings(request: Request):
            """Serve the system settings page."""
            return self.templates.TemplateResponse(
                "dashboard.html",
                {
                    "request": request,
                    "active_page": "system_settings"
                }
            )
        
        @self.app.get("/events", response_class=HTMLResponse, name="events")
        async def events(request: Request):
            """Serve the events page."""
            return self.templates.TemplateResponse(
                "dashboard.html",
                {
                    "request": request,
                    "active_page": "events"
                }
            )
        
        @self.app.get("/help", response_class=HTMLResponse, name="help")
        async def help_page(request: Request):
            """Serve the help and documentation page."""
            return self.templates.TemplateResponse(
                "help.html",
                {
                    "request": request,
                    "active_page": "help"
                }
            )
        
        # 404 handler
        @self.app.exception_handler(404)
        async def not_found(request: Request, exc: StarletteHTTPException):
            if request.url.path.startswith("/api/"):
                return JSONResponse(
                    status_code=404,
                    content={"detail": "Not Found"},
                )
            
            return self.templates.TemplateResponse(
                "404.html",
                {"request": request},
                status_code=404
            )
    
    async def _generate_webcam_stream(self, camera) -> Generator[bytes, None, None]:
        """Generate MJPEG stream from webcam."""
        try:
            import cv2
            import asyncio
            
            # Ensure camera is connected
            if not await camera.is_connected():
                await camera.connect()
            
            # Get OpenCV VideoCapture from webcam
            if hasattr(camera, '_cap') and camera._cap:
                cap = camera._cap
                
                while True:
                    ret, frame = cap.read()
                    if not ret:
                        break
                    
                    # Encode frame as JPEG
                    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 80]
                    result, encoded_img = cv2.imencode('.jpg', frame, encode_param)
                    
                    if result:
                        # Create MJPEG frame
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n\r\n' + 
                               encoded_img.tobytes() + b'\r\n')
                    
                    # Control frame rate
                    await asyncio.sleep(0.033)  # ~30 FPS
                    
        except Exception as e:
            logger.error(f"Error generating webcam stream: {e}")
            # Send error frame
            error_frame = b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x01\x01\x11\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00\x3f\x00\xaa\xff\xd9' + b'\r\n'
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
    # Setup logging
    setup_logging()
    
    # Create and run the server
    server = WebServer()
    server.run()
