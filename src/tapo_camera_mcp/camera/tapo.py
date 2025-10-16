"""Tapo camera implementation."""

import asyncio
import io
from pathlib import Path
from typing import Dict, Optional

from PIL import Image
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
                self.config.params["host"],
                self.config.params["username"],
                self.config.params["password"],
            )
            # Test connection
            await asyncio.get_event_loop().run_in_executor(
                None, lambda: self._camera.getBasicInfo()
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
                None, lambda: self._camera.get_image()
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
                    None, lambda: self._camera.get_rtsp_config()
                )
                if rtsp_config.get("enabled"):
                    username = self.config.params.get("username", "admin")
                    password = self.config.params.get("password", "")
                    host = self.config.params["host"]
                    self._stream_url = f"rtsp://{username}:{password}@{host}/stream1"
            except Exception as e:
                raise RuntimeError(f"Failed to get stream URL: {e}")

        return self._stream_url

    async def get_status(self) -> Dict:
        """Get camera status with detailed capabilities."""
        if not await self.is_connected():
            await self.connect()

        try:
            basic_info = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self._camera.getBasicInfo()
            )

            device_info = basic_info.get("device_info", {})

            # Get resolution from video capabilities if available
            resolution = "Unknown"
            try:
                # Try to get video config for resolution info
                video_config = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: self._camera.getVideoConfig()
                )
                if video_config and "video_config" in video_config:
                    res_info = video_config["video_config"].get("resolution", {})
                    if res_info:
                        width = res_info.get("width", "Unknown")
                        height = res_info.get("height", "Unknown")
                        if width != "Unknown" and height != "Unknown":
                            resolution = f"{width}x{height}"
            except Exception:
                # Fallback to basic resolution detection
                pass

            # Check PTZ capability (most Tapo cameras have PTZ)
            ptz_capable = True  # Assume true for Tapo cameras, could be enhanced

            # Check audio capability
            audio_capable = False
            try:
                audio_config = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: self._camera.getAudioConfig()
                )
                if audio_config and audio_config.get("enabled", False):
                    audio_capable = True
            except Exception:
                pass

            return {
                "connected": True,
                "model": device_info.get("device_model", "Unknown"),
                "firmware": device_info.get("firmware_version", "Unknown"),
                "streaming": await self.is_streaming(),
                "resolution": resolution,
                "ptz_capable": ptz_capable,
                "audio_capable": audio_capable,
                "streaming_capable": True,  # All Tapo cameras can stream
                "capture_capable": True,  # All Tapo cameras can capture
            }
        except Exception as e:
            self._is_connected = False
            return {
                "connected": False,
                "error": str(e),
                "resolution": "N/A",
                "ptz_capable": False,
                "audio_capable": False,
                "streaming_capable": False,
                "capture_capable": False,
            }

    async def get_info(self) -> Dict:
        """Get comprehensive Tapo camera information."""
        try:
            info = {
                "name": self.config.name,
                "type": self.config.type.value,
                "host": self.config.params.get("host", ""),
                "connected": await self.is_connected(),
                "streaming": await self.is_streaming(),
                "capabilities": {
                    "video_capture": True,
                    "image_capture": True,
                    "streaming": True,
                    "ptz": True,
                },
            }

            # Add Tapo-specific information if connected
            if await self.is_connected():
                try:
                    basic_info = await asyncio.get_event_loop().run_in_executor(
                        None, lambda: self._camera.getBasicInfo()
                    )

                    device_info = basic_info.get("device_info", {})
                    info.update(
                        {
                            "model": device_info.get("device_model"),
                            "firmware_version": device_info.get("firmware_version"),
                            "serial_number": device_info.get("serial_number"),
                            "device_alias": device_info.get("device_alias"),
                            "mac_address": device_info.get("mac"),
                            "ip_address": device_info.get("ip"),
                        }
                    )
                except Exception as e:
                    info["device_info_error"] = str(e)

            return info

        except Exception as e:
            return {
                "name": self.config.name,
                "type": self.config.type.value,
                "host": self.config.params.get("host", ""),
                "error": f"Failed to get camera info: {e}",
            }
