"""API routes for the Tapo Camera MCP server."""
from typing import Dict, Any, List, Optional
from fastmcp import FastMCP
from ..camera.manager import CameraManager

class APIRouter:
    """API router for camera operations."""
    
    def __init__(self, mcp: FastMCP, camera_manager: CameraManager):
        self.mcp = mcp
        self.camera_manager = camera_manager
        self._register_routes()
    
    def _register_routes(self):
        """Register all API routes."""
        
        @self.mcp.tool()
        async def list_cameras(params: dict = None) -> Dict[str, Any]:
            """List all cameras."""
            try:
                cameras = await self.camera_manager.list_cameras()
                return {
                    'status': 'success',
                    'cameras': cameras
                }
            except Exception as e:
                return {
                    'status': 'error',
                    'message': f'Failed to list cameras: {str(e)}'
                }
        
        @self.mcp.tool()
        async def add_camera(params: dict) -> Dict[str, Any]:
            """Add a new camera."""
            try:
                name = params.get('name')
                if not name:
                    return {
                        'status': 'error',
                        'message': 'Camera name is required'
                    }
                
                success = await self.camera_manager.add_camera(params)
                if success:
                    return {
                        'status': 'success',
                        'message': f'Camera {name} added successfully'
                    }
                else:
                    return {
                        'status': 'error',
                        'message': f'Failed to add camera {name}'
                    }
            except Exception as e:
                return {
                    'status': 'error',
                    'message': f'Failed to add camera: {str(e)}'
                }
        
        @self.mcp.tool()
        async def remove_camera(params: dict) -> Dict[str, Any]:
            """Remove a camera."""
            try:
                name = params.get('name')
                if not name:
                    return {
                        'status': 'error',
                        'message': 'Camera name is required'
                    }
                
                success = await self.camera_manager.remove_camera(name)
                if success:
                    return {
                        'status': 'success',
                        'message': f'Camera {name} removed successfully'
                    }
                else:
                    return {
                        'status': 'error',
                        'message': f'Failed to remove camera {name}'
                    }
            except Exception as e:
                return {
                    'status': 'error',
                    'message': f'Failed to remove camera: {str(e)}'
                }
        
        @self.mcp.tool()
        async def capture_still(params: dict) -> Dict[str, Any]:
            """Capture a still image from a camera."""
            try:
                camera_name = params.get('camera')
                if not camera_name:
                    return {
                        'status': 'error',
                        'message': 'Camera name is required'
                    }
                
                result = await self.camera_manager.capture_still(
                    camera_name,
                    params.get('save_path')
                )
                return result
                
            except Exception as e:
                return {
                    'status': 'error',
                    'message': f'Failed to capture image: {str(e)}'
                }
        
        @self.mcp.tool()
        async def get_stream_url(params: dict) -> Dict[str, Any]:
            """Get stream URL for a camera."""
            try:
                camera_name = params.get('camera')
                if not camera_name:
                    return {
                        'status': 'error',
                        'message': 'Camera name is required'
                    }
                
                camera = await self.camera_manager.get_camera(camera_name)
                if not camera:
                    return {
                        'status': 'error',
                        'message': f'Camera {camera_name} not found'
                    }
                
                stream_url = await camera.get_stream_url()
                if not stream_url:
                    return {
                        'status': 'error',
                        'message': 'Stream URL not available'
                    }
                
                return {
                    'status': 'success',
                    'camera': camera_name,
                    'stream_url': stream_url
                }
                
            except Exception as e:
                return {
                    'status': 'error',
                    'message': f'Failed to get stream URL: {str(e)}'
                }

def setup_api_routes(server) -> APIRouter:
    """Set up API routes for the server."""
    return APIRouter(server.mcp, server.camera_manager)
