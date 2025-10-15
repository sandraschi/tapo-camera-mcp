"""Webcam implementation using OpenCV."""
import asyncio
import cv2
import numpy as np
from pathlib import Path
from typing import Dict, Optional
from PIL import Image

from .base import BaseCamera, CameraFactory, CameraType

@CameraFactory.register(CameraType.WEBCAM)
class WebCamera(BaseCamera):
    """Webcam implementation using OpenCV."""
    
    def __init__(self, config):
        super().__init__(config)
        self._cap = None
        self._device_id = int(self.config.params.get('device_id', 0))
        self._frame = None
        self._frame_lock = asyncio.Lock()
    
    async def _capture_loop(self):
        """Background task to capture frames."""
        while self._is_connected:
            ret, frame = self._cap.read()
            if ret:
                async with self._frame_lock:
                    self._frame = frame
            await asyncio.sleep(0.03)  # ~30 FPS
    
    async def connect(self) -> bool:
        """Initialize connection to the webcam."""
        try:
            self._cap = cv2.VideoCapture(self._device_id)
            if not self._cap.isOpened():
                raise RuntimeError(f"Could not open webcam device {self._device_id}")
            
            self._is_connected = True
            self._capture_task = asyncio.create_task(self._capture_loop())
            return True
            
        except Exception as e:
            self._is_connected = False
            if self._cap:
                self._cap.release()
                self._cap = None
            raise ConnectionError(f"Failed to connect to webcam: {e}")
    
    async def disconnect(self) -> None:
        """Close connection to the webcam."""
        self._is_connected = False
        if hasattr(self, '_capture_task'):
            self._capture_task.cancel()
            try:
                await self._capture_task
            except asyncio.CancelledError:
                pass
        
        if self._cap:
            self._cap.release()
            self._cap = None
    
    async def capture_still(self, save_path: Optional[str] = None) -> Image.Image:
        """Capture a still image from the webcam."""
        if not await self.is_connected():
            await self.connect()
        
        try:
            async with self._frame_lock:
                if self._frame is None:
                    raise RuntimeError("No frame available from webcam")
                
                # Convert BGR to RGB
                frame_rgb = cv2.cvtColor(self._frame, cv2.COLOR_BGR2RGB)
                image = Image.fromarray(frame_rgb)
                
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
        """Webcams typically don't have a stream URL."""
        return None
    
    async def get_status(self) -> Dict:
        """Get webcam status with detailed capabilities."""
        connected = await self.is_connected()

        # Get resolution information if connected
        resolution = 'Unknown'
        if connected and self._cap:
            try:
                width = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                if width > 0 and height > 0:
                    resolution = f"{width}x{height}"
            except Exception:
                pass

        return {
            'connected': connected,
            'model': f"Webcam Device {self._device_id}",
            'firmware': 'N/A',
            'device_id': self._device_id,
            'streaming': await self.is_streaming(),
            'resolution': resolution,
            'ptz_capable': False,  # Most webcams don't have PTZ
            'audio_capable': False,  # Audio not implemented for webcams
            'streaming_capable': True,  # Webcams can stream
            'capture_capable': True     # Webcams can capture
        }
    
    async def get_info(self) -> Dict:
        """Get comprehensive webcam information."""
        try:
            info = {
                'name': self.config.name,
                'type': self.config.type.value,
                'device_id': self._device_id,
                'connected': await self.is_connected(),
                'streaming': await self.is_streaming(),
                'capabilities': {
                    'video_capture': True,
                    'image_capture': True,
                    'streaming': True,
                    'ptz': False
                }
            }
            
            # Add OpenCV-specific information if connected
            if await self.is_connected() and self._cap:
                try:
                    width = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    height = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    fps = self._cap.get(cv2.CAP_PROP_FPS)
                    
                    info.update({
                        'resolution': f"{width}x{height}",
                        'fps': fps,
                        'backend': self._cap.getBackendName()
                    })
                except Exception as e:
                    info['resolution_info_error'] = str(e)
            
            return info
            
        except Exception as e:
            return {
                'name': self.config.name,
                'type': self.config.type.value,
                'device_id': self._device_id,
                'error': f"Failed to get camera info: {e}"
            }