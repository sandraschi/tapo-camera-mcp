"""Base camera interface for unified camera support."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional, Union
from pathlib import Path
from PIL import Image


class CameraType(str, Enum):
    """Supported camera types.

    Attributes:
        TAPO: Tapo camera (TP-Link)
        RING: Ring doorbell camera
        WEBCAM: Standard USB/web camera
        PETCUBE: Petcube pet camera
    """

    TAPO = "tapo"
    RING = "ring"
    WEBCAM = "webcam"
    PETCUBE = "petcube"

    @classmethod
    def values(cls):
        """Get all enum values."""
        return [e.value for e in cls]


@dataclass
class CameraConfig:
    """Camera configuration."""

    name: str
    type: CameraType
    params: dict
    enabled: bool = True


class BaseCamera(ABC):
    """Base class for all camera implementations.

    Attributes:
        config: Camera configuration
        _is_streaming: Whether the camera is currently streaming
        _is_connected: Whether the camera is connected
        _last_error: Last error message, if any
    """

    def __init__(self, config: CameraConfig):
        self.config = config
        self._is_streaming = False
        self._is_connected = False
        self._last_error = None

    @abstractmethod
    async def connect(self) -> bool:
        """Initialize connection to the camera.

        Returns:
            bool: True if connection was successful, False otherwise
        """
        self._is_connected = True
        self._last_error = None
        return True

    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to the camera.

        This should clean up any resources and set _is_connected to False.
        """
        self._is_connected = False

    @abstractmethod
    async def capture_still(
        self, save_path: Optional[Union[str, Path]] = None
    ) -> Image.Image:
        """Capture a still image from the camera.

        Args:
            save_path: Optional path to save the image to

        Returns:
            PIL.Image.Image: The captured image

        Raises:
            RuntimeError: If the camera is not connected or capture fails
        """
        if not self._is_connected:
            raise RuntimeError("Camera is not connected")

    @abstractmethod
    async def get_stream_url(self) -> Optional[str]:
        """Get the stream URL for the camera.

        Returns:
            Optional[str]: The stream URL if available, None otherwise
        """
        if not self._is_connected:
            return None

    @abstractmethod
    async def get_status(self) -> Dict:
        """Get the status of the camera.

        Returns:
            Dict: Status information including connection state, streaming state, etc.
        """
        return {
            "connected": self._is_connected,
            "streaming": self._is_streaming,
            "type": self.config.type.value,
            "enabled": self.config.enabled,
            "last_error": self._last_error,
            "model": "Unknown",
            "firmware": "Unknown",
            "resolution": "Unknown",
            "ptz_capable": False,
            "audio_capable": False,
            "streaming_capable": False,
            "capture_capable": True,  # Most cameras can capture
            "config": {
                k: v
                for k, v in self.config.params.items()
                if k
                not in ["password", "token", "api_key"]  # Don't expose sensitive data
            },
        }

    async def is_streaming(self) -> bool:
        """Check if the camera is currently streaming.

        Returns:
            bool: True if the camera is streaming, False otherwise
        """
        return self._is_streaming

    async def is_connected(self) -> bool:
        """Check if the camera is connected.

        Returns:
            bool: True if connected, False otherwise
        """
        return self._is_connected


class CameraFactory:
    """Factory for creating camera instances."""

    _camera_classes = {}

    @classmethod
    def register(cls, camera_type: CameraType):
        """Register a camera implementation."""

        def decorator(camera_class):
            cls._camera_classes[camera_type] = camera_class
            return camera_class

        return decorator

    @classmethod
    def create(cls, config: Union[dict, CameraConfig]) -> BaseCamera:
        """Create a camera instance from config."""
        if isinstance(config, dict):
            config = CameraConfig(**config)

        if config.type not in cls._camera_classes:
            raise ValueError(f"Unsupported camera type: {config.type}")

        return cls._camera_classes[config.type](config)
