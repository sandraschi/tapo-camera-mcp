"""
Configuration file for pytest.
This file is automatically discovered and used by pytest.
"""
import asyncio
import os
import sys
from pathlib import Path
from typing import AsyncGenerator, Dict, Any

import pytest
import pytest_asyncio
from fastmcp import FastMCP

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tapo_camera_mcp.server import TapoCameraMCP
from tapo_camera_mcp.models import CameraConfig
from tapo_camera_mcp.exceptions import ConnectionError, AuthenticationError

# Test configuration
TEST_CONFIG = {
    "host": "192.168.1.100",
    "port": 443,
    "username": "testuser",
    "password": "testpass",
    "use_https": True,
    "verify_ssl": False,
    "timeout": 5,
}

# Fixtures
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def config() -> CameraConfig:
    """Return a test configuration."""
    return CameraConfig(**TEST_CONFIG)

@pytest_asyncio.fixture
async def mock_session():
    """Return a mock aiohttp client session."""
    with patch('aiohttp.ClientSession') as mock_session_class:
        mock_session = AsyncMock()
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None
        mock_session_class.return_value = mock_session
        
        # Mock response for connection test
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {"result": {"device_id": "test-device-123"}}
        
        mock_session.request.return_value.__aenter__.return_value = mock_response
        
        yield mock_session

@pytest_asyncio.fixture
async def tapo_camera(config, mock_session) -> AsyncGenerator[TapoCameraMCP, None]:
    """Return a TapoCameraMCP instance with a mock session."""
    camera = TapoCameraMCP(config=config.dict())
    
    # Connect the camera
    await camera.connect()
    
    yield camera
    
    # Clean up
    if camera._is_connected:
        await camera.disconnect()

@pytest.fixture
def test_image() -> bytes:
    """Return a test image in bytes."""
    # This is a minimal PNG file (1x1 transparent pixel)
    return (
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89' 
        b'\x00\x00\x00\nIDATx\xdac\x00\x01\x00\x00\x05\x00\x01\x0f\xa5\xea\xfd\x00\x00\x00\x00IEND\xaeB`\x82'
    )

# Test utilities
def assert_dict_contains(d: Dict[Any, Any], sub_d: Dict[Any, Any]) -> None:
    """Assert that dictionary d contains all key-value pairs from sub_d."""
    for key, value in sub_d.items():
        assert key in d, f"Key '{key}' not found in dictionary"
        assert d[key] == value, f"Value for key '{key}' does not match. Expected {value}, got {d[key]}"

# Mock classes for testing
class AsyncContextManagerMock:
    """A mock class for async context managers."""
    
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

# Mock classes for external dependencies
class MockResponse:
    """A mock response class for testing HTTP requests."""
    
    def __init__(self, status: int, json_data: Dict[str, Any] = None, text: str = None):
        self.status = status
        self._json_data = json_data or {}
        self._text = text or ""
    
    async def json(self) -> Dict[str, Any]:
        """Return the JSON response data."""
        return self._json_data
    
    async def text(self) -> str:
        """Return the response text."""
        return self._text
    
    async def read(self) -> bytes:
        """Return the response content as bytes."""
        return self._text.encode() if self._text else b''
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

# Patch decorators for common mocks
def patch_aiohttp_client():
    """Patch aiohttp client to return mock responses."""
    return patch('aiohttp.ClientSession')

def patch_os_path_exists(exists: bool = True):
    """Patch os.path.exists to return the specified value."""
    return patch('os.path.exists', return_value=exists)

def patch_open():
    """Patch the built-in open function."""
    return patch('builtins.open', new_callable=MagicMock)

def patch_json_load(return_value: Any = None):
    """Patch json.load to return the specified value."""
    return patch('json.load', return_value=return_value)

def patch_json_dump():
    """Patch json.dump to do nothing."""
    return patch('json.dump')

# Constants for testing
TEST_DEVICE_INFO = {
    "model": "Tapo C200",
    "fw_ver": "1.0.0",
    "hw_ver": "1.0",
    "type": "SMART.TAPOPLUG",
    "mac": "00-11-22-33-44-55",
    "device_id": "test-device-123",
    "hw_id": "test-hw-id",
    "fw_id": "test-fw-id",
    "oem_id": "test-oem-id",
    "color": "#000000",
    "alias": "Tapo Camera",
    "dev_name": "Tapo Camera C200",
    "icon": "",
    "latitude": 0,
    "longitude": 0,
    "has_set_location_info": False,
    "ip": "192.168.1.100",
    "ssid": "MyWiFi",
    "signal_level": 4,
    "rssi": -50,
    "on_time": 3600,
    "specs": "",
    "lang": "en_US",
    "region": "US",
    "device_on": True,
    "overheated": False,
    "nickname": "My Tapo Camera",
    "location": "Living Room"
}

TEST_CAMERA_STATUS = {
    "device_id": "test-device-123",
    "is_on": True,
    "is_online": True,
    "is_streaming": False,
    "is_recording": False,
    "motion_detection_enabled": True,
    "motion_detected": False,
    "sound_detection_enabled": False,
    "sound_detected": False,
    "privacy_mode": False,
    "led_enabled": True,
    "battery_level": 100,
    "signal_level": 4,
    "rssi": -50,
    "uptime": 3600,
    "last_motion": None,
    "last_sound": None,
    "last_alarm": None,
    "storage": {
        "total_bytes": 10737418240,  # 10 GB
        "used_bytes": 1073741824,   # 1 GB
        "free_bytes": 9663676416,   # 9 GB
        "usage_percent": 10.0
    },
    "firmware_version": "1.0.0",
    "hardware_version": "1.0",
    "model": "Tapo C200",
    "serial_number": "00-11-22-33-44-55",
    "ip_address": "192.168.1.100",
    "mac_address": "00:11:22:33:44:55",
    "ssid": "MyWiFi",
    "location": "Living Room",
    "timezone": "America/New_York",
    "last_updated": "2023-01-01T12:00:00Z"
}

TEST_STREAM_INFO = {
    "stream_id": "test-stream-123",
    "stream_type": "rtsp",
    "stream_url": "rtsp://192.168.1.100:554/stream1",
    "width": 1920,
    "height": 1080,
    "fps": 30,
    "bitrate": 2048,
    "codec": "H.264",
    "audio_enabled": True,
    "audio_codec": "AAC",
    "audio_bitrate": 128,
    "audio_channels": 2,
    "audio_sample_rate": 44100,
    "status": "active",
    "clients": 1,
    "started_at": "2023-01-01T12:00:00Z",
    "uptime": 60,
    "bytes_sent": 15360000,
    "bytes_received": 0,
    "bitrate_current": 2048,
    "bitrate_max": 4096,
    "bitrate_min": 512,
    "fps_current": 30,
    "fps_max": 30,
    "fps_min": 15,
    "resolution": "1920x1080",
    "quality": "high"
}

TEST_RECORDING_INFO = {
    "recording_id": "test-recording-123",
    "camera_id": "test-device-123",
    "start_time": "2023-01-01T12:00:00Z",
    "end_time": "2023-01-01T12:01:00Z",
    "duration": 60,
    "size_bytes": 15360000,
    "file_path": "/recordings/test-recording-123.mp4",
    "file_format": "mp4",
    "video_codec": "H.264",
    "audio_codec": "AAC",
    "resolution": "1920x1080",
    "fps": 30,
    "bitrate": 2048,
    "audio_bitrate": 128,
    "channels": 2,
    "sample_rate": 44100,
    "status": "completed",
    "motion_detected": True,
    "motion_regions": [[0, 0, 100, 100]],
    "motion_scores": [0.95],
    "motion_timestamps": ["2023-01-01T12:00:30Z"],
    "tags": ["motion"],
    "metadata": {}
}
