"""Tapo camera implementation."""
import asyncio
from typing import Dict, Optional
from pathlib import Path
from PIL import Image
import io

from pytapo import Tapo
from .base import BaseCamera, CameraFactory, CameraType

@CameraFactory.register(CameraType.TAPO)
class TapoCamera(BaseCamera):
    """Tapo camera implementation."""
    
    def __init__(self, config):
        super().__init__(config)
        self._camera = None
        self._stream_url = None
    
    async def connect(self) -> bool:
        """Initialize connection to the Tapo camera."""
        try:
            self._camera = Tapo(
                self.config.params['host'],
                self.config.params['username'],
                self.config.params['password']
            )
            # Test connection
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self._camera.getBasicInfo()
            )
            self._is_connected = True
            return True
        except Exception as e:
            self._is_connected = False
            raise ConnectionError(f"Failed to connect to Tapo camera: {e}")
    
    async def disconnect(self) -> None:
        """Close connection to the camera."""
        self._is_connected = False
        self._camera = None
    
    async def capture_still(self, save_path: Optional[str] = None) -> Image.Image:
        """Capture a still image from the camera."""
        if not await self.is_connected():
            await self.connect()
        
        try:
            # Capture image
            img_data = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self._camera.get_image()
            )
            
            # Convert to PIL Image
            image = Image.open(io.BytesIO(img_data))
            
            # Save if path provided
            if save_path:
                save_path = Path(save_path)
                save_path.parent.mkdir(parents=True, exist_ok=True)
                image.save(save_path)
                
            return image
            
        except Exception as e:
            self._is_connected = False
            raise RuntimeError(f"Failed to capture image: {e}")
    
    async def get_stream_url(self) -> Optional[str]:
        """Get the RTSP stream URL for the camera."""
        if not await self.is_connected():
            await self.connect()
            
        if not self._stream_url:
            try:
                rtsp_config = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self._camera.get_rtsp_config()
                )
                if rtsp_config.get('enabled'):
                    username = self.config.params.get('username', 'admin')
                    password = self.config.params.get('password', '')
                    host = self.config.params['host']
                    self._stream_url = f"rtsp://{username}:{password}@{host}/stream1"
            except Exception as e:
                raise RuntimeError(f"Failed to get stream URL: {e}")
                
        return self._stream_url
    
    async def get_status(self) -> Dict:
        """Get camera status."""
        if not await self.is_connected():
            await self.connect()
            
        try:
            basic_info = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self._camera.getBasicInfo()
            )
            
            return {
                'connected': True,
                'model': basic_info.get('device_info', {}).get('device_model'),
                'firmware': basic_info.get('device_info', {}).get('firmware_version'),
                'streaming': await self.is_streaming()
            }
        except Exception as e:
            self._is_connected = False
            return {
                'connected': False,
                'error': str(e)
            }
