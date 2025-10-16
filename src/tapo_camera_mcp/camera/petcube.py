"""Petcube camera implementation."""

import logging
from pathlib import Path
from typing import Dict, Optional

import aiohttp
from PIL import Image

from .base import BaseCamera, CameraFactory, CameraType

logger = logging.getLogger(__name__)


class PetcubeAPI:
    """Petcube API client."""

    BASE_URL = "https://api.petcube.com"

    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password
        self._session = None
        self._token = None
        self._device_id = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "PetcubeCameraMCP/1.0",
                }
            )
        return self._session

    async def login(self) -> str:
        """Login to Petcube API and get token."""
        session = await self._get_session()

        try:
            async with session.post(
                f"{self.BASE_URL}/auth/login",
                json={"email": self.email, "password": self.password},
            ) as response:
                data = await response.json()
                if response.status != 200:
                    raise ValueError(f"Login failed: {data.get('message', 'Unknown error')}")

                self._token = data.get("token") or data.get("access_token")
                if not self._token:
                    raise ValueError("No token received from login")

                # Update session headers with token
                session.headers.update({"Authorization": f"Bearer {self._token}"})

                return self._token

        except Exception as e:
            logger.error(f"Petcube login error: {e}")
            raise

    async def get_devices(self) -> list:
        """Get list of user's devices."""
        session = await self._get_session()

        try:
            async with session.get(f"{self.BASE_URL}/devices") as response:
                if response.status != 200:
                    raise ValueError(f"Failed to get devices: HTTP {response.status}")

                devices = await response.json()
                return devices.get("devices", devices) if isinstance(devices, dict) else devices

        except Exception as e:
            logger.error(f"Error getting devices: {e}")
            raise

    async def get_device_status(self, device_id: str) -> dict:
        """Get device status and capabilities."""
        session = await self._get_session()

        try:
            async with session.get(f"{self.BASE_URL}/devices/{device_id}") as response:
                if response.status != 200:
                    raise ValueError(f"Failed to get device status: HTTP {response.status}")

                return await response.json()

        except Exception as e:
            logger.error(f"Error getting device status: {e}")
            raise

    async def get_stream_url(self, device_id: str) -> str:
        """Get video stream URL for device."""
        session = await self._get_session()

        try:
            async with session.get(f"{self.BASE_URL}/devices/{device_id}/stream") as response:
                if response.status != 200:
                    raise ValueError(f"Failed to get stream URL: HTTP {response.status}")

                data = await response.json()
                return data.get("stream_url") or data.get("url")

        except Exception as e:
            logger.error(f"Error getting stream URL: {e}")
            raise

    async def dispense_treat(self, device_id: str, amount: int = 1) -> dict:
        """Dispense treats from device."""
        session = await self._get_session()

        try:
            async with session.post(
                f"{self.BASE_URL}/devices/{device_id}/treat", json={"amount": amount}
            ) as response:
                if response.status not in [200, 201]:
                    raise ValueError(f"Failed to dispense treat: HTTP {response.status}")

                return await response.json()

        except Exception as e:
            logger.error(f"Error dispensing treat: {e}")
            raise

    async def close(self):
        """Close the API session."""
        if self._session and not self._session.closed:
            await self._session.close()


@CameraFactory.register(CameraType.PETCUBE)
class PetcubeCamera(BaseCamera):
    """Petcube camera implementation."""

    def __init__(self, config):
        super().__init__(config)
        self.api = PetcubeAPI(config.params.get("email", ""), config.params.get("password", ""))
        self.device_id = config.params.get("device_id")
        self._stream_url = None

    async def connect(self) -> bool:
        """Initialize connection to the Petcube camera."""
        try:
            # Login to API
            await self.api.login()

            # Get device information if not specified
            if not self.device_id:
                devices = await self.api.get_devices()
                if devices:
                    # Use first device or try to match by name
                    self.device_id = devices[0].get("id") or devices[0].get("device_id")
                    logger.info(f"Auto-selected Petcube device: {self.device_id}")
                else:
                    raise ValueError("No Petcube devices found for this account")

            # Verify device access
            device_info = await self.api.get_device_status(self.device_id)

            self._is_connected = True
            logger.info(f"Connected to Petcube device: {self.device_id}")
            return True

        except Exception as e:
            self._is_connected = False
            logger.error(f"Failed to connect to Petcube camera: {e}")
            raise ConnectionError(f"Failed to connect to Petcube camera: {e}")

    async def disconnect(self) -> None:
        """Close connection to the camera."""
        await self.api.close()
        self._is_connected = False
        self._stream_url = None

    async def capture_still(self, save_path: Optional[str] = None) -> Image.Image:
        """Capture a still image from the camera."""
        if not await self.is_connected():
            await self.connect()

        try:
            # Get stream URL and capture frame
            if not self._stream_url:
                self._stream_url = await self.api.get_stream_url(self.device_id)

            # For now, return a placeholder - would need actual stream processing
            # In a full implementation, this would:
            # 1. Connect to RTSP/HLS stream
            # 2. Capture a single frame
            # 3. Return as PIL Image

            # Placeholder implementation - create a simple image
            # TODO: Implement actual stream capture
            img = Image.new("RGB", (640, 480), color="gray")
            # Add timestamp or camera info
            from PIL import ImageDraw

            draw = ImageDraw.Draw(img)
            draw.text((10, 10), f"Petcube {self.device_id}", fill="white")
            draw.text(
                (10, 30),
                f"Status: {'Online' if self._is_connected else 'Offline'}",
                fill="white",
            )

            # Save if path provided
            if save_path:
                save_path = Path(save_path)
                save_path.parent.mkdir(parents=True, exist_ok=True)
                img.save(save_path)

            return img

        except Exception as e:
            self._is_connected = False
            raise RuntimeError(f"Failed to capture image: {e}")

    async def get_stream_url(self) -> Optional[str]:
        """Get the video stream URL."""
        if not await self.is_connected():
            await self.connect()

        try:
            self._stream_url = await self.api.get_stream_url(self.device_id)
            return self._stream_url
        except Exception as e:
            logger.error(f"Failed to get stream URL: {e}")
            return None

    async def get_status(self) -> Dict:
        """Get camera status with detailed capabilities."""
        if not await self.is_connected():
            await self.connect()

        try:
            device_info = await self.api.get_device_status(self.device_id)

            return {
                "connected": True,
                "model": device_info.get("model", "Petcube Camera"),
                "firmware": device_info.get("firmware_version", "Unknown"),
                "streaming": bool(self._stream_url),
                "resolution": device_info.get("video_resolution", "1080p"),
                "ptz_capable": False,  # Petcube cameras typically don't have PTZ
                "audio_capable": device_info.get("audio_enabled", True),
                "streaming_capable": True,
                "capture_capable": True,
                "treat_dispenser": device_info.get("treat_compartments", 0),
                "battery_level": device_info.get("battery_level"),
                "online": device_info.get("online", True),
            }

        except Exception as e:
            self._is_connected = False
            return {
                "connected": False,
                "error": str(e),
                "resolution": "Unknown",
                "ptz_capable": False,
                "audio_capable": False,
                "streaming_capable": False,
                "capture_capable": False,
            }

    async def dispense_treat(self, amount: int = 1) -> dict:
        """Dispense treats from the camera."""
        if not await self.is_connected():
            await self.connect()

        try:
            result = await self.api.dispense_treat(self.device_id, amount)
            return {
                "success": True,
                "message": f"Dispensed {amount} treat(s)",
                "details": result,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_info(self) -> Dict:
        """Get comprehensive Petcube camera information."""
        try:
            info = {
                "name": self.config.name,
                "type": self.config.type.value,
                "device_id": self.device_id,
                "connected": await self.is_connected(),
                "streaming": await self.is_streaming(),
                "capabilities": {
                    "video_capture": True,
                    "image_capture": True,
                    "streaming": True,
                    "audio": True,
                    "treat_dispenser": True,
                    "motion_detection": True,
                },
            }

            if await self.is_connected():
                device_info = await self.api.get_device_status(self.device_id)
                info.update(
                    {
                        "model": device_info.get("model"),
                        "firmware": device_info.get("firmware_version"),
                        "battery_level": device_info.get("battery_level"),
                        "treat_compartments": device_info.get("treat_compartments"),
                        "last_seen": device_info.get("last_seen"),
                    }
                )

            return info

        except Exception as e:
            logger.error(f"Error getting Petcube info: {e}")
            return {
                "name": self.config.name,
                "type": self.config.type.value,
                "error": str(e),
            }
