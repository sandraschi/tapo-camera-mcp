"""
Tests for the Tapo Camera MCP server.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastmcp.server import FastMCP

from tapo_camera_mcp.core.server import TapoCameraServer
from tapo_camera_mcp.exceptions import AuthenticationError, ConnectionError
from tapo_camera_mcp.tools.camera import CameraInfoTool

# Test data
TEST_CONFIG = {
    "host": "192.168.1.100",
    "port": 443,
    "username": "testuser",
    "password": "testpass",
    "use_https": True,
    "verify_ssl": False,
    "timeout": 5,
    "web": {"enabled": False},
}


# Fixtures
@pytest.fixture
def config():
    """Return a test configuration."""
    return {
        "host": TEST_CONFIG["host"],
        "port": TEST_CONFIG["port"],
        "username": TEST_CONFIG["username"],
        "password": TEST_CONFIG["password"],
        "use_https": TEST_CONFIG["use_https"],
        "verify_ssl": TEST_CONFIG["verify_ssl"],
        "timeout": TEST_CONFIG["timeout"],
    }


@pytest.fixture
def mock_session():
    """Return a mock aiohttp client session."""
    with patch("aiohttp.ClientSession") as mock_session_class:
        mock_session = AsyncMock()
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None
        mock_session_class.return_value = mock_session

        # Mock response for device info
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "result": {
                "device_id": "test-device-123",
                "model": "Tapo C200",
                "fw_ver": "1.0.0",
                "hw_ver": "1.0",
                "type": "SMART.IPCAMERA",
                "mac": "00:11:22:33:44:55",
                "dev_name": "Tapo Camera",
                "device_on": True,
            }
        }
        mock_session.request.return_value.__aenter__.return_value = mock_response

        yield mock_session


@pytest.fixture
def tapo_camera(config, mock_session):
    """Return a TapoCameraServer instance with a mock session."""
    server = TapoCameraServer()
    # Initialize with test config
    server.config = {
        "cameras": [
            {
                "host": config["host"],
                "username": config["username"],
                "password": config["password"],
            }
        ],
        "web": {"enabled": False},
    }
    # Mock the session creation and FastMCP initialization
    server._session = mock_session
    server.mcp = Mock(spec=FastMCP)
    return server


@pytest.mark.asyncio
async def test_initialization(tapo_camera):
    """Test that the server initializes correctly."""
    assert tapo_camera is not None
    assert tapo_camera.mcp is not None
    assert len(tapo_camera.config.get("cameras", [])) > 0


@pytest.mark.asyncio
async def test_register_tools(tapo_camera):
    """Test that tools are registered with the MCP server."""
    # Mock the tool registration
    tapo_camera.mcp.tool = Mock()

    # Call the method that registers tools
    tapo_camera._register_tools()

    # Verify that mcp.tool was called for each tool
    assert tapo_camera.mcp.tool.call_count > 0


@pytest.mark.asyncio
async def test_run_server(tapo_camera):
    """Test that the server can be started."""
    # Mock the MCP run method
    tapo_camera.mcp.run = AsyncMock()

    # Call the run method
    await tapo_camera.run(host="127.0.0.1", port=8000, stdio=False, direct=True)

    # Verify that mcp.run was called
    tapo_camera.mcp.run.assert_called_once()


@pytest.mark.asyncio
async def test_web_server_initialization(tapo_camera):
    """Test that the web server is initialized when enabled."""
    # Enable web server in config
    tapo_camera.config["web"] = {"enabled": True, "port": 8080}

    # Mock the web server
    with patch("tapo_camera_mcp.web.server.WebServer") as mock_web_server:
        mock_web_instance = Mock()
        mock_web_server.return_value = mock_web_instance

        # Initialize the server
        await tapo_camera.initialize(tapo_camera.config)

        # Verify the web server was created and started
        mock_web_server.assert_called_once()
        mock_web_instance.start.assert_called_once()


@pytest.mark.asyncio
async def test_handle_get_camera_info(tapo_camera, mock_session):
    """Test handling of get_camera_info tool."""
    # Mock the response for get_device_info
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = {
        "result": {
            "model": "Tapo C200",
            "fw_ver": "1.0.0",
            "hw_ver": "1.0",
            "mac": "00:11:22:33:44:55",
            "device_id": "test-device-123",
            "device_on": True,
        }
    }
    mock_session.request.return_value.__aenter__.return_value = mock_response

    # Call the method that handles get_camera_info
    tool = CameraInfoTool()
    result = await tool.execute({})

    # Verify the response
    assert result is not None
    assert "model" in result
    assert result["model"] == "Tapo C200"
    assert "fw_ver" in result
    assert result["fw_ver"] == "1.0.0"
    """Test authentication error during connection."""
    # Mock a 401 Unauthorized response
    mock_response = AsyncMock()
    mock_response.status = 401
    mock_session.request.return_value.__aenter__.return_value = mock_response

    with pytest.raises(AuthenticationError):
        await tapo_camera.connect()

    assert tapo_camera._is_connected is False
    assert tapo_camera._session is None


@pytest.mark.asyncio
async def test_connect_network_error(tapo_camera, mock_session):
    """Test network error during connection."""
    # Mock a network error
    mock_session.request.side_effect = aiohttp.ClientError("Network error")

    with pytest.raises(ConnectionError):
        await tapo_camera.connect()

    assert tapo_camera._is_connected is False
    assert tapo_camera._session is None


@pytest.mark.asyncio
async def test_disconnect(tapo_camera, mock_session):
    """Test disconnecting from the camera."""
    await tapo_camera.connect()
    assert tapo_camera._is_connected is True

    await tapo_camera.disconnect()
    assert tapo_camera._is_connected is False
    assert tapo_camera._session is None


@pytest.mark.asyncio
async def test_get_camera_info(tapo_camera, mock_session):
    """Test getting camera information."""
    # Mock the response for get_device_info
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = {
        "result": {
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
            "on_time": 3600,
            "overheated": False,
            "nickname": "My Tapo Camera",
            "location": "Living Room",
        }
    }
    mock_session.request.return_value.__aenter__.return_value = mock_response

    await tapo_camera.connect()
    info = await tapo_camera.handle_get_info(McpMessage(type="camera_info", data={}))

    assert "model" in info
    assert info["model"] == "Tapo C200"
    assert "firmware_version" in info
    assert "serial_number" in info


@pytest.mark.asyncio
async def test_ptz_control(tapo_camera, mock_session):
    """Test PTZ control commands."""
    # Mock the response for PTZ control
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = {"result": {"response": "ok"}}
    mock_session.request.return_value.__aenter__.return_value = mock_response

    await tapo_camera.connect()

    # Test PTZ move
    result = await tapo_camera.handle_ptz_move(
        McpMessage(type="ptz_move", data={"direction": "up", "speed": 0.5})
    )
    assert "status" in result
    assert result["status"] == "success"

    # Test PTZ home
    result = await tapo_camera.handle_ptz_home(McpMessage(type="ptz_home", data={}))
    assert "status" in result
    assert result["status"] == "success"

    # Test PTZ preset
    result = await tapo_camera.handle_ptz_preset(
        McpMessage(type="ptz_preset", data={"action": "list"})
    )
    assert "status" in result
    assert "presets" in result


@pytest.mark.asyncio
async def test_stream_control(tapo_camera, mock_session):
    """Test stream control commands."""
    # Mock the response for stream control
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = {
        "result": {
            "stream_url": "rtsp://192.168.1.100:554/stream1",
            "stream_type": "rtsp",
        }
    }
    mock_session.request.return_value.__aenter__.return_value = mock_response

    await tapo_camera.connect()

    # Test start stream
    result = await tapo_camera.handle_start_stream(
        McpMessage(type="stream_start", data={"stream_id": "test", "stream_type": "rtsp"})
    )
    assert "status" in result
    assert result["status"] == "success"
    assert "stream_url" in result

    # Test stop stream
    result = await tapo_camera.handle_stop_stream(
        McpMessage(type="stream_stop", data={"stream_id": "test"})
    )
    assert "status" in result
    assert result["status"] == "success"


@pytest.mark.asyncio
async def test_motion_detection(tapo_camera, mock_session):
    """Test motion detection control."""
    # Mock the response for motion detection
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = {"result": {"motion_detection_enabled": True}}
    mock_session.request.return_value.__aenter__.return_value = mock_response

    await tapo_camera.connect()

    # Test start motion detection
    result = await tapo_camera.handle_motion_detection(
        McpMessage(type="motion_detection", data={"action": "start"})
    )
    assert "status" in result
    assert result["status"] == "success"

    # Test stop motion detection
    result = await tapo_camera.handle_motion_detection(
        McpMessage(type="motion_detection", data={"action": "stop"})
    )
    assert "status" in result
    assert result["status"] == "success"

    # Test get motion detection status
    result = await tapo_camera.handle_motion_detection(
        McpMessage(type="motion_detection", data={"action": "status"})
    )
    assert "status" in result
    assert "enabled" in result
    assert "motion_detected" in result


@pytest.mark.asyncio
async def test_recording_control(tapo_camera, mock_session, tmp_path):
    """Test recording control commands."""
    # Set up test recording directory
    test_dir = tmp_path / "recordings"
    test_dir.mkdir()
    tapo_camera.config.storage_path = str(test_dir)

    # Mock the response for recording control
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = {"result": {"recording_id": "test-recording"}}
    mock_session.request.return_value.__aenter__.return_value = mock_response

    await tapo_camera.connect()

    # Test start recording
    result = await tapo_camera.handle_start_recording(
        McpMessage(type="recording_start", data={"recording_id": "test"})
    )
    assert "status" in result
    assert result["status"] == "success"
    assert "recording_id" in result

    # Test stop recording
    result = await tapo_camera.handle_stop_recording(
        McpMessage(type="recording_stop", data={"recording_id": "test"})
    )
    assert "status" in result
    assert result["status"] == "success"


@pytest.mark.asyncio
async def test_snapshot(tapo_camera, mock_session, tmp_path):
    """Test taking a snapshot."""
    # Create a test image
    test_image = b"\x89PNG\r\n\x1a\n\x00\x00\x00\x0dIHDR..."

    # Mock the response for snapshot
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.read.return_value = test_image
    mock_session.request.return_value.__aenter__.return_value = mock_response

    await tapo_camera.connect()

    # Test take snapshot
    result = await tapo_camera.handle_snapshot(McpMessage(type="snapshot", data={}))
    assert "status" in result
    assert result["status"] == "success"
    assert "snapshot" in result
    assert result["snapshot"].startswith("data:image/")
    assert "timestamp" in result


@pytest.mark.asyncio
async def test_config_handling(tapo_camera, mock_session):
    """Test configuration handling."""
    await tapo_camera.connect()

    # Test get config
    result = await tapo_camera.handle_get_config(McpMessage(type="camera_config", data={}))
    assert "host" in result
    assert result["host"] == tapo_camera.config.host

    # Test update config
    new_host = "192.168.1.200"
    result = await tapo_camera.handle_update_config(
        McpMessage(type="camera_update_config", data={"config": {"host": new_host}})
    )
    assert "status" in result
    assert result["status"] == "success"
    assert tapo_camera.config.host == new_host


@pytest.mark.asyncio
async def test_reboot(tapo_camera, mock_session):
    """Test rebooting the camera."""
    # Mock the response for reboot
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = {"result": {"response": "ok"}}
    mock_session.request.return_value.__aenter__.return_value = mock_response

    await tapo_camera.connect()

    # Test reboot
    result = await tapo_camera.handle_reboot(McpMessage(type="camera_reboot", data={}))
    assert "status" in result
    assert result["status"] == "success"
    assert tapo_camera._is_connected is False
