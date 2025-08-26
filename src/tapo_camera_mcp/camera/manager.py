"""Camera manager for handling multiple camera types and groups."""
import asyncio
from typing import Dict, List, Optional, Union, Set, Any
from pathlib import Path
import logging

from .base import CameraFactory, CameraConfig, CameraType
from .groups import CameraGroupManager

logger = logging.getLogger(__name__)

class CameraManager:
    """Manages multiple camera instances and groups."""
    
    def __init__(self):
        self.cameras: Dict[str, Any] = {}
        self._initialized = False
        self.groups = CameraGroupManager()
    
    async def initialize(self, configs: List[dict] = None) -> None:
        """Initialize camera manager with configuration.
        
        Args:
            configs: List of camera configurations
        """
        if self._initialized:
            return
            
        if configs:
            for cfg in configs:
                await self.add_camera(cfg)
        
        self._initialized = True
    
    async def add_camera(self, config: Union[dict, CameraConfig]) -> bool:
        """Add a new camera.
        
        Args:
            config: Camera configuration
            
        Returns:
            bool: True if camera was added successfully
        """
        try:
            if isinstance(config, dict):
                config = CameraConfig(**config)
                
            if config.name in self.cameras:
                logger.warning(f"Camera '{config.name}' already exists")
                return False
                
            # Create and connect to camera
            camera = CameraFactory.create(config)
            connected = await camera.connect()
            
            if connected:
                self.cameras[config.name] = camera
                logger.info(f"Added camera: {config.name} ({config.type})")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to add camera {config.name}: {e}")
            return False
    
    async def remove_camera(self, name: str) -> bool:
        """Remove a camera.
        
        Args:
            name: Name of the camera to remove
            
        Returns:
            bool: True if camera was removed successfully
        """
        if name not in self.cameras:
            return False
            
        try:
            # Remove from all groups first
            self.groups.remove_camera(name)
            
            # Disconnect and remove camera
            await self.cameras[name].disconnect()
            del self.cameras[name]
            logger.info(f"Removed camera: {name}")
            return True
        except Exception as e:
            logger.error(f"Error removing camera {name}: {e}")
            return False
    
    async def get_camera(self, name: str):
        """Get a camera instance by name."""
        return self.cameras.get(name)
    
    async def list_cameras(self, group: Optional[str] = None) -> List[dict]:
        """List all cameras and their status, optionally filtered by group.
        
        Args:
            group: Optional group name to filter cameras
            
        Returns:
            List of camera information dictionaries
        """
        result = []
        camera_names = self.groups.get_group_cameras(group) if group else self.cameras.keys()
        
        for name in camera_names:
            if name not in self.cameras:
                continue
                
            camera = self.cameras[name]
            try:
                status = await camera.get_status()
                result.append({
                    'name': name,
                    'type': camera.config.type.value,
                    'status': status,
                    'groups': self.groups.get_camera_groups(name)
                })
            except Exception as e:
                logger.error(f"Error getting status for {name}: {e}")
                result.append({
                    'name': name,
                    'error': str(e),
                    'groups': self.groups.get_camera_groups(name)
                })
        return result
    
    async def capture_still(
        self, 
        camera_name: str, 
        save_path: Optional[Union[str, Path]] = None
    ) -> dict:
        """Capture a still image from a camera."""
        if camera_name not in self.cameras:
            return {
                'status': 'error',
                'message': f'Camera not found: {camera_name}'
            }
            
        try:
            image = await self.cameras[camera_name].capture_still(save_path)
            return {
                'status': 'success',
                'camera': camera_name,
                'image': image if not save_path else str(save_path)
            }
        except Exception as e:
            return {
                'status': 'error',
                'camera': camera_name,
                'message': str(e)
            }
    
    # Group management methods
    async def add_camera_to_group(self, camera_name: str, group_name: str) -> bool:
        """Add a camera to a group.
        
        Args:
            camera_name: Name of the camera
            group_name: Name of the group
            
        Returns:
            bool: True if camera was added to group
        """
        if camera_name not in self.cameras:
            logger.warning(f"Camera {camera_name} not found")
            return False
            
        return self.groups.add_camera_to_group(camera_name, group_name)
    
    async def remove_camera_from_group(self, camera_name: str, group_name: str) -> bool:
        """Remove a camera from a group.
        
        Args:
            camera_name: Name of the camera
            group_name: Name of the group
            
        Returns:
            bool: True if camera was removed from group
        """
        return self.groups.remove_camera_from_group(camera_name, group_name)
    
    async def create_group(self, group_name: str) -> bool:
        """Create a new camera group.
        
        Args:
            group_name: Name of the group to create
            
        Returns:
            bool: True if group was created
        """
        return self.groups.create_group(group_name)
    
    async def delete_group(self, group_name: str) -> bool:
        """Delete a camera group.
        
        Args:
            group_name: Name of the group to delete
            
        Returns:
            bool: True if group was deleted
        """
        return self.groups.delete_group(group_name)
    
    async def list_groups(self) -> List[Dict[str, Any]]:
        """List all camera groups with their cameras.
        
        Returns:
            List of group information dictionaries
        """
        groups = []
        for group_name in self.groups.list_groups():
            cameras = self.groups.get_group_cameras(group_name)
            groups.append({
                'name': group_name,
                'cameras': cameras,
                'camera_count': len(cameras)
            })
        return groups
    
    async def close(self):
        """Close all camera connections and clean up."""
        for name in list(self.cameras.keys()):
            await self.remove_camera(name)
        self._initialized = False

# Global instance
camera_manager = CameraManager()
