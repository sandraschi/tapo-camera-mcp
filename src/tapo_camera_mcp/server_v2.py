"""
Tapo-Camera-MCP - FastMCP 2.10 server for controlling TP-Link Tapo cameras.
"""
import asyncio
import base64
import hashlib
import io
import json
import logging
import os
import sys
import time
from collections import OrderedDict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union, Callable, BinaryIO

import numpy as np
from fastmcp import FastMCP
from fastmcp.client import Client
from pydantic import BaseModel, Field, HttpUrl
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter
from pytapo import Tapo, HttpMediaSession as MediaSession

from . import presets
from .web_server import TapoWebServer
from .analysis import image_analyzer
from .camera.manager import camera_manager
from .camera.base import CameraType, CameraConfig
# Import camera implementations to ensure registration
from . import camera

# Configure logging
logger = logging.getLogger(__name__)

# Pydantic models for request/response validation
class TapoCameraConfig(BaseModel):
    """Camera configuration model."""
    host: str = Field(..., description="Camera IP address or hostname")
    username: str = Field(..., description="Camera username")
    password: str = Field(..., description="Camera password")
    stream_quality: str = Field("hd", description="Stream quality (hd/sd)")
    verify_ssl: bool = Field(True, description="Verify SSL certificate")

class PTZPosition(BaseModel):
    """PTZ position model."""
    pan: float = Field(0.0, ge=-1.0, le=1.0, description="Pan position (-1.0 to 1.0)")
    tilt: float = Field(0.0, ge=-1.0, le=1.0, description="Tilt position (-1.0 to 1.0)")
    zoom: float = Field(0.0, ge=0.0, le=1.0, description="Zoom level (0.0 to 1.0)")

class CameraInfo(BaseModel):
    """Camera information model."""
    model: str = Field(..., description="Camera model name")
    serial_number: str = Field(..., description="Camera serial number")
    firmware_version: str = Field(..., description="Firmware version")
    mac_address: str = Field(..., description="MAC address")
    ip_address: str = Field(..., description="IP address")
    wifi_signal: int = Field(..., description="WiFi signal strength (0-100)")
    wifi_ssid: str = Field(..., description="Connected WiFi SSID")

class CameraStatus(BaseModel):
    """Camera status model."""
    online: bool = Field(..., description="Camera online status")
    recording: bool = Field(..., description="Recording status")
    motion_detected: bool = Field(..., description="Motion detection status")
    privacy_mode: bool = Field(..., description="Privacy mode status")
    led_enabled: bool = Field(..., description="LED status")
    uptime: int = Field(..., description="Uptime in seconds")
    storage: Dict[str, int] = Field(..., description="Storage information")

class StreamInfo(BaseModel):
    """Stream information model."""
    url: HttpUrl = Field(..., description="Stream URL")
    type: str = Field(..., description="Stream type (rtsp/rtmp)")
    quality: str = Field(..., description="Stream quality (hd/sd)")

class ImageCache:
    """LRU cache for processed images with memory management."""
    def __init__(self, max_size_mb: int = 100, max_items: int = 100):
        self.cache = OrderedDict()
        self.max_size = max_size_mb * 1024 * 1024  # Convert MB to bytes
        self.current_size = 0
        self.max_items = max_items
        self.lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[bytes]:
        """Get an item from the cache."""
        async with self.lock:
            if key in self.cache:
                # Move to end (most recently used)
                value = self.cache.pop(key)
                self.cache[key] = value
                return value
            return None
    
    async def set(self, key: str, value: bytes) -> None:
        """Add an item to the cache, evicting if necessary."""
        item_size = sys.getsizeof(value)
        if item_size > self.max_size:
            return  # Item too large for cache
            
        async with self.lock:
            # Remove existing item if it exists
            if key in self.cache:
                self.current_size -= sys.getsizeof(self.cache[key])
                del self.cache[key]
            
            # Evict least recently used items if needed
            while (self.current_size + item_size > self.max_size or 
                   len(self.cache) >= self.max_items):
                if not self.cache:
                    break
                _, oldest_value = self.cache.popitem(last=False)
                self.current_size -= sys.getsizeof(oldest_value)
            
            # Add new item
            self.cache[key] = value
            self.current_size += item_size

class TapoCameraServer:
    """Tapo Camera MCP server implementation using FastMCP 2.10."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the Tapo Camera MCP server.
        
        Args:
            config: Optional configuration dictionary with keys:
                - cache_size_mb: Maximum cache size in MB (default: 100)
                - max_cache_items: Maximum number of items in cache (default: 100)
                - temp_dir: Directory for temporary files (default: C:/temp)
                - request_timeout: HTTP request timeout in seconds (default: 30)
                - max_retries: Maximum retry attempts for operations (default: 3)
        """
        # Load camera configuration from config parameter
        camera_config = config.copy() if config else {}
        
        # Only create TapoCameraConfig if we have the required fields or they're provided via config
        if camera_config.get('host') and camera_config.get('username') and camera_config.get('password'):
            self.camera_config = TapoCameraConfig(**camera_config)
        else:
            # Create empty camera config - camera connection will be established later
            self.camera_config = None
        
        # General server config (not camera-specific)
        self.config = config or {}
        self.camera: Optional[Tapo] = None
        self.mcp = FastMCP(
            name="Tapo-Camera-MCP",
            version="0.3.0"  # Bump version for new features
        )
        
        # Initialize image cache
        self.image_cache = ImageCache(
            max_size_mb=self.config.get('cache_size_mb', 100),
            max_items=self.config.get('max_cache_items', 100)
        )
        
        # Configure directories
        self.temp_dir = Path(self.config.get('temp_dir', 'C:/temp'))
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Performance settings
        self.request_timeout = self.config.get('request_timeout', 30)
        self.max_retries = self.config.get('max_retries', 3)
        
        # Web server settings
        self.web_enabled = self.config.get('web_enabled', True)
        self.web_host = self.config.get('web_host', '0.0.0.0')
        self.web_port = self.config.get('web_port', 7777)  # Default port changed to 7777
        self.web_server = None
        
        # Initialize camera manager
        self.camera_manager = camera_manager
        
        # Initialize camera tracking
        self._active_camera = None
        self.cameras = {}  # Legacy camera storage for compatibility
        
        # Store default camera config for later initialization
        self.default_camera_config = None
        if self.config.get('host') and self.config.get('username') and self.config.get('password'):
            self.default_camera_config = {
                'name': 'default',
                'type': CameraType.TAPO,
                'params': {
                    'host': self.config['host'],
                    'username': self.config['username'],
                    'password': self.config['password']
                },
                'enabled': True
            }
        
        self._register_tools()
        
        # Start web server if enabled
        if self.web_enabled:
            self._start_web_server()
        

    async def initialize(self):
        """Initialize the camera manager and default camera if configured."""
        # Initialize camera manager
        await self.camera_manager.initialize()
        
        # Add default camera if config was provided
        if self.default_camera_config:
            try:
                await self.camera_manager.add_camera(self.default_camera_config)
                logger.info("Default camera initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize default camera: {e}")
    async def get_rtsp_url(self, camera_name: str = None) -> Dict[str, Any]:
        """Get RTSP stream URL for a camera."""
        camera_name = camera_name or self._active_camera
        if not camera_name or camera_name not in self.cameras:
            return {"status": "error", "message": "No valid camera specified"}
            
        camera = self.cameras[camera_name]['camera']
        config = self.cameras[camera_name]['config']
        
        try:
            # Try to get RTSP config
            rtsp_config = await camera.get_rtsp_config()
            if rtsp_config and rtsp_config.get('auth') == 'basic':
                rtsp_url = f"rtsp://{config['username']}:{config['password']}@{config['host']}:554/stream1"
                return {
                    "status": "success",
                    "camera": camera_name,
                    "rtsp_url": rtsp_url,
                    "player_commands": {
                        "vlc": f"vlc {rtsp_url}",
                        "ffmpeg": f"ffplay -rtsp_transport tcp {rtsp_url}"
                    }
                }
            return {"status": "error", "message": "RTSP not enabled on camera"}
        except Exception as e:
            return {"status": "error", "message": f"Failed to get RTSP URL: {str(e)}"}
        
    def _start_web_server(self):
        """Start the web server for the camera viewer."""
        try:
            self.web_server = TapoWebServer(
                mcp_server=self,
                host=self.web_host,
                port=self.web_port
            )
            # Run in background
            import threading
            web_thread = threading.Thread(
                target=self.web_server.run,
                daemon=True
            )
            web_thread.start()
            logger.info(f"Web server started at http://{self.web_host}:{self.web_port}")
        except Exception as e:
            logger.error(f"Failed to start web server: {e}")
    
    def _register_analysis_tools(self):
        """Register image analysis tools with the MCP server."""
        
        @self.mcp.tool()
        async def find_similar_images(params: dict) -> Dict[str, Any]:
            """
            Find images similar to a query image using DINOv3.
            
            Args:
                params: Dictionary containing:
                    - query_image: Path to the query image
                    - search_dir: Directory to search for similar images
                    - extensions: Optional list of image extensions to consider (default: ['.jpg', '.png', '.jpeg', '.bmp'])
                    - top_k: Number of similar images to return (default: 5)
                    
            Returns:
                Dictionary containing similar images and their similarity scores
            """
            try:
                query_image = params.get('query_image')
                search_dir = params.get('search_dir')
                
                if not query_image or not search_dir:
                    return {
                        "status": "error",
                        "message": "Both 'query_image' and 'search_dir' are required"
                    }
                
                # Convert to Path objects
                query_path = Path(query_image)
                search_path = Path(search_dir)
                
                if not query_path.exists():
                    return {
                        "status": "error",
                        "message": f"Query image not found: {query_image}"
                    }
                
                if not search_path.exists() or not search_path.is_dir():
                    return {
                        "status": "error",
                        "message": f"Search directory not found: {search_dir}"
                    }
                
                # Call the image analyzer
                result = await image_analyzer.find_similar_images(
                    query_image=query_path,
                    search_dir=search_path,
                    extensions=params.get('extensions'),
                    top_k=int(params.get('top_k', 5))
                )
                
                return result
                
            except Exception as e:
                return {
                    "status": "error",
                    "message": f"Failed to find similar images: {str(e)}"
                }
        
        @self.mcp.tool()
        async def list_cameras(params: dict = None) -> Dict[str, Any]:
            """
            List all registered cameras and their status.
            
            Args:
                params: Optional parameters (not used, for MCP compatibility)
                
            Returns:
                Dictionary with camera information
            """
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
            """
            Add a new camera.
            
            Args:
                params: Dictionary containing:
                    - name: Unique name for the camera
                    - type: Camera type ('tapo', 'webcam', etc.)
                    - params: Camera-specific parameters
                    - group: Optional group name
                    
            Returns:
                Status dictionary
            """
            try:
                name = params.get('name')
                if not name:
                    return {
                        'status': 'error',
                        'message': 'Camera name is required'
                    }
                
                # Add camera using camera manager
                camera_config = {
                    'name': name,
                    'type': params.get('type', 'tapo'),
                    'params': params.get('params', {})
                }
                
                success = await self.camera_manager.add_camera(camera_config)
                
                if success:
                    return {
                        'status': 'success',
                        'message': f'Camera {name} added successfully',
                        'connected': True
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
            """
            Remove a camera.
            
            Args:
                params: Dictionary containing:
                    - name: Name of the camera to remove
                    
            Returns:
                Status dictionary
            """
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
                        'message': f'Camera {name} not found or could not be removed'
                    }
                
            except Exception as e:
                return {
                    'status': 'error',
                    'message': f'Failed to remove camera: {str(e)}'
                }
        
        @self.mcp.tool()
        async def set_active_camera(params: dict) -> Dict[str, Any]:
            """
            Set the active camera.
            
            Args:
                params: Dictionary containing:
                    - name: Name of the camera to set as active
                    
            Returns:
                Status dictionary
            """
            try:
                name = params.get('name')
                if not name:
                    return {
                        'status': 'error',
                        'message': 'Camera name is required'
                    }
                
                success = await self.camera_manager.set_active_camera(name)
                
                if success:
                    return {
                        'status': 'success',
                        'message': f'Active camera set to {name}'
                    }
                else:
                    return {
                        'status': 'error',
                        'message': f'Camera {name} not found or could not be set as active'
                    }
                
            except Exception as e:
                return {
                    'status': 'error',
                    'message': f'Failed to set active camera: {str(e)}'
                }
        
        @self.mcp.tool()
        async def camera_groups(params: dict) -> Dict[str, Any]:
            """
            Manage camera groups.
            
            Args:
                params: Dictionary containing:
                    - action: 'list', 'add', 'remove', or 'list_group' (required)
                    - group: Group name (required for 'add', 'remove', 'list_group')
                    - camera: Camera name (required for 'add', 'remove')
                    
            Returns:
                Status dictionary
            """
            try:
                action = params.get('action')
                if not action:
                    return {
                        'status': 'error',
                        'message': 'Action is required'
                    }
                
                if action == 'list':
                    groups = await self.camera_manager.list_groups()
                    return {
                        'status': 'success',
                        'groups': groups
                    }
                
                elif action == 'list_group':
                    group = params.get('group')
                    if not group:
                        return {
                            'status': 'error',
                            'message': 'Group is required'
                        }
                    
                    cameras = await self.camera_manager.list_cameras_in_group(group)
                    return {
                        'status': 'success',
                        'group': group,
                        'cameras': cameras
                    }
                
                elif action == 'add':
                    group = params.get('group')
                    camera = params.get('camera')
                    
                    if not group or not camera:
                        return {
                            'status': 'error',
                            'message': 'Group and camera are required'
                        }
                    
                    success = await self.camera_manager.add_camera_to_group(camera, group)
                    
                    if success:
                        return {
                            'status': 'success',
                            'message': f'Camera {camera} added to group {group}'
                        }
                    else:
                        return {
                            'status': 'error',
                            'message': f'Failed to add camera {camera} to group {group}'
                        }
                
                elif action == 'remove':
                    group = params.get('group')
                    camera = params.get('camera')
                    
                    if not group or not camera:
                        return {
                            'status': 'error',
                            'message': 'Group and camera are required'
                        }
                    
                    success = await self.camera_manager.remove_camera_from_group(camera, group)
                    
                    if success:
                        return {
                            'status': 'success',
                            'message': f'Camera {camera} removed from group {group}'
                        }
                    else:
                        return {
                            'status': 'error',
                            'message': f'Failed to remove camera {camera} from group {group}'
                        }
                
                else:
                    return {
                        'status': 'error',
                        'message': f'Invalid action: {action}'
                    }
            
            except Exception as e:
                return {
                    'status': 'error',
                    'message': f'Failed to manage camera groups: {str(e)}'
                }
        
        @self.mcp.tool()
        async def get_stream_url(params: dict = None) -> Dict[str, Any]:
            """
            Get RTSP stream URL for viewing camera feed.
            
            Args:
                params: Dictionary containing:
                    - camera: Optional camera name (uses active camera if not specified)
            
            Returns:
                Dictionary with RTSP URL and viewing instructions
            """
            camera_name = (params or {}).get('camera')
            return await self.get_rtsp_url(camera_name)
        
        # Register the camera management tools
        self.list_cameras_tool = list_cameras
        self.add_camera_tool = add_camera
        self.remove_camera_tool = remove_camera
        self.set_active_camera_tool = set_active_camera
        self.camera_groups_tool = camera_groups
        self.get_stream_url_tool = get_stream_url
    
    @property
    def active_camera(self) -> Optional[Tapo]:
        """Get the currently active camera instance."""
        if not self._active_camera or self._active_camera not in self.cameras:
            return None
        return self.cameras[self._active_camera]['camera']
    
    async def add_camera(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add a new camera to the registry.
        
        Args:
            config: Camera configuration with keys:
                - name: Unique identifier for the camera
                - host: Camera IP/hostname
                - username: Camera username
                - password: Camera password
                - group: Optional group name
                - timeout: Optional request timeout (default: 10)
                
        Returns:
            dict: Operation status and camera info
        """
        try:
            name = config.get('name')
            if not name:
                return {"status": "error", "message": "Camera name is required"}
                
            if name in self.cameras:
                return {"status": "error", "message": f"Camera '{name}' already exists"}
            
            # Create and connect to camera
            camera = Tapo(
                config['host'],
                config['username'],
                config['password'],
                cloud_password=config.get('cloud_password', config['password']),
                timeout=config.get('timeout', 10)
            )
            
            # Test connection
            await camera.getBasicInfo()
            
            # Add to registry
            self.cameras[name] = {
                'camera': camera,
                'config': config,
                'last_seen': datetime.now().isoformat(),
                'status': 'online'
            }
            
            # Set as active if first camera
            if len(self.cameras) == 1:
                self._active_camera = name
            
            # Add to group if specified
            if 'group' in config:
                await self.add_camera_to_group(name, config['group'])
            
            return {
                "status": "success",
                "camera": name,
                "message": f"Camera '{name}' added successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to add camera: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": f"Failed to add camera: {str(e)}"
            }
    
    async def remove_camera(self, name: str) -> Dict[str, Any]:
        """
        Remove a camera from the registry.
        
        Args:
            name: Name of the camera to remove
            
        Returns:
            dict: Operation status
        """
        if name not in self.cameras:
            return {"status": "error", "message": f"Camera '{name}' not found"}
        
        try:
            # Close camera connection
            camera = self.cameras[name]['camera']
            if hasattr(camera, 'close'):
                await camera.close()
            
            # Remove from groups
            for group, cameras in list(self.camera_groups.items()):
                if name in cameras:
                    cameras.remove(name)
                    if not cameras:  # Remove empty groups
                        del self.camera_groups[group]
            
            # Remove from registry
            del self.cameras[name]
            
            # Update active camera if needed
            if self._active_camera == name:
                self._active_camera = next(iter(self.cameras.keys()), None)
            
            return {
                "status": "success",
                "message": f"Camera '{name}' removed successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to remove camera: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": f"Failed to remove camera: {str(e)}"
            }
    
    async def add_camera_to_group(self, camera_name: str, group_name: str) -> Dict[str, Any]:
        """
        Add a camera to a group.
        
        Args:
            camera_name: Name of the camera
            group_name: Name of the group
            
        Returns:
            dict: Operation status
        """
        if camera_name not in self.cameras:
            return {"status": "error", "message": f"Camera '{camera_name}' not found"}
        
        if group_name not in self.camera_groups:
            self.camera_groups[group_name] = []
        
        if camera_name not in self.camera_groups[group_name]:
            self.camera_groups[group_name].append(camera_name)
        
        return {
            "status": "success",
            "message": f"Camera '{camera_name}' added to group '{group_name}'"
        }
    
    async def remove_camera_from_group(self, camera_name: str, group_name: str) -> Dict[str, Any]:
        """
        Remove a camera from a group.
        
        Args:
            camera_name: Name of the camera
            group_name: Name of the group
            
        Returns:
            dict: Operation status
        """
        if group_name not in self.camera_groups:
            return {"status": "error", "message": f"Group '{group_name}' not found"}
        
        if camera_name in self.camera_groups[group_name]:
            self.camera_groups[group_name].remove(camera_name)
            
            # Remove group if empty
            if not self.camera_groups[group_name]:
                del self.camera_groups[group_name]
        
        return {
            "status": "success",
            "message": f"Camera '{camera_name}' removed from group '{group_name}'"
        }
    
    async def get_camera_status(self, name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get status of a specific camera or all cameras.
        
        Args:
            name: Optional camera name (returns all if None)
            
        Returns:
            dict: Camera status information
        """
        if name:
            if name not in self.cameras:
                return {"status": "error", "message": f"Camera '{name}' not found"}
            
            camera = self.cameras[name]
            try:
                info = await camera['camera'].getBasicInfo()
                camera['status'] = 'online'
                camera['last_seen'] = datetime.now().isoformat()
                
                return {
                    "status": "success",
                    "camera": name,
                    "info": info,
                    "last_seen": camera['last_seen'],
                    "config": camera['config']
                }
                
            except Exception as e:
                camera['status'] = 'error'
                return {
                    "status": "error",
                    "camera": name,
                    "error": str(e),
                    "last_seen": camera.get('last_seen')
                }
        
        # Return status for all cameras
        status = {}
        for name in self.cameras:
            status[name] = await self.get_camera_status(name)
        
        return {
            "status": "success",
            "cameras": status,
            "groups": self.camera_groups,
            "active_camera": self._active_camera,
            "timestamp": datetime.now().isoformat()
        }
    
    async def set_active_camera(self, name: str) -> Dict[str, Any]:
        """
        Set the active camera.
        
        Args:
            name: Name of the camera to set as active
            
        Returns:
            dict: Operation status
        """
        if name not in self.cameras:
            return {"status": "error", "message": f"Camera '{name}' not found"}
        
        self._active_camera = name
        return {
            "status": "success",
            "message": f"Active camera set to '{name}'"
        }
    
    async def _analyze_image(
        self, 
        image_path: Union[str, Path, bytes],
        prompt: str,
        use_cache: bool = True,
        cache_key: Optional[str] = None,
        max_retries: Optional[int] = None,
        advanced_analysis: bool = False
    ) -> Dict[str, Any]:
        """
        Prepare image for analysis with caching and retry logic.
        
        Args:
            image_path: Path to image file or image data
            prompt: Analysis prompt
            use_cache: Whether to use cached results if available
            cache_key: Optional custom cache key (default: hash of image + prompt)
            max_retries: Maximum number of retry attempts
            advanced_analysis: Whether to use DINOv3 for advanced analysis
            
        Returns:
            Analysis results dictionary
        """
        # First, handle advanced DINOv3 analysis if requested
        if advanced_analysis and isinstance(image_path, (str, Path)):
            try:
                dinov3_result = await image_analyzer.analyze_image(image_path)
                if dinov3_result["status"] == "success":
                    return {
                        "status": "success",
                        "analysis": {
                            "type": "advanced",
                            "features": dinov3_result.get("features"),
                            "feature_dim": dinov3_result.get("feature_dim")
                        },
                        "timestamp": datetime.now().isoformat()
                    }
            except Exception as e:
                logger.warning(f"DINOv3 analysis failed, falling back to basic analysis: {e}")
                
        # Fall back to basic analysis
        from PIL import Image, ImageFile
        import hashlib
        
        # Enable loading of truncated images
        ImageFile.LOAD_TRUNCATED_IMAGES = True
        
        # Generate cache key if not provided
        if cache_key is None and use_cache:
            cache_key = hashlib.md5(
                (str(image_path) + str(prompt)).encode('utf-8')
            ).hexdigest()
            
            # Try to get from cache first
            if use_cache and cache_key:
                cached = await self.image_cache.get(cache_key)
                if cached:
                    return {
                        **cached,
                        "cached": True,
                        "cache_key": cache_key
                    }
        
        retries = max_retries or self.max_retries
        last_error = None
        
        for attempt in range(retries):
            try:
                # Handle both file path and bytes input
                if isinstance(image_path, (str, Path)):
                    with Image.open(image_path) as img:
                        # Convert to RGB if needed
                        if img.mode != 'RGB':
                            img = img.convert('RGB')
                        
                        # Resize if too large (max 2048x2048 for LLM efficiency)
                        max_size = 2048
                        if max(img.size) > max_size:
                            img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                        
                        # Convert to bytes if not already
                        img_io = io.BytesIO()
                        img.save(img_io, format='JPEG', quality=85, optimize=True)
                        image_data = img_io.getvalue()
                elif isinstance(image_path, bytes):
                    image_data = image_path
                else:
                    raise ValueError("image_path must be a file path or bytes")
                
                # Encode to base64 for multimodal LLM
                base64_data = base64.b64encode(image_data).decode('utf-8')
                
                # Prepare result
                result = {
                    "image_base64": base64_data,
                    "image_path": str(image_path) if not isinstance(image_path, bytes) else "<in-memory>",
                    "prompt": prompt,
                    "media_type": "image/jpeg",
                    "analysis_ready": True,
                    "timestamp": datetime.now().isoformat(),
                    "image_size_kb": len(image_data) / 1024,
                    "cached": False,
                    "attempts": attempt + 1
                }
                
                # Cache the result
                if use_cache and cache_key:
                    await self.image_cache.set(cache_key, result)
                    result["cache_key"] = cache_key
                
                return result
                
            except (IOError, OSError) as e:
                last_error = e
                if attempt < retries - 1:
                    await asyncio.sleep(1 * (attempt + 1))  # Exponential backoff
                    continue
                
                logger.error(f"Failed to process image after {retries} attempts: {str(e)}")
                return {
                    "status": "error",
                    "error": f"Failed to process image: {str(e)}",
                    "analysis_ready": False,
                    "timestamp": datetime.now().isoformat(),
                    "attempts": attempt + 1
                }
            
            except Exception as e:
                last_error = e
                logger.error(f"Unexpected error processing image: {str(e)}", exc_info=True)
                return {
                    "status": "error",
                    "error": f"Unexpected error: {str(e)}",
                    "analysis_ready": False,
                    "timestamp": datetime.now().isoformat(),
                    "attempts": attempt + 1
                }
        
        return {
            "status": "error",
            "error": f"Max retries ({retries}) exceeded. Last error: {str(last_error)}",
            "analysis_ready": False,
            "timestamp": datetime.now().isoformat(),
            "attempts": retries
        }
    
    def _register_tools(self):
        """Register all MCP tools."""
        # Register camera management tools first
        self._register_camera_tools()
        
        # Register other tools...
        
        def format_tool_help(tool_name: str, tool_info: dict) -> dict:
            """Format tool information for the help system."""
            help_info = {
                "name": tool_name,
                "description": tool_info.get("description", "No description available"),
                "parameters": []
            }
            
            if "parameters" in tool_info:
                for param_name, param_info in tool_info["parameters"].items():
                    param_data = {
                        "name": param_name,
                        "type": param_info.get("type", "any"),
                        "required": param_info.get("required", False),
                        "description": param_info.get("description", "No description"),
                        "default": param_info.get("default", "(required)" if param_info.get("required", False) else None)
                    }
                    help_info["parameters"].append(param_data)
                    
            return help_info
            
        @self.mcp.tool()
        async def help(params: dict = None) -> dict:
            """
            Get comprehensive help about available tools and their usage.
            
            This help system provides multi-level information about all available tools,
            their parameters, and usage examples. Use the 'tool' parameter to get
            detailed information about a specific tool.
            
            Args:
                params: Dictionary containing help parameters:
                    - tool: (Optional) Name of the tool to get detailed help for
                    - level: (Optional) Detail level (basic, full, examples)
                    
            Returns:
                dict: Structured help information
            """
            if not params:
                params = {}
                
            tool_name = params.get("tool")
            level = params.get("level", "basic")
            
            # Define tool metadata for help system
            tools_metadata = {
                "capture_still": {
                    "description": "Capture a still image from the camera with optional analysis",
                    "parameters": {
                        "save_to_temp": {
                            "type": "bool",
                            "required": False,
                            "default": True,
                            "description": "Save the captured image to the temporary directory"
                        },
                        "analyze": {
                            "type": "bool",
                            "required": False,
                            "default": False,
                            "description": "Perform multimodal analysis on the captured image"
                        },
                        "prompt": {
                            "type": "str",
                            "required": False,
                            "description": "Custom analysis prompt (only used if analyze=True)"
                        },
                        "camera_name": {
                            "type": "str",
                            "required": False,
                            "default": "main",
                            "description": "Identifier for the camera (used in filenames)"
                        }
                    },
                    "examples": [
                        "capture_still({\"analyze\": true, \"prompt\": \"Describe this image in detail\"})",
                        "capture_still({\"save_to_temp\": false})"
                    ]
                },
                "analyze_image": {
                    "description": "Analyze an existing image file with the multimodal LLM",
                    "parameters": {
                        "image_path": {
                            "type": "str",
                            "required": True,
                            "description": "Path to the image file to analyze"
                        },
                        "prompt": {
                            "type": "str",
                            "required": False,
                            "description": "Custom analysis prompt"
                        },
                        "preset": {
                            "type": "str",
                            "required": False,
                            "description": "Use a predefined analysis preset (security/food/pets/delivery/general)",
                            "options": ["security", "food", "pets", "delivery", "general"]
                        }
                    },
                    "examples": [
                        'analyze_image({"image_path": "/path/to/image.jpg", "preset": "security"})',
                        'analyze_image({"image_path": "/path/to/image.jpg", "prompt": "What objects do you see?"})'
                    ]
                },
                "security_scan": {
                    "description": "Perform a security scan using the camera feed",
                    "parameters": {
                        "threat_types": {
                            "type": "list[str]",
                            "required": False,
                            "default": ["person", "unknown_person", "package"],
                            "description": "List of threat types to detect"
                        },
                        "save_images": {
                            "type": "bool",
                            "required": False,
                            "default": True,
                            "description": "Save captured images to disk"
                        }
                    },
                    "examples": [
                        'security_scan({"threat_types": ["person", "package"]})',
                        'security_scan({"save_images": false})'
                    ]
                },
                "help": {
                    "description": "Show help information about available tools",
                    "parameters": {
                        "tool": {
                            "type": "str",
                            "required": False,
                            "description": "Name of the tool to get detailed help for"
                        },
                        "level": {
                            "type": "str",
                            "required": False,
                            "default": "basic",
                            "description": "Detail level (basic, full, examples)",
                            "options": ["basic", "full", "examples"]
                        }
                    },
                    "examples": [
                        'help({"tool": "capture_still"})',
                        'help({"level": "full"})'
                    ]
                }
            }
            
            # Add standard camera control tools to metadata
            standard_tools = {
                "connect_camera": "Connect to a Tapo camera",
                "disconnect_camera": "Disconnect from the current camera",
                "get_camera_info": "Get information about the connected camera",
                "get_camera_status": "Get the current status of the camera",
                "move_ptz": "Control the camera's PTZ (Pan-Tilt-Zoom) functions",
                "get_stream_url": "Get the RTSP stream URL for the camera",
                "set_motion_detection": "Enable or disable motion detection",
                "set_led_enabled": "Control the camera's LED indicator",
                "set_privacy_mode": "Enable or disable privacy mode (lens mask)",
                "reboot_camera": "Reboot the camera",
                "get_ptz_presets": "Get all saved PTZ presets"
            }
            
            for tool_name, description in standard_tools.items():
                if tool_name not in tools_metadata:
                    tools_metadata[tool_name] = {"description": description}
            
            # If a specific tool is requested, return detailed help for that tool
            if tool_name:
                if tool_name not in tools_metadata:
                    return {
                        "status": "error",
                        "message": f"Unknown tool: {tool_name}",
                        "available_tools": sorted(list(tools_metadata.keys()))
                    }
                
                tool_info = tools_metadata[tool_name]
                help_response = format_tool_help(tool_name, tool_info)
                
                if level in ["full", "examples"] and "examples" in tool_info:
                    help_response["examples"] = tool_info["examples"]
                
                return {
                    "status": "success",
                    "tool": help_response,
                    "timestamp": datetime.now().isoformat()
                }
            
            # Return list of all tools with basic info
            tools_list = []
            for name, info in tools_metadata.items():
                tools_list.append({
                    "name": name,
                    "description": info.get("description", "No description available"),
                    "parameters": [{"name": p} for p in info.get("parameters", {}).keys()]
                })
            
            return {
                "status": "success",
                "help": {
                    "introduction": "Tapo Camera MCP Server - Available Tools",
                    "usage": "Call help({'tool': 'tool_name'}) for detailed information about a specific tool",
                    "tools": tools_list,
                    "timestamp": datetime.now().isoformat()
                }
            }
        
        # Camera connection management
        @self.mcp.tool()
        async def connect_camera(params: dict) -> Dict[str, Any]:
            """
            Connect to a Tapo camera.
            
            Args:
                params: Dictionary containing connection parameters:
                    - host: Camera IP address or hostname
                    - username: Camera username
                    - password: Camera password
                    - verify_ssl: Verify SSL certificate (optional, default: True)
                
            Returns:
                dict: Connection status and camera information
            """
            try:
                host = params.get("host")
                username = params.get("username")
                password = params.get("password")
                verify_ssl = params.get("verify_ssl", True)
                
                if not all([host, username, password]):
                    raise ValueError("Missing required parameters: host, username, password")
                
                if self.camera:
                    await self.camera.close()
                
                self.camera = Tapo(host, username, password, cloud_password=password)
                await self.camera.login()
                info = await self.camera.getBasicInfo()
                
                return {
                    "status": "connected",
                    "camera_info": {
                        "model": info.get("device_info", {}).get("device_model"),
                        "firmware": info.get("firmware_version"),
                        "mac_address": info.get("mac"),
                        "ip_address": host,
                        "host": host,
                        "username": username,
                        "password": password
                    }
                }
            except Exception as e:
                logger.error(f"Failed to connect to camera: {str(e)}")
                return {"status": "error", "message": str(e)}
        
        @self.mcp.tool()
        async def disconnect_camera(params: dict = None) -> Dict[str, str]:
            """
            Disconnect from the Tapo camera.
            
            Args:
                params: Dictionary containing any parameters (unused)
                
            Returns:
                dict: Disconnection status
            """
            if self.camera:
                await self.camera.close()
                self.camera = None
            return {"status": "disconnected"}
        
        # Camera information and status
        @self.mcp.tool()
        async def get_camera_info(params: dict = None) -> Dict[str, Any]:
            """
            Get detailed information about the connected camera.
            
            Args:
                params: Dictionary containing any parameters (unused)
                
            Returns:
                dict: Camera information
            """
            if not self.camera:
                raise ValueError("Not connected to a camera. Call connect_camera first.")
            
            try:
                info = await self.camera.getBasicInfo()
                device_info = info.get("device_info", {})
                
                return {
                    "status": "success",
                    "model": device_info.get("device_model", "Unknown"),
                    "serial_number": device_info.get("device_id", ""),
                    "firmware_version": info.get("firmware_version", ""),
                    "mac_address": info.get("mac", ""),
                    "ip_address": self.camera.host,
                    "wifi_signal": info.get("signal_level", 0),
                    "wifi_ssid": info.get("ssid", "")
                }
            except Exception as e:
                logger.error(f"Failed to get camera info: {str(e)}")
                return {"status": "error", "message": str(e)}
        
        @self.mcp.tool()
        async def get_camera_status(params: dict = None) -> Dict[str, Any]:
            """
            Get the current status of the camera.
            
            Args:
                params: Dictionary containing any parameters (unused)
                
            Returns:
                dict: Current camera status
            """
            if not self.camera:
                return {"status": "error", "message": "Not connected to a camera. Call connect_camera first."}
            
            try:
                info = await self.camera.getBasicInfo()
                motion_detection = await self.camera.getMotionDetection()
                led_status = await self.camera.getLED()
                
                return {
                    "status": "success",
                    "online": True,
                    "recording": info.get("record", {}).get("recording", False),
                    "motion_detected": motion_detection.get("enabled", False),
                    "privacy_mode": info.get("lens_mask", {}).get("lens_mask", False),
                    "led_enabled": led_status.get("enabled", True),
                    "uptime": info.get("device_info", {}).get("up_time", 0),
                    "storage": {
                        "total": 0,  # These would come from camera.getStorageInfo()
                        "used": 0,
                        "free": 0
                    }
                }
            except Exception as e:
                error_msg = f"Failed to get camera status: {str(e)}"
                logger.error(error_msg)
                return {"status": "error", "message": error_msg}
        
        # PTZ control
        @self.mcp.tool()
        async def move_ptz(params: dict) -> Dict[str, Any]:
            """
            Move the camera PTZ (Pan-Tilt-Zoom).
            
            Args:
                params: Dictionary containing PTZ parameters:
                    - pan: Pan position (-1.0 to 1.0, default: 0.0)
                    - tilt: Tilt position (-1.0 to 1.0, default: 0.0)
                    - zoom: Zoom level (0.0 to 1.0, default: 0.0)
                
            Returns:
                dict: Operation status
            """
            if not self.camera:
                return {"status": "error", "message": "Not connected to a camera. Call connect_camera first."}
            
            try:
                pan = float(params.get("pan", 0.0))
                tilt = float(params.get("tilt", 0.0))
                zoom = float(params.get("zoom", 0.0))
                
                # Validate parameter ranges
                if not (-1.0 <= pan <= 1.0):
                    raise ValueError("Pan value must be between -1.0 and 1.0")
                if not (-1.0 <= tilt <= 1.0):
                    raise ValueError("Tilt value must be between -1.0 and 1.0")
                if not (0.0 <= zoom <= 1.0):
                    raise ValueError("Zoom value must be between 0.0 and 1.0")
                
                # Move the camera PTZ
                if pan != 0 or tilt != 0:
                    await self.camera.moveMotor(pan, tilt)
                if zoom != 0:
                    await self.camera.zoom(zoom)
                
                return {
                    "status": "success", 
                    "message": "PTZ movement completed",
                    "position": {"pan": pan, "tilt": tilt, "zoom": zoom}
                }
            except Exception as e:
                logger.error(f"Failed to move PTZ: {str(e)}")
                return {"status": "error", "message": str(e)}
        
        # Stream management
        @self.mcp.tool()
        async def get_stream_url(quality: str = "hd") -> StreamInfo:
            """
            Get the RTSP stream URL.
            
            Args:
                quality: Stream quality (hd/sd)
                
            Returns:
                StreamInfo: Stream information
            """
            if not self.camera:
                raise ValueError("Not connected to a camera. Call connect_camera first.")
            
            try:
                # In a real implementation, this would get the actual RTSP URL from the camera
                # This is a simplified version that assumes a standard RTSP URL format
                rtsp_url = f"rtsp://{self.camera.host}/stream1"
                
                return StreamInfo(
                    url=rtsp_url,
                    type="rtsp",
                    quality=quality
                )
            except Exception as e:
                logger.error(f"Failed to get stream URL: {str(e)}")
                raise
        
        # Motion detection control
        @self.mcp.tool()
        async def set_motion_detection(
            enabled: bool = Field(..., description="Enable or disable motion detection")
        ) -> Dict[str, Any]:
            """
            Enable or disable motion detection.
            
            Args:
                enabled: Whether to enable motion detection
                
            Returns:
                dict: Operation status
            """
            if not self.camera:
                raise ValueError("Not connected to a camera. Call connect_camera first.")
            
            try:
                await self.camera.setMotionDetection(enabled)
                return {"status": "success", "motion_detection": enabled}
            except Exception as e:
                logger.error(f"Failed to set motion detection: {str(e)}")
                return {"status": "error", "message": str(e)}
        
        # LED control
        @self.mcp.tool()
        async def set_led_enabled(
            enabled: bool = Field(..., description="Enable or disable the camera LED")
        ) -> Dict[str, Any]:
            """
            Enable or disable the camera LED.
            
            Args:
                enabled: Whether to enable the LED
                
            Returns:
                dict: Operation status
            """
            if not self.camera:
                raise ValueError("Not connected to a camera. Call connect_camera first.")
            
            try:
                await self.camera.setLED(enabled)
                return {"status": "success", "led_enabled": enabled}
            except Exception as e:
                logger.error(f"Failed to set LED state: {str(e)}")
                return {"status": "error", "message": str(e)}
        
        # Privacy mode control
        @self.mcp.tool()
        async def set_privacy_mode(
            enabled: bool = Field(..., description="Enable or disable privacy mode")
        ) -> Dict[str, Any]:
            """
            Enable or disable privacy mode (lens mask).
            
            Args:
                enabled: Whether to enable privacy mode
                
            Returns:
                dict: Operation status
            """
            if not self.camera:
                raise ValueError("Not connected to a camera. Call connect_camera first.")
            
            try:
                await self.camera.setPrivacyMode(enabled)
                return {"status": "success", "privacy_mode": enabled}
            except Exception as e:
                logger.error(f"Failed to set privacy mode: {str(e)}")
                return {"status": "error", "message": str(e)}
        
        # Reboot camera
        @self.mcp.tool()
        async def reboot_camera(params: Dict[str, Any] = None) -> Dict[str, Any]:
            """
            Reboot the camera.
            
            Args:
                params: Dictionary containing any parameters (unused, for API consistency)
                
            Returns:
                dict: Operation status
            """
            if not self.camera:
                raise ValueError("Not connected to a camera. Call connect_camera first.")
            
            try:
                await self.camera.reboot()
                return {"status": "success", "message": "Camera is rebooting"}
            except Exception as e:
                logger.error(f"Failed to reboot camera: {str(e)}")
                return {"status": "error", "message": str(e)}
        
        # Get camera presets
        @self.mcp.tool()
        async def get_ptz_presets() -> Dict[str, Any]:
            """
            Get all saved PTZ presets.
            
            Returns:
                dict: Dictionary of preset names and their positions
            """
            if not self.camera:
                raise ValueError("Not connected to a camera. Call connect_camera first.")
            
            try:
                presets = await self.camera.getPresets()
                return {"status": "success", "presets": presets}
            except Exception as e:
                logger.error(f"Failed to get PTZ presets: {str(e)}")
                return {"status": "error", "message": str(e)}
                
        @self.mcp.tool()
        async def capture_still(params: dict) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
            """
            Capture still image(s) from one or more cameras with optional batch analysis.
            
            Args:
                params: Dictionary containing:
                    - camera_name: (str|list) Camera identifier(s) or 'all' for all cameras
                    - save_to_temp: Save images to temp directory (default: True)
                    - analyze: Perform multimodal analysis (default: False)
                    - prompt: Analysis prompt or preset name (default: "general")
                    - group: Capture from all cameras in this group (optional)
                    - batch_size: Max concurrent captures (default: 4)
                    - use_cache: Use cached analysis when available (default: True)
                    
            Returns:
                dict: Single capture result or list of results for batch operations
            """
            from typing import List, Dict, Any, Union
            import asyncio
            from collections import defaultdict
            
            async def capture_single(camera_name: str, camera: Tapo, idx: int) -> Dict[str, Any]:
                """Capture from a single camera with retry logic."""
                last_error = None
                for attempt in range(self.max_retries):
                    try:
                        # Capture image with timeout
                        image_data = await asyncio.wait_for(
                            camera.getSnapshot(), 
                            timeout=self.request_timeout
                        )
                        
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        result = {
                            "status": "success",
                            "camera": camera_name,
                            "timestamp": datetime.now().isoformat(),
                            "image_size": len(image_data) if image_data else 0,
                            "attempts": attempt + 1
                        }
                        
                        # Save to temp directory if requested
                        if params.get("save_to_temp", True) and image_data:
                            os.makedirs(self.temp_dir, exist_ok=True)
                            temp_path = str(self.temp_dir / f"tapo_{camera_name}_{timestamp}_{idx}.jpg")
                            
                            with open(temp_path, 'wb') as f:
                                f.write(image_data)
                            
                            result["saved_path"] = temp_path
                            
                            # Perform analysis if requested
                            if params.get("analyze", False):
                                prompt = params.get("prompt", "general")
                                # Check if prompt is a preset
                                if hasattr(presets, prompt.upper()):
                                    prompt = getattr(presets, prompt.upper())
                                
                                analysis = await self._analyze_image(
                                    temp_path, 
                                    prompt=prompt,
                                    use_cache=params.get("use_cache", True),
                                    cache_key=f"{camera_name}_{os.path.basename(temp_path)}_{hash(prompt)}"
                                )
                                result["analysis"] = analysis
                        
                        return result
                        
                    except (asyncio.TimeoutError, Exception) as e:
                        last_error = str(e)
                        if attempt < self.max_retries - 1:
                            await asyncio.sleep(1 * (attempt + 1))  # Exponential backoff
                            continue
                        
                        logger.error(f"Failed to capture from {camera_name} after {self.max_retries} attempts: {last_error}")
                        return {
                            "status": "error",
                            "camera": camera_name,
                            "error": last_error,
                            "timestamp": datetime.now().isoformat(),
                            "attempts": attempt + 1
                        }
            
            try:
                # Determine which cameras to use
                camera_name = params.get("camera_name", "main")
                group_name = params.get("group")
                
                # Get target cameras
                if group_name:
                    # Capture from camera group
                    if group_name not in self.camera_groups:
                        return {"status": "error", "message": f"Camera group '{group_name}' not found"}
                    camera_names = self.camera_groups[group_name]
                    cameras = {name: self.cameras[name] for name in camera_names if name in self.cameras}
                elif camera_name == "all":
                    # Capture from all registered cameras
                    cameras = self.cameras.copy()
                    camera_names = list(cameras.keys())
                elif isinstance(camera_name, list):
                    # Capture from specified list of cameras
                    camera_names = [str(name) for name in camera_name]
                    cameras = {name: self.cameras[name] for name in camera_names if name in self.cameras}
                else:
                    # Single camera capture (legacy behavior)
                    if not self.camera:
                        return {"status": "error", "message": "Not connected to a camera. Call connect_camera first."}
                    cameras = {camera_name: self.camera}
                    camera_names = [camera_name]
                
                if not cameras:
                    return {"status": "error", "message": "No cameras available for capture"}
                
                # Process cameras in batches
                batch_size = min(params.get("batch_size", 4), 8)  # Max 8 concurrent captures
                results = []
                
                for i in range(0, len(camera_names), batch_size):
                    batch_cameras = {
                        name: cameras[name] 
                        for name in camera_names[i:i + batch_size] 
                        if name in cameras
                    }
                    
                    # Start all captures in parallel
                    tasks = [
                        capture_single(name, cam, i + idx) 
                        for idx, (name, cam) in enumerate(batch_cameras.items())
                    ]
                    
                    # Wait for batch to complete
                    batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # Process results
                    for res in batch_results:
                        if isinstance(res, Exception):
                            logger.error(f"Error in batch capture: {str(res)}")
                            results.append({
                                "status": "error",
                                "error": str(res),
                                "timestamp": datetime.now().isoformat()
                            })
                        else:
                            results.append(res)
                
                # Return single result for single camera, list for multiple
                return results[0] if len(results) == 1 else results
                
            except Exception as e:
                logger.error(f"Failed to capture images: {str(e)}", exc_info=True)
                return {
                    "status": "error", 
                    "message": f"Capture failed: {str(e)}",
                    "timestamp": datetime.now().isoformat()
                }
                
        @self.mcp.tool()
        async def analyze_image(params: dict) -> Dict[str, Any]:
            """
            Analyze one or more images with multimodal LLM using advanced features.
            
            Args:
                params: Dictionary containing:
                    - image_path: (str|list) Path to image file(s) or directory
                    - prompt: (str) Analysis prompt or preset name (default: "general")
                    - preset: (str) Use a predefined analysis preset (overrides prompt)
                    - use_cache: (bool) Use cached results (default: True)
                    - batch_size: (int) Max concurrent analyses (default: 4)
                    - output_format: (str) 'full', 'summary', or 'minimal' (default: 'full')
                    - confidence_threshold: (float) Filter results by confidence (0.0-1.0)
                    
            Returns:
                dict: Analysis results with metadata, or list of results for batch processing
            """
            from typing import Union, List, Dict, Any
            import asyncio
            from pathlib import Path
            
            async def process_single_image(
                img_path: Union[str, Path], 
                prompt: str, 
                use_cache: bool,
                idx: int = 0
            ) -> Dict[str, Any]:
                """Process a single image with error handling and retries."""
                img_path = Path(img_path)
                if not img_path.exists():
                    return {
                        "status": "error",
                        "image": str(img_path),
                        "error": "File not found",
                        "timestamp": datetime.now().isoformat()
                    }
                
                # Generate cache key
                cache_key = None
                if use_cache:
                    import hashlib
                    with open(img_path, 'rb') as f:
                        file_hash = hashlib.md5(f.read()).hexdigest()
                    cache_key = f"analyze_{file_hash}_{hash(prompt)}"
                
                try:
                    result = await self._analyze_image(
                        image_path=str(img_path),
                        prompt=prompt,
                        use_cache=use_cache,
                        cache_key=cache_key,
                        max_retries=self.max_retries
                    )
                    
                    if "error" in result:
                        return {
                            "status": "error",
                            "image": str(img_path),
                            "error": result.get("error", "Unknown error"),
                            "timestamp": datetime.now().isoformat(),
                            "attempts": result.get("attempts", 1)
                        }
                    
                    # Apply confidence threshold if specified
                    confidence = result.get("analysis", {}).get("confidence")
                    if (isinstance(confidence, (int, float)) and 
                        "confidence_threshold" in params and 
                        confidence < params["confidence_threshold"]):
                        result["filtered"] = True
                    
                    # Format output based on requested format
                    output_format = params.get("output_format", "full").lower()
                    if output_format == "minimal":
                        return {
                            "status": "success",
                            "image": str(img_path),
                            "analysis": result.get("analysis", {}).get("summary", "No analysis available"),
                            "timestamp": datetime.now().isoformat()
                        }
                    elif output_format == "summary":
                        return {
                            "status": "success",
                            "image": str(img_path),
                            "analysis": {
                                "summary": result.get("analysis", {}).get("summary"),
                                "confidence": result.get("analysis", {}).get("confidence"),
                                "objects": result.get("analysis", {}).get("objects", []),
                                "tags": result.get("analysis", {}).get("tags", [])
                            },
                            "timestamp": datetime.now().isoformat(),
                            "cached": result.get("cached", False)
                        }
                    
                    # Full format (default)
                    return {
                        "status": "success",
                        "image": str(img_path),
                        "metadata": {
                            "size": f"{result.get('image_size_kb', 0):.2f} KB",
                            "dimensions": result.get("analysis", {}).get("dimensions"),
                            "cached": result.get("cached", False)
                        },
                        "analysis": result.get("analysis", {}),
                        "timestamp": datetime.now().isoformat()
                    }
                    
                except Exception as e:
                    logger.error(f"Failed to analyze {img_path}: {str(e)}", exc_info=True)
                    return {
                        "status": "error",
                        "image": str(img_path),
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    }
            
            try:
                # Process input parameters
                image_path = params.get("image_path")
                if not image_path:
                    return {"status": "error", "message": "Missing required parameter: image_path"}
                
                # Handle preset or custom prompt
                prompt = params.get("prompt", "general")
                if "preset" in params:
                    preset = str(params["preset"]).upper()
                    if hasattr(presets, preset):
                        prompt = getattr(presets, preset)
                
                use_cache = params.get("use_cache", True)
                batch_size = min(params.get("batch_size", 4), 8)  # Max 8 concurrent analyses
                
                # Handle different input types
                if isinstance(image_path, (str, Path)):
                    image_path = Path(image_path)
                    if image_path.is_dir():
                        # Process all images in directory
                        image_paths = list(image_path.glob("*.jpg")) + list(image_path.glob("*.jpeg")) + \
                                    list(image_path.glob("*.png"))
                        if not image_paths:
                            return {"status": "error", "message": f"No image files found in {image_path}"}
                    else:
                        # Single file
                        image_paths = [image_path]
                elif isinstance(image_path, list):
                    # List of file paths
                    image_paths = [Path(p) for p in image_path if Path(p).exists()]
                else:
                    return {"status": "error", "message": "Invalid image_path format"}
                
                if not image_paths:
                    return {"status": "error", "message": "No valid image files found"}
                
                # Process images in batches
                results = []
                for i in range(0, len(image_paths), batch_size):
                    batch = image_paths[i:i + batch_size]
                    tasks = [
                        process_single_image(path, prompt, use_cache, i + idx)
                        for idx, path in enumerate(batch)
                    ]
                    batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # Process batch results
                    for res in batch_results:
                        if isinstance(res, Exception):
                            logger.error(f"Error in batch processing: {str(res)}")
                            results.append({
                                "status": "error",
                                "error": str(res),
                                "timestamp": datetime.now().isoformat()
                            })
                        else:
                            results.append(res)
                
                # Return single result for single image, list for multiple
                if len(results) == 1:
                    return results[0]
                
                # Add summary for batch processing
                success_count = sum(1 for r in results if r.get("status") == "success")
                return {
                    "status": "success",
                    "summary": {
                        "total_images": len(results),
                        "successful": success_count,
                        "failed": len(results) - success_count,
                        "processing_time_seconds": (datetime.now() - start_time).total_seconds()
                    },
                    "results": results,
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Image analysis failed: {str(e)}", exc_info=True)
                return {
                    "status": "error",
                    "message": f"Analysis failed: {str(e)}",
                    "timestamp": datetime.now().isoformat()
                }

        @self.mcp.tool()
        async def security_scan(params: dict) -> Dict[str, Any]:
            """
            Perform security scan across multiple cameras.
            
            Args:
                params: Dictionary containing:
                    - cameras: List of camera configs (default: current camera)
                    - threat_types: Types to detect (default: ["person", "unknown_person", "package"])
                    - save_images: Save captured images (default: True)
            
            Returns:
                dict: Security scan results from all cameras
            """
            import uuid
            
            # For now, use current camera (future: multi-camera support)
            if not self.camera:
                return {"status": "error", "message": "No camera connected"}
            
            threat_types = params.get("threat_types", ["person", "unknown_person", "package"])
            save_images = params.get("save_images", True)
            
            scan_id = str(uuid.uuid4())[:8]
            
            try:
                # Capture image for analysis
                capture_result = await self.capture_still({
                    "save_to_temp": save_images,
                    "analyze": True,
                    "prompt": f'''Security analysis for: {", ".join(threat_types)}

CRITICAL ASSESSMENT NEEDED:
- Unknown people (not family members)
- Suspicious or unusual activity  
- Packages or deliveries
- Unusual objects or vehicles
- Animals (pets vs wildlife)

Respond with:
- Threat level: none/low/medium/high
- Description of what you see
- Specific concerns identified
- Recommended action if any''',
                    "camera_name": f"security_scan_{scan_id}"
                })
                
                # Format security scan result
                return {
                    "status": "success",
                    "scan_id": scan_id,
                    "scan_type": "security",
                    "cameras_scanned": 1,
                    "timestamp": datetime.now().isoformat(),
                    "threat_types_monitored": threat_types,
                    "results": [capture_result]
                }
                
            except Exception as e:
                logger.error(f"Security scan failed: {str(e)}")
                return {
                    "status": "error", 
                    "scan_id": scan_id,
                    "message": str(e),
                    "timestamp": datetime.now().isoformat()
                }
    
    def run(self, host: str = "0.0.0.0", port: int = 8000, stdio: bool = True, direct: bool = False):
        """
        Run the MCP server with both HTTP and stdio transports.
        
        Args:
            host: Host to bind the HTTP server to
            port: Port to bind the HTTP server to
            stdio: Enable stdio transport
            direct: If True, runs in direct mode (no event loop management, for Claude Desktop)
        """
        if direct:
            # In direct mode, we don't manage the event loop - Claude Desktop will handle it
            if stdio:
                logger.info("Running in direct mode with stdio transport (Claude Desktop compatible)")
                self.mcp.create_stdio_server()
            else:
                logger.info("Running in direct mode with HTTP transport")
                self.mcp.create_http_server(host=host, port=port)
            
            # Initialize camera manager in direct mode
            # We need to ensure initialization happens when the event loop is available
            asyncio.create_task(self.initialize())
            return
            
        # Original server mode with event loop management
        # Start HTTP server
        http_server = self.mcp.create_http_server(host=host, port=port)
        
        # Start stdio server if requested
        stdio_server = None
        if stdio:
            stdio_server = self.mcp.create_stdio_server()
        
        # Run the event loop
        loop = asyncio.get_event_loop()
        # Initialize camera manager
        loop.run_until_complete(self.initialize())
        
        try:
            logger.info(f"Starting MCP server on http://{host}:{port}")
            if stdio:
                logger.info("Stdio transport enabled")
            
            loop.run_forever()
        except KeyboardInterrupt:
            logger.info("Shutting down...")
        finally:
            # Clean up
            if stdio_server:
                stdio_server.close()
                loop.run_until_complete(stdio_server.wait_closed())
            
            http_server.close()
            loop.run_until_complete(http_server.wait_closed())
            
            # Close camera connection if open
            if self.camera:
                loop.run_until_complete(self.camera.close())
            
            loop.close()


def main():
    """Main entry point for the Tapo Camera MCP server."""
    import argparse
    
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Tapo Camera MCP Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind the HTTP server to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind the HTTP server to")
    parser.add_argument("--no-stdio", action="store_false", dest="stdio", 
                       help="Disable stdio transport")
    parser.add_argument("--direct", action="store_true", 
                       help="Run in direct mode (no event loop management, for Claude Desktop)")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()
    
    # Configure logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Load configuration from environment variables
    config = {
        'host': os.getenv('TAPO_CAMERA_HOST'),
        'username': os.getenv('TAPO_CAMERA_USERNAME'),
        'password': os.getenv('TAPO_CAMERA_PASSWORD'),
    }
    
    # Remove None values to let defaults apply
    config = {k: v for k, v in config.items() if v is not None}
    
    # Create and run the server
    server = TapoCameraServer(config)
    
    try:
        server.run(
            host=args.host, 
            port=args.port, 
            stdio=args.stdio,
            direct=args.direct  # Pass the direct flag to run method
        )
    except Exception as e:
        logger.error(f"Server error: {str(e)}", exc_info=args.debug)
        return 1
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
