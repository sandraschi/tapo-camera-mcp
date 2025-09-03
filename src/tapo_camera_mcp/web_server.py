"""Web server for the Tapo Camera MCP viewer with Grafana integration."""
import os
import asyncio
import base64
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, Response, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import json

class TapoWebServer:
    def __init__(self, mcp_server, host: str = "0.0.0.0", port: int = 8000):
        self.mcp_server = mcp_server
        self.host = host
        self.port = port
        self.app = FastAPI(title="Tapo Camera Viewer")
        
        # Set up CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Create static files directory if it doesn't exist
        self.static_dir = os.path.join(os.path.dirname(__file__), "static")
        os.makedirs(self.static_dir, exist_ok=True)
        self.app.mount("/static", StaticFiles(directory=self.static_dir), name="static")
        
        # Set up routes
        self.setup_routes()
    
    def setup_routes(self):
        @self.app.get("/", response_class=HTMLResponse)
        async def get_viewer():
            """Serve the main viewer page."""
            viewer_path = os.path.join(os.path.dirname(__file__), "templates", "viewer.html")
            return FileResponse(viewer_path)
            
        @self.app.get("/api/grafana/metrics")
        async def get_grafana_metrics():
            """Get metrics in Grafana-compatible format."""
            try:
                result = await self.mcp_server.call_tool(
                    "get_grafana_metrics",
                    {}
                )
                if not result.get("success"):
                    raise HTTPException(status_code=500, detail=result.get("error", "Failed to get metrics"))
                return JSONResponse(
                    content=result["data"],
                    media_type=result.get("content_type", "application/json")
                )
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
                
        @self.app.get("/api/grafana/snapshot/{camera_id}")
        async def get_camera_snapshot(
            camera_id: str,
            quality: str = Query("medium", description="Image quality (low, medium, high)"),
            width: Optional[int] = Query(None, description="Image width in pixels"),
            height: Optional[int] = Query(None, description="Image height in pixels"),
            t: Optional[int] = Query(None, description="Cache buster timestamp")
        ):
            """Get a live snapshot from a camera for Grafana image panels."""
            try:
                result = await self.mcp_server.call_tool(
                    "get_camera_snapshot",
                    {
                        "camera_id": camera_id,
                        "quality": quality,
                        "width": width,
                        "height": height
                    }
                )
                
                if not result.get("success"):
                    raise HTTPException(status_code=500, detail=result.get("error", "Failed to get snapshot"))
                
                # If we have base64 image data, decode it
                if "image" in result["data"] and result["data"]["image"].startswith("data:image"):
                    # Extract base64 data
                    header, encoded = result["data"]["image"].split(",", 1)
                    image_data = base64.b64decode(encoded)
                    return Response(
                        content=image_data,
                        media_type=header.split(":")[1].split(";")[0]  # Extract content type
                    )
                
                return JSONResponse(
                    content=result["data"],
                    media_type=result.get("content_type", "application/json")
                )
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
                
        @self.app.get("/api/grafana/dashboard/vienna")
        async def get_vienna_dashboard():
            """Get Vienna-specific dashboard data."""
            try:
                result = await self.mcp_server.call_tool(
                    "get_vienna_security_dashboard",
                    {}
                )
                if not result.get("success"):
                    raise HTTPException(status_code=500, detail=result.get("error", "Failed to get dashboard data"))
                return JSONResponse(
                    content=result["data"],
                    media_type=result.get("content_type", "application/json")
                )
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/cameras")
        async def list_cameras() -> Dict[str, Any]:
            """List all available cameras."""
            try:
                # Get camera status from MCP server
                status = await self.mcp_server.get_camera_status()
                return {"status": "success", "cameras": status.get("cameras", {})}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/stream/{camera_name}")
        async def get_camera_stream(camera_name: str) -> Dict[str, Any]:
            """Get RTSP stream URL for a camera."""
            try:
                # Get RTSP URL from MCP server
                result = await self.mcp_server.get_rtsp_url(camera_name)
                if result.get("status") != "success":
                    raise HTTPException(status_code=400, detail=result.get("message", "Failed to get stream URL"))
                return result
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
    
    async def start(self):
        """Start the web server."""
        import uvicorn
        config = uvicorn.Config(
            self.app,
            host=self.host,
            port=self.port,
            log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()
    
    def run(self):
        """Run the web server (blocking)."""
        asyncio.run(self.start())
