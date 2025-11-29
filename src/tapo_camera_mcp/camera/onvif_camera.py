"""ONVIF camera implementation for Tapo and other ONVIF-compatible cameras."""

import asyncio
import io
import logging
from pathlib import Path
from typing import Dict, Optional
from urllib.parse import urlparse

import requests
from PIL import Image

from .base import BaseCamera, CameraFactory, CameraType

logger = logging.getLogger(__name__)


class ONVIFCameraWrapper:
    """Wrapper for python-onvif-zeep camera interface."""

    def __init__(self, host: str, port: int, username: str, password: str):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self._camera = None
        self._ptz = None
        self._media = None
        self._profiles = None

    def connect(self) -> bool:
        """Connect to ONVIF camera."""
        try:
            from onvif import ONVIFCamera

            self._camera = ONVIFCamera(
                self.host, self.port, self.username, self.password
            )
            return True
        except Exception as e:
            logger.exception("Failed to connect to ONVIF camera at %s:%s", self.host, self.port)
            raise ConnectionError(f"ONVIF connection failed: {e}") from e

    def get_device_info(self) -> Dict:
        """Get device information."""
        if not self._camera:
            raise RuntimeError("Camera not connected")
        info = self._camera.devicemgmt.GetDeviceInformation()
        return {
            "manufacturer": info.Manufacturer,
            "model": info.Model,
            "firmware_version": info.FirmwareVersion,
            "serial_number": info.SerialNumber,
            "hardware_id": info.HardwareId,
        }

    def get_media_profiles(self) -> list:
        """Get available media profiles."""
        if not self._camera:
            raise RuntimeError("Camera not connected")
        if not self._media:
            self._media = self._camera.create_media_service()
        if not self._profiles:
            self._profiles = self._media.GetProfiles()
        return self._profiles

    def get_stream_uri(self, profile_token: Optional[str] = None) -> str:
        """Get RTSP stream URI for a profile."""
        if not self._camera:
            raise RuntimeError("Camera not connected")
        if not self._media:
            self._media = self._camera.create_media_service()

        profiles = self.get_media_profiles()
        if not profiles:
            raise RuntimeError("No media profiles available")

        # Use specified profile or first one (mainStream)
        if profile_token:
            profile = next((p for p in profiles if p.token == profile_token), profiles[0])
        else:
            profile = profiles[0]

        # Create proper request object for GetStreamUri
        req = self._media.create_type("GetStreamUri")
        req.ProfileToken = profile.token
        req.StreamSetup = {
            "Stream": "RTP-Unicast",
            "Transport": {"Protocol": "RTSP"},
        }
        uri_response = self._media.GetStreamUri(req)
        return uri_response.Uri

    def get_snapshot_uri(self, profile_token: Optional[str] = None) -> str:
        """Get snapshot URI for a profile."""
        if not self._camera:
            raise RuntimeError("Camera not connected")
        if not self._media:
            self._media = self._camera.create_media_service()

        profiles = self.get_media_profiles()
        if not profiles:
            raise RuntimeError("No media profiles available")

        # Use jpegStream profile if available, otherwise first profile
        if profile_token:
            profile = next((p for p in profiles if p.token == profile_token), profiles[0])
        else:
            # Try to find jpegStream profile
            jpeg_profile = next((p for p in profiles if "jpeg" in p.Name.lower()), None)
            profile = jpeg_profile or profiles[0]

        # Create proper request for GetSnapshotUri
        req = self._media.create_type("GetSnapshotUri")
        req.ProfileToken = profile.token
        uri_response = self._media.GetSnapshotUri(req)
        return uri_response.Uri

    def get_ptz_service(self):
        """Get PTZ service."""
        if not self._camera:
            raise RuntimeError("Camera not connected")
        if not self._ptz:
            self._ptz = self._camera.create_ptz_service()
        return self._ptz

    def continuous_move(self, pan: float = 0, tilt: float = 0, zoom: float = 0):
        """Start continuous PTZ movement."""
        ptz = self.get_ptz_service()
        profiles = self.get_media_profiles()
        if not profiles:
            raise RuntimeError("No media profiles for PTZ")

        request = ptz.create_type("ContinuousMove")
        request.ProfileToken = profiles[0].token
        request.Velocity = {"PanTilt": {"x": pan, "y": tilt}, "Zoom": {"x": zoom}}
        ptz.ContinuousMove(request)

    def stop_move(self):
        """Stop PTZ movement."""
        ptz = self.get_ptz_service()
        profiles = self.get_media_profiles()
        if not profiles:
            return

        request = ptz.create_type("Stop")
        request.ProfileToken = profiles[0].token
        request.PanTilt = True
        request.Zoom = True
        ptz.Stop(request)

    def go_to_preset(self, preset_token: str):
        """Go to a PTZ preset."""
        ptz = self.get_ptz_service()
        profiles = self.get_media_profiles()
        if not profiles:
            raise RuntimeError("No media profiles for PTZ")

        request = ptz.create_type("GotoPreset")
        request.ProfileToken = profiles[0].token
        request.PresetToken = preset_token
        ptz.GotoPreset(request)

    def get_presets(self) -> list:
        """Get PTZ presets."""
        ptz = self.get_ptz_service()
        profiles = self.get_media_profiles()
        if not profiles:
            return []

        presets = ptz.GetPresets(profiles[0].token)
        return [{"token": p.token, "name": p.Name} for p in presets]


@CameraFactory.register(CameraType.ONVIF)
class ONVIFBasedCamera(BaseCamera):
    """ONVIF-based camera implementation."""

    def __init__(self, config, mock_camera=None):
        super().__init__(config)
        self._camera: Optional[ONVIFCameraWrapper] = None
        self._mock_camera = mock_camera
        self._stream_url: Optional[str] = None
        self._snapshot_url: Optional[str] = None

    async def connect(self) -> bool:
        """Initialize connection to the ONVIF camera."""
        try:
            if self._mock_camera:
                self._camera = self._mock_camera
            else:
                host = self.config.params["host"]
                port = self.config.params.get("onvif_port", 2020)
                username = self.config.params["username"]
                password = self.config.params["password"]

                self._camera = ONVIFCameraWrapper(host, port, username, password)

                # Connect in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self._camera.connect)

            self._is_connected = True
            host = self.config.params.get("host", "unknown")
            logger.info("Successfully connected to ONVIF camera at %s", host)
            return True

        except Exception as e:
            self._is_connected = False
            host = self.config.params.get("host", "unknown")
            error_msg = str(e)
            logger.exception("Failed to connect to ONVIF camera at %s", host)
            raise ConnectionError(
                f"Failed to connect to ONVIF camera {host}: {error_msg}"
            ) from e

    async def disconnect(self) -> None:
        """Close connection to the camera."""
        self._is_connected = False
        self._camera = None
        self._stream_url = None
        self._snapshot_url = None

    async def capture_still(self, save_path: Optional[str] = None) -> Image.Image:
        """Capture a still image from the camera via RTSP stream.
        
        Note: Tapo cameras don't support ONVIF GetSnapshotUri, so we grab
        a frame from the RTSP stream using OpenCV.
        """
        if not await self.is_connected():
            await self.connect()

        try:
            import cv2
            
            loop = asyncio.get_event_loop()

            # Get RTSP stream URL
            stream_url = await self.get_stream_url()
            if not stream_url:
                raise RuntimeError("Could not get stream URL")

            # Add auth credentials to RTSP URL
            username = self.config.params["username"]
            password = self.config.params["password"]
            # Parse and rebuild URL with auth
            parsed = urlparse(stream_url)
            auth_url = f"rtsp://{username}:{password}@{parsed.hostname}:{parsed.port or 554}{parsed.path}"

            # Capture frame from RTSP in thread pool
            def grab_frame():
                cap = cv2.VideoCapture(auth_url)
                try:
                    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                    ret, frame = cap.read()
                    if not ret:
                        raise RuntimeError("Failed to grab frame from RTSP stream")
                    # Convert BGR to RGB
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    return Image.fromarray(frame_rgb)
                finally:
                    cap.release()

            image = await loop.run_in_executor(None, grab_frame)

            # Save if path provided
            if save_path:
                save_path = Path(save_path)
                save_path.parent.mkdir(parents=True, exist_ok=True)
                image.save(save_path)

            return image

        except Exception as e:
            logger.exception("Failed to capture ONVIF snapshot via RTSP")
            raise RuntimeError(f"Failed to capture image: {e}") from e

    async def get_stream_url(self) -> Optional[str]:
        """Get the RTSP stream URL for the camera."""
        if not await self.is_connected():
            await self.connect()

        if not self._stream_url:
            try:
                loop = asyncio.get_event_loop()
                self._stream_url = await loop.run_in_executor(
                    None, self._camera.get_stream_uri
                )
            except Exception as e:
                logger.exception("Failed to get ONVIF stream URL")
                raise RuntimeError(f"Failed to get stream URL: {e}") from e

        return self._stream_url

    async def get_status(self) -> Dict:
        """Get camera status with detailed capabilities."""
        if not await self.is_connected():
            try:
                await self.connect()
            except Exception as e:
                return {
                    "connected": False,
                    "error": str(e),
                    "resolution": "N/A",
                    "ptz_capable": False,
                    "audio_capable": False,
                    "streaming_capable": False,
                    "capture_capable": False,
                }

        try:
            loop = asyncio.get_event_loop()
            device_info = await loop.run_in_executor(
                None, self._camera.get_device_info
            )

            # Check PTZ capability
            ptz_capable = False
            try:
                await loop.run_in_executor(None, self._camera.get_ptz_service)
                ptz_capable = True
            except Exception:
                pass

            # Get profiles for resolution info
            profiles = await loop.run_in_executor(
                None, self._camera.get_media_profiles
            )
            resolution = "Unknown"
            if profiles and hasattr(profiles[0], "VideoEncoderConfiguration"):
                vec = profiles[0].VideoEncoderConfiguration
                if vec and hasattr(vec, "Resolution"):
                    resolution = f"{vec.Resolution.Width}x{vec.Resolution.Height}"

            return {
                "connected": True,
                "model": device_info.get("model", "Unknown"),
                "firmware": device_info.get("firmware_version", "Unknown"),
                "manufacturer": device_info.get("manufacturer", "Unknown"),
                "streaming": await self.is_streaming(),
                "resolution": resolution,
                "ptz_capable": ptz_capable,
                "audio_capable": False,  # ONVIF audio check would need more work
                "streaming_capable": True,
                "capture_capable": True,
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
        """Get comprehensive ONVIF camera information."""
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

            if await self.is_connected():
                try:
                    loop = asyncio.get_event_loop()
                    device_info = await loop.run_in_executor(
                        None, self._camera.get_device_info
                    )
                    info.update(
                        {
                            "model": device_info.get("model"),
                            "firmware_version": device_info.get("firmware_version"),
                            "serial_number": device_info.get("serial_number"),
                            "manufacturer": device_info.get("manufacturer"),
                            "hardware_id": device_info.get("hardware_id"),
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

    # PTZ Methods
    async def ptz_move(self, pan: float = 0, tilt: float = 0, zoom: float = 0):
        """Move PTZ camera continuously."""
        if not await self.is_connected():
            await self.connect()

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None, lambda: self._camera.continuous_move(pan, tilt, zoom)
        )

    async def ptz_stop(self):
        """Stop PTZ movement."""
        if not await self.is_connected():
            return

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._camera.stop_move)

    async def ptz_go_to_preset(self, preset_token: str):
        """Go to PTZ preset."""
        if not await self.is_connected():
            await self.connect()

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None, lambda: self._camera.go_to_preset(preset_token)
        )

    async def ptz_get_presets(self) -> list:
        """Get PTZ presets."""
        if not await self.is_connected():
            await self.connect()

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._camera.get_presets)

