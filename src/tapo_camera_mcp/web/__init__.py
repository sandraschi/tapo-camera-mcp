"""
Tapo Camera MCP Web Interface

This module provides the web interface for the Tapo Camera MCP server.
"""

from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security import APIKeyCookie
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from ..config import ServerConfig

# Re-export models for external use
from ..core.models import CameraInfo as CameraInfo
from ..core.models import CameraStatus as CameraStatus
from ..core.models import PTZPosition as PTZPosition
from ..utils import get_logger

logger = get_logger(__name__)


class WebServer:
    """Web server for the Tapo Camera MCP interface."""

    def __init__(self, config: ServerConfig):
        """Initialize the web server."""
        self.config = config
        self.app = FastAPI(
            title="Tapo Camera MCP",
            description="Management and Control Panel for Tapo Cameras",
            version="1.0.0",
            docs_url="/api/docs" if config.web_enable_swagger else None,
            redoc_url="/api/redoc" if config.web_enable_swagger else None,
        )

        # Set up templates and static files
        self.templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

        # Mount static files
        static_path = Path(__file__).parent / "static"
        self.app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

        # Set up security
        self.security = APIKeyCookie(name="session")

        # Set up routes
        self._setup_routes()

    def _setup_routes(self) -> None:
        """Set up all web routes."""

        # Home/Dashboard
        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard(request: Request):
            """Render the dashboard page."""
            # This would fetch real data in a real implementation
            return self.templates.TemplateResponse(
                "dashboard.html",
                {
                    "request": request,
                    "online_cameras": 3,
                    "total_cameras": 5,
                    "storage_used": 45,
                    "active_alerts": 2,
                    "active_recordings": 1,
                    "cameras": [
                        {
                            "id": "cam1",
                            "name": "Front Door",
                            "model": "Tapo C200",
                            "ip_address": "192.168.1.100",
                            "is_online": True,
                        },
                        # Add more mock cameras as needed
                    ],
                    "recent_events": [
                        {
                            "type": "motion",
                            "title": "Motion Detected",
                            "description": "Motion detected at Front Door",
                            "timestamp": "2 minutes ago",
                            "has_thumbnail": True,
                            "thumbnail_url": "/static/img/placeholder-thumb.jpg",
                        },
                        {
                            "type": "recording",
                            "title": "Recording Started",
                            "description": "Recording started for Backyard",
                            "timestamp": "10 minutes ago",
                            "has_thumbnail": False,
                        },
                    ],
                    "system_status": {
                        "cpu_usage": 24,
                        "memory_usage": 65,
                        "disk_usage": 45,
                        "network": {"upload": 1.2, "download": 3.4},
                    },
                },
            )

        # Camera endpoints
        @self.app.get("/cameras", response_class=HTMLResponse)
        async def list_cameras(request: Request):
            """List all cameras."""
            return self.templates.TemplateResponse("cameras.html", {"request": request})

        @self.app.get("/cameras/{camera_id}", response_class=HTMLResponse)
        async def view_camera(request: Request, camera_id: str):
            """View a specific camera."""
            return self.templates.TemplateResponse(
                "camera_view.html", {"request": request, "camera_id": camera_id}
            )

        # API endpoints
        @self.app.get("/api/cameras")
        async def api_list_cameras():
            """API endpoint to list all cameras."""
            # This would fetch from the camera manager
            return {"status": "success", "data": []}

        @self.app.get("/api/cameras/{camera_id}")
        async def api_get_camera(camera_id: str):
            """API endpoint to get camera details."""
            # This would fetch from the camera manager
            return {"status": "success", "data": {"id": camera_id}}

        @self.app.get("/api/cameras/{camera_id}/snapshot")
        async def get_camera_snapshot(camera_id: str):
            """Get a snapshot from a camera."""
            # This would fetch a real snapshot
            snapshot_path = Path(__file__).parent / "static" / "img" / "placeholder.jpg"
            if not snapshot_path.exists():
                raise HTTPException(status_code=404, detail="Snapshot not available")

            from fastapi.responses import FileResponse

            return FileResponse(snapshot_path)

        # System endpoints
        @self.app.get("/system/settings", response_class=HTMLResponse)
        async def system_settings(request: Request):
            """System settings page."""
            return self.templates.TemplateResponse(
                "system_settings.html",
                {"request": request, "config": self.config.dict()},
            )

        # Authentication
        @self.app.post("/api/auth/login")
        async def login():
            """Handle user login."""
            # This would validate credentials
            response = JSONResponse({"status": "success"})
            response.set_cookie(
                key="session",
                value="dummy-session-token",
                httponly=True,
                max_age=3600,  # 1 hour
            )
            return response

        @self.app.post("/api/auth/logout")
        async def logout():
            """Handle user logout."""
            response = JSONResponse({"status": "success"})
            response.delete_cookie("session")
            return response

    def run(self):
        """Run the web server."""
        import uvicorn

        logger.info(f"Starting web server on http://{self.config.web_host}:{self.config.web_port}")

        uvicorn.run(
            self.app,
            host=self.config.web_host,
            port=self.config.web_port,
            log_level="info",
        )


def create_web_app(config: ServerConfig) -> FastAPI:
    """Create and configure the web application.

    Args:
        config: Server configuration

    Returns:
        Configured FastAPI application instance
    """
    web_server = WebServer(config)
    return web_server.app


# For development
def main():
    """Run the web server directly for development."""
    from ..config import ServerConfig

    config = ServerConfig()
    web_server = WebServer(config)
    web_server.run()


if __name__ == "__main__":
    main()
