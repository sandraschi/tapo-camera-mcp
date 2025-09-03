"""
Web server module for Tapo Camera MCP.

This module provides the web server implementation using FastAPI.
"""
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Union

from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
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
        
        # Web UI routes
        @self.app.get("/", response_class=HTMLResponse)
        async def index(request: Request):
            """Serve the main dashboard page."""
            return self.templates.TemplateResponse(
                "dashboard.html",
                {"request": request, "active_page": "dashboard"}
            )
        
        @self.app.get("/cameras", response_class=HTMLResponse)
        async def cameras(request: Request):
            """Serve the cameras page."""
            # TODO: Get actual camera data
            cameras = [
                {"id": "cam1", "name": "Front Door", "status": "online"},
                {"id": "cam2", "name": "Backyard", "status": "offline"},
            ]
            
            return self.templates.TemplateResponse(
                "cameras.html",
                {
                    "request": request,
                    "active_page": "cameras",
                    "cameras": cameras
                }
            )
        
        @self.app.get("/settings", response_class=HTMLResponse)
        async def settings(request: Request):
            """Serve the settings page."""
            return self.templates.TemplateResponse(
                "settings.html",
                {
                    "request": request,
                    "active_page": "settings",
                    "config": self.config
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
