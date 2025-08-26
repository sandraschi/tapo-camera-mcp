"""Ring doorbell camera implementation."""
import asyncio
from typing import Dict, Optional
from pathlib import Path
from PIL import Image
import io
import logging

from ring_doorbell import Ring, Auth
from oauthlib.oauth2 import MissingTokenError

from .base import BaseCamera, CameraFactory, CameraType

logger = logging.getLogger(__name__)

@CameraFactory.register(CameraType.RING)
class RingCamera(BaseCamera):
    """Ring doorbell camera implementation."""
    
    def __init__(self, config):
        super().__init__(config)
        self._ring = None
        self._device = None
        self._stream_url = None
    
    async def connect(self) -> bool:
        """Initialize connection to the Ring doorbell."""
        try:
            # Initialize Ring authentication
            auth = Auth(
                self.config.params.get('token_updater', lambda x: None),
                self.config.params.get('token')
            )
            
            # Create Ring instance
            self._ring = Ring(auth)
            
            # Authenticate
            try:
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self._ring.update_data()
                )
            except MissingTokenError:
                # If no token, try to authenticate with username/password
                if not all(k in self.config.params for k in ['username', 'password']):
                    raise ValueError("Ring authentication requires either a token or username/password")
                
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self._ring.create_session(
                        self.config.params['username'],
                        self.config.params['password']
                    )
                )
            
            # Find the specific device
            device_id = self.config.params.get('device_id')
            if device_id:
                self._device = self._ring.doorbell(device_id)
            else:
                # Get first available doorbell
                devices = self._ring.doorbells
                if not devices:
                    raise ValueError("No Ring doorbells found")
                self._device = devices[0]
            
            self._is_connected = True
            return True
            
        except Exception as e:
            self._is_connected = False
            logger.error(f"Failed to connect to Ring: {e}")
            raise ConnectionError(f"Failed to connect to Ring: {e}")
    
    async def disconnect(self) -> None:
        """Close connection to the camera."""
        self._is_connected = False
        self._device = None
        self._ring = None
    
    async def capture_still(self, save_path: Optional[str] = None) -> Image.Image:
        """Capture a still image from the camera."""
        if not await self.is_connected():
            await self.connect()
        
        try:
            # Get snapshot from Ring
            snapshot = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self._device.get_snapshot()
            )
            
            if not snapshot:
                raise RuntimeError("Failed to capture snapshot from Ring")
            
            # Convert to PIL Image
            image = Image.open(io.BytesIO(snapshot))
            
            # Save if path provided
            if save_path:
                save_path = Path(save_path)
                save_path.parent.mkdir(parents=True, exist_ok=True)
                image.save(save_path)
            
            return image
            
        except Exception as e:
            self._is_connected = False
            logger.error(f"Failed to capture image from Ring: {e}")
            raise RuntimeError(f"Failed to capture image: {e}")
    
    async def get_stream_url(self) -> Optional[str]:
        """Get the stream URL for the camera."""
        if not await self.is_connected():
            await self.connect()
        
        try:
            # Get live stream URL
            stream_url = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self._device.recording_url()
            )
            
            return stream_url
            
        except Exception as e:
            logger.error(f"Failed to get stream URL from Ring: {e}")
            return None
    
    async def get_status(self) -> Dict:
        """Get camera status."""
        if not await self.is_connected():
            return {
                'connected': False,
                'error': 'Not connected to Ring'
            }
        
        try:
            # Get device health
            health = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self._device.health
            )
            
            return {
                'connected': True,
                'model': self._device.family,
                'battery_life': health.get('battery_life'),
                'firmware': health.get('firmware_version'),
                'streaming': await self.is_streaming()
            }
            
        except Exception as e:
            self._is_connected = False
            logger.error(f"Error getting Ring status: {e}")
            return {
                'connected': False,
                'error': str(e)
            }
