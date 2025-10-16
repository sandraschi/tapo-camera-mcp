"""
Exception classes for Tapo-Camera-MCP.
"""


class TapoCameraError(Exception):
    """Base exception for all Tapo Camera MCP errors."""

    pass


class AuthenticationError(TapoCameraError):
    """Raised when authentication with the camera fails."""

    pass


class ConnectionError(TapoCameraError):
    """Raised when there is a connection error with the camera."""

    pass


class CameraBusyError(TapoCameraError):
    """Raised when the camera is busy with another operation."""

    pass


class CameraNotSupportedError(TapoCameraError):
    """Raised when a feature is not supported by the camera."""

    pass


class StreamError(TapoCameraError):
    """Raised when there is an error with the video stream."""

    pass


class PTZError(TapoCameraError):
    """Raised when there is an error with PTZ operations."""

    pass


class StorageError(TapoCameraError):
    """Raised when there is an error accessing camera storage."""

    pass


class ConfigurationError(TapoCameraError):
    """Raised when there is an error with the camera configuration."""

    pass


class TimeoutError(TapoCameraError):
    """Raised when an operation times out."""

    pass


class FirmwareError(TapoCameraError):
    """Raised when there is a firmware-related error."""

    pass
