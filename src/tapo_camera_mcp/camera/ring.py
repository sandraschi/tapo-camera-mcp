"""Ring doorbell camera implementation."""

import asyncio
import io
import logging
from pathlib import Path
from typing import Dict, Optional

from oauthlib.oauth2 import MissingTokenError
from PIL import Image
from ring_doorbell import Auth, Ring

from .base import BaseCamera, CameraFactory, CameraType

logger = logging.getLogger(__name__)


@CameraFactory.register(CameraType.RING)
class RingCamera(BaseCamera):
    """Ring doorbell camera implementation."""

    def __init__(self, config, mock_ring=None):
        super().__init__(config)
        self._mock_ring = mock_ring
        self._ring = None
        self._device = None
        self._stream_url = None

    async def connect(self) -> bool:
        """Initialize connection to the Ring doorbell."""
        try:
            if self._mock_ring:
                # Use mock camera for testing
                await self._mock_ring.connect()
            else:
                # Use real camera for production
                # Initialize Ring authentication
                auth = Auth(
                    self.config.params.get("token_updater", lambda _x: None),
                    self.config.params.get("token"),
                )

                # Create Ring instance
                self._ring = Ring(auth)

                # Authenticate
                try:
                    await asyncio.get_event_loop().run_in_executor(
                        None, lambda: self._ring.update_data()
                    )
                except MissingTokenError:
                    # If no token, try to authenticate with username/password
                    if not all(k in self.config.params for k in ["username", "password"]):
                        raise ValueError(
                            "Ring authentication requires either a token or username/password"
                        ) from None

                    await asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: self._ring.create_session(
                            self.config.params["username"], self.config.params["password"]
                        ),
                    )

                # Find the specific device
                device_id = self.config.params.get("device_id")
                if device_id:
                    self._device = self._ring.doorbell(device_id)
                else:
                    # Get first available doorbell
                    devices = self._ring.doorbells
                    if not devices:
                        raise ValueError("No Ring doorbells found")
                    self._device = devices[0]

        except Exception as e:
            self._is_connected = False
            logger.exception("Failed to connect to Ring")
            raise ConnectionError(f"Failed to connect to Ring: {e}") from e
        else:
            self._is_connected = True
            return True

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
                None, lambda: self._device.get_snapshot()
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

        except Exception as e:
            self._is_connected = False
            logger.exception("Failed to capture image from Ring")
            raise RuntimeError(f"Failed to capture image: {e}") from e
        else:
            return image

    async def get_stream_url(self) -> Optional[str]:
        """Get the stream URL for the camera.

        Ring doorbells use WebRTC for live streaming, not HTTP URLs.
        This method returns None to indicate WebRTC should be used instead.
        """
        if not await self.is_connected():
            await self.connect()

        # Ring doorbells require WebRTC for live streaming
        # The stream viewer should detect this and use WebRTC endpoints
        logger.info("Ring doorbell live streaming requires WebRTC - no HTTP URL available")
        return None

    async def get_status(self) -> Dict:
        """Get camera status."""
        if not await self.is_connected():
            return {"connected": False, "error": "Not connected to Ring"}

        try:
            # Get device health
            health = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self._device.health
            )

            return {
                "connected": True,
                "model": self._device.family,
                "battery_life": health.get("battery_life"),
                "firmware": health.get("firmware_version"),
                "streaming": await self.is_streaming(),
            }

        except Exception as e:
            self._is_connected = False
            logger.exception("Error getting Ring status")
            return {"connected": False, "error": str(e)}

    async def get_info(self) -> Dict:
        """Get comprehensive Ring camera information."""
        try:
            info = {
                "name": self.config.name,
                "type": self.config.type.value,
                "connected": await self.is_connected(),
                "streaming": await self.is_streaming(),
                "capabilities": {
                    "video_capture": True,
                    "image_capture": True,
                    "streaming": True,
                    "ptz": False,
                },
            }

            # Add Ring-specific information if connected
            if await self.is_connected():
                try:
                    health = await asyncio.get_event_loop().run_in_executor(
                        None, lambda: self._device.health
                    )

                    info.update(
                        {
                            "model": self._device.family,
                            "name": self._device.name,
                            "battery_life": health.get("battery_life"),
                            "firmware_version": health.get("firmware_version"),
                            "wifi_signal": health.get("wifi_signal_category"),
                            "device_id": self._device.id,
                        }
                    )
                except Exception as e:
                    info["device_info_error"] = str(e)

        except Exception as e:
            return {
                "name": self.config.name,
                "type": self.config.type.value,
                "error": f"Failed to get camera info: {e}",
            }
        else:
            return info
