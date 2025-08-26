"""Furbo dog camera implementation."""
import asyncio
import aiohttp
import json
import logging
from typing import Dict, Optional
from pathlib import Path
from PIL import Image
import io

from .base import BaseCamera, CameraFactory, CameraType

logger = logging.getLogger(__name__)

class FurboAPI:
    """Furbo API client."""
    
    BASE_URL = "https://api.furbo.jp/1.0"
    
    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password
        self._session = None
        self._token = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
    
    async def login(self) -> str:
        """Login to Furbo API and get token."""
        session = await self._get_session()
        
        try:
            async with session.post(
                f"{self.BASE_URL}/auth/login",
                json={
                    "email": self.email,
                    "password": self.password,
                    "type": "email"
                }
            ) as response:
                data = await response.json()
                if response.status != 200:
                    raise ValueError(f"Login failed: {data.get('message', 'Unknown error')}")
                
                self._token = data.get('token')
                if not self._token:
                    raise ValueError("No token received from Furbo API")
                
                return self._token
                
        except Exception as e:
            logger.error(f"Furbo login error: {e}")
            raise
    
    async def get_devices(self) -> list:
        """Get list of Furbo devices."""
        if not self._token:
            await self.login()
            
        session = await self._get_session()
        
        try:
            async with session.get(
                f"{self.BASE_URL}/devices",
                headers={"Authorization": f"Bearer {self._token}"}
            ) as response:
                data = await response.json()
                if response.status != 200:
                    raise ValueError(f"Failed to get devices: {data.get('message', 'Unknown error')}")
                
                return data.get('devices', [])
                
        except Exception as e:
            logger.error(f"Error getting Furbo devices: {e}")
            raise
    
    async def get_snapshot(self, device_id: str) -> bytes:
        """Get snapshot from Furbo camera."""
        if not self._token:
            await self.login()
            
        session = await self._get_session()
        
        try:
            async with session.get(
                f"{self.BASE_URL}/devices/{device_id}/snapshot",
                headers={"Authorization": f"Bearer {self._token}"}
            ) as response:
                if response.status != 200:
                    error = await response.text()
                    raise ValueError(f"Failed to get snapshot: {error}")
                
                return await response.read()
                
        except Exception as e:
            logger.error(f"Error getting Furbo snapshot: {e}")
            raise
    
    async def close(self):
        """Close the session."""
        if self._session and not self._session.closed:
            await self._session.close()

@CameraFactory.register(CameraType.FURBO)
class FurboCamera(BaseCamera):
    """Furbo dog camera implementation."""
    
    def __init__(self, config):
        super().__init__(config)
        self._api = None
        self._device_id = None
        self._device_info = None
    
    async def connect(self) -> bool:
        """Initialize connection to the Furbo camera."""
        try:
            # Initialize API client
            self._api = FurboAPI(
                email=self.config.params['email'],
                password=self.config.params['password']
            )
            
            # Login and get devices
            devices = await self._api.get_devices()
            if not devices:
                raise ValueError("No Furbo devices found")
            
            # Find the specified device or use the first one
            device_id = self.config.params.get('device_id')
            if device_id:
                self._device_info = next(
                    (d for d in devices if d.get('id') == device_id),
                    None
                )
                if not self._device_info:
                    raise ValueError(f"Device {device_id} not found")
            else:
                self._device_info = devices[0]
            
            self._device_id = self._device_info['id']
            self._is_connected = True
            return True
            
        except Exception as e:
            self._is_connected = False
            logger.error(f"Failed to connect to Furbo: {e}")
            raise ConnectionError(f"Failed to connect to Furbo: {e}")
    
    async def disconnect(self) -> None:
        """Close connection to the camera."""
        self._is_connected = False
        if self._api:
            await self._api.close()
            self._api = None
        self._device_id = None
        self._device_info = None
    
    async def capture_still(self, save_path: Optional[str] = None) -> Image.Image:
        """Capture a still image from the camera.
        
        Args:
            save_path: Optional path to save the image to
            
        Returns:
            PIL.Image.Image: The captured image
            
        Raises:
            RuntimeError: If the camera is not connected or capture fails
        """
        if not await self.is_connected():
            await self.connect()
            
        if not self._device_id:
            raise RuntimeError("No device ID available for Furbo camera")
            
        try:
            # Get real snapshot from Furbo API
            img_data = await self._api.get_snapshot(self._device_id)
            if not img_data:
                raise RuntimeError("Received empty image data from Furbo camera")
                
            image = Image.open(io.BytesIO(img_data))
            
            # Save if path provided
            if save_path:
                save_path = Path(save_path)
                save_path.parent.mkdir(parents=True, exist_ok=True)
                image.save(save_path)
                
            return image
            
        except Exception as e:
            self._is_connected = False
            logger.error(f"Failed to capture image from Furbo: {e}", exc_info=True)
            raise RuntimeError(f"Failed to capture image: {e}")
    
    async def get_stream_url(self) -> Optional[str]:
        """Get the RTSP stream URL for the camera.
        
        Note: This uses the undocumented RTSP service on Furbo cameras.
        The stream requires authentication and may not work on all Furbo models.
        
        Returns:
            Optional[str]: RTSP URL if available, None otherwise
        """
        if not await self.is_connected():
            await self.connect()
            
        if not self._device_id:
            return None
            
        try:
            # Build RTSP URL with authentication
            host = self.config.params.get('host')
            username = self.config.params.get('username')
            password = self.config.params.get('password')
            
            if not all([host, username, password]):
                logger.warning("Missing required credentials for RTSP stream")
                return None
                
            # Standard RTSP port for Furbo
            rtsp_url = f"rtsp://{username}:{password}@{host}:554/stream1"
            
            # Test the connection
            # Note: This is a basic check - actual streaming would need proper RTSP client
            return rtsp_url
            
        except Exception as e:
            logger.warning(f"Failed to get RTSP stream URL: {e}")
            return None
    
    async def get_status(self) -> Dict:
        """Get camera status."""
        if not await self.is_connected():
            return {
                'connected': False,
                'error': 'Not connected to Furbo'
            }
        
        try:
            return {
                'connected': True,
                'model': self._device_info.get('model', 'Unknown'),
                'name': self._device_info.get('name', 'Unknown'),
                'battery_level': self._device_info.get('battery_level'),
                'firmware': self._device_info.get('firmware_version'),
                'streaming': await self.is_streaming()
            }
            
        except Exception as e:
            self._is_connected = False
            logger.error(f"Error getting Furbo status: {e}")
            return {
                'connected': False,
                'error': str(e)
            }
