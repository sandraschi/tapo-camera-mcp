"""Webcam implementation using OpenCV."""

import asyncio
import contextlib
import logging
import os
from pathlib import Path
from typing import Dict, Optional

import cv2
from PIL import Image

from .base import BaseCamera, CameraFactory, CameraType

# Suppress OpenCV warnings (MSMF grab frame errors)
os.environ["OPENCV_LOG_LEVEL"] = "ERROR"
cv2.setLogLevel(0)  # 0 = silent

logger = logging.getLogger(__name__)


@CameraFactory.register(CameraType.WEBCAM)
class WebCamera(BaseCamera):
    """Webcam implementation using OpenCV."""

    def __init__(self, config, mock_webcam=None):
        super().__init__(config)
        self._cap = None
        self._device_id = int(self.config.params.get("device_id", 0))
        self._frame = None
        self._frame_lock = asyncio.Lock()
        self._mock_webcam = mock_webcam
        self._in_use_by_another_app = False
        self._in_use_error_message = None

    async def _capture_loop(self):
        """Background task to capture frames."""
        while self._is_connected:
            try:
                ret, frame = self._cap.read()
                if ret:
                    async with self._frame_lock:
                        self._frame = frame
            except Exception as e:
                logger.debug(f"Error in capture loop: {e}")
            finally:
                # Always sleep to prevent tight polling loops
                # 0.1 seconds = 10 FPS (reasonable for status monitoring)
                await asyncio.sleep(0.1)

    async def connect(self) -> bool:
        """Initialize connection to the webcam."""
        self._in_use_by_another_app = False
        self._in_use_error_message = None

        try:
            if self._mock_webcam:
                # Use mock webcam for testing
                self._cap = self._mock_webcam
                await self._cap.connect()
            else:
                # Use real webcam for production
                self._cap = cv2.VideoCapture(self._device_id)

                # Check if camera opened successfully
                if not self._cap.isOpened():
                    # Try to detect if camera is in use by another application
                    # On Windows, this often happens with Teams, Zoom, etc.
                    import platform

                    if platform.system() == "Windows":
                        # Try to read a frame to see if we get a specific error
                        try:
                            ret, frame = self._cap.read()
                            if not ret:
                                # Camera exists but can't read - likely in use
                                self._in_use_by_another_app = True
                                self._in_use_error_message = f"USB camera device {self._device_id} is in use by another application (e.g., Microsoft Teams, Zoom, Skype). Close the other application and try again."
                                logger.warning(self._in_use_error_message)
                                raise RuntimeError(self._in_use_error_message)
                        except Exception as read_error:
                            # Check error message for common patterns
                            error_str = str(read_error).lower()
                            if (
                                "access" in error_str
                                or "busy" in error_str
                                or "in use" in error_str
                            ):
                                self._in_use_by_another_app = True
                                self._in_use_error_message = f"USB camera device {self._device_id} is locked by another application. Close Microsoft Teams, Zoom, or other video apps and try again."
                                logger.warning(self._in_use_error_message)
                                raise RuntimeError(self._in_use_error_message) from read_error

                    # Generic error if we can't determine the cause
                    raise RuntimeError(
                        f"Could not open webcam device {self._device_id}. Camera may be in use by another application or not available."
                    )

                # Test if we can actually read frames (camera might be "opened" but locked)
                try:
                    ret, frame = self._cap.read()
                    if not ret:
                        self._in_use_by_another_app = True
                        self._in_use_error_message = f"USB camera device {self._device_id} is in use by another application. Close Microsoft Teams, Zoom, or other video apps."
                        logger.warning(self._in_use_error_message)
                        self._cap.release()
                        self._cap = None
                        raise RuntimeError(self._in_use_error_message)
                except RuntimeError:
                    # Re-raise our custom error
                    raise
                except Exception as test_error:
                    # Other errors during frame read test
                    error_str = str(test_error).lower()
                    if "access" in error_str or "busy" in error_str:
                        self._in_use_by_another_app = True
                        self._in_use_error_message = (
                            f"USB camera device {self._device_id} is locked by another application."
                        )
                        logger.warning(self._in_use_error_message)
                        if self._cap:
                            self._cap.release()
                            self._cap = None
                        raise RuntimeError(self._in_use_error_message) from test_error

        except RuntimeError as e:
            # Re-raise RuntimeError (our custom errors)
            self._is_connected = False
            if self._cap and not self._mock_webcam:
                self._cap.release()
                self._cap = None
            raise ConnectionError(str(e)) from e
        except Exception as e:
            self._is_connected = False
            if self._cap and not self._mock_webcam:
                self._cap.release()
                self._cap = None

            # Check if error suggests camera is in use
            error_str = str(e).lower()
            if any(
                keyword in error_str
                for keyword in ["access", "busy", "in use", "locked", "exclusive"]
            ):
                self._in_use_by_another_app = True
                self._in_use_error_message = f"USB camera device {self._device_id} appears to be in use by another application (Microsoft Teams, Zoom, etc.). Close the other application and try again."
                logger.warning(self._in_use_error_message)
                raise ConnectionError(self._in_use_error_message) from e

            raise ConnectionError(f"Failed to connect to webcam: {e}") from e
        else:
            self._is_connected = True
            if not self._mock_webcam:
                self._capture_task = asyncio.create_task(self._capture_loop())
            return True

    async def disconnect(self) -> None:
        """Close connection to the webcam."""
        self._is_connected = False
        if hasattr(self, "_capture_task"):
            self._capture_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._capture_task

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
            raise RuntimeError(f"Failed to capture image: {e}") from e

    async def get_stream_url(self) -> Optional[str]:
        """Webcams typically don't have a stream URL."""
        return None

    async def get_status(self) -> Dict:
        """Get webcam status with detailed capabilities."""
        connected = await self.is_connected()

        # Get resolution information if connected
        resolution = "Unknown"
        if connected:
            # Try to get resolution from existing capture object
            if self._cap:
                try:
                    width = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    height = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    if width > 0 and height > 0:
                        resolution = f"{width}x{height}"
                except Exception as exc:
                    logger.debug("Failed to get webcam resolution from existing cap: %s", exc)

            # If no resolution from existing cap, try to open camera briefly
            if resolution == "Unknown":
                temp_cap = None
                try:
                    temp_cap = cv2.VideoCapture(self._device_id)
                    if temp_cap.isOpened():
                        # Try to set configured resolution first
                        config_res = self.config.get("params", {}).get("resolution", "640x480")
                        try:
                            conf_width, conf_height = map(int, config_res.split("x"))
                            temp_cap.set(cv2.CAP_PROP_FRAME_WIDTH, conf_width)
                            temp_cap.set(cv2.CAP_PROP_FRAME_HEIGHT, conf_height)
                        except Exception as e:
                            logger.debug(f"Config resolution parsing failed: {e}")

                        # Get actual resolution
                        width = int(temp_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                        height = int(temp_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                        if width > 0 and height > 0:
                            resolution = f"{width}x{height}"
                except Exception as exc:
                    logger.debug("Failed to get webcam resolution: %s", exc)
                finally:
                    if temp_cap:
                        temp_cap.release()

        status = {
            "connected": connected,
            "model": f"Webcam Device {self._device_id}",
            "firmware": "N/A",
            "device_id": self._device_id,
            "streaming": await self.is_streaming(),
            "resolution": resolution,
            "ptz_capable": False,  # Most webcams don't have PTZ
            "digital_zoom_capable": True,  # Digital zoom always available
            "audio_capable": False,  # Audio not implemented for webcams
            "streaming_capable": True,  # Webcams can stream
            "capture_capable": True,  # Webcams can capture
        }

        # Add in-use detection status
        if self._in_use_by_another_app:
            status["in_use_by_another_app"] = True
            status["in_use_error"] = (
                self._in_use_error_message
                or f"USB camera device {self._device_id} is in use by another application"
            )
            status["warning"] = (
                "Camera is locked by another application (e.g., Microsoft Teams, Zoom). Close the other app to use this camera."
            )
        else:
            status["in_use_by_another_app"] = False

        return status

    async def get_info(self) -> Dict:
        """Get comprehensive webcam information."""
        try:
            info = {
                "name": self.config.name,
                "type": self.config.type.value,
                "device_id": self._device_id,
                "connected": await self.is_connected(),
                "streaming": await self.is_streaming(),
                "capabilities": {
                    "video_capture": True,
                    "image_capture": True,
                    "streaming": True,
                    "ptz": False,
                },
            }

            # Add OpenCV-specific information if connected
            if await self.is_connected() and self._cap:
                try:
                    width = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    height = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    fps = self._cap.get(cv2.CAP_PROP_FPS)

                    info.update(
                        {
                            "resolution": f"{width}x{height}",
                            "fps": fps,
                            "backend": self._cap.getBackendName(),
                        }
                    )
                except Exception as e:
                    info["resolution_info_error"] = str(e)

        except Exception as e:
            return {
                "name": self.config.name,
                "type": self.config.type.value,
                "device_id": self._device_id,
                "error": f"Failed to get camera info: {e}",
            }
        else:
            return info
