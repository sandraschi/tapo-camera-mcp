"""
Custom exceptions for the Tapo Camera MCP.
"""

class TapoCameraError(Exception):
    """Base exception for all Tapo Camera MCP errors."""
    pass

class CameraConnectionError(TapoCameraError):
    """Raised when there's an error connecting to or communicating with a camera."""
    pass

class CameraAuthError(TapoCameraError):
    """Raised when authentication with a camera fails."""
    pass

class CameraNotSupportedError(TapoCameraError):
    """Raised when a requested feature is not supported by the camera."""
    pass

class ConfigurationError(TapoCameraError):
    """Raised when there's an error in the configuration."""
    pass

class ValidationError(TapoCameraError):
    """Raised when input validation fails."""
    pass

class ResourceNotFoundError(TapoCameraError):
    """Raised when a requested resource is not found."""
    pass

class OperationNotPermittedError(TapoCameraError):
    """Raised when an operation is not permitted."""
    pass

class RateLimitExceededError(TapoCameraError):
    """Raised when API rate limits are exceeded."""
    pass

class TimeoutError(TapoCameraError):
    """Raised when an operation times out."""
    pass

class StorageError(TapoCameraError):
    """Raised when there's an error with storage operations."""
    pass

class StreamError(TapoCameraError):
    """Raised when there's an error with video streaming."""
    pass
