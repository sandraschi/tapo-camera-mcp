"""
Direct test script for Tapo Camera MCP server (FastMCP 2.10).
This script tests the server functionality directly without using pytest.
"""

import asyncio
import json
import os
import sys
from unittest.mock import AsyncMock, patch

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from tapo_camera_mcp.core.server import TapoCameraServer


async def run_tests():
    """Run direct tests for the TapoCameraServer class."""
    print("Starting direct tests for TapoCameraServer...")

    # Initialize the server
    server = TapoCameraServer()
    test_host = "192.168.1.100"
    test_username = "testuser"
    test_password = "testpass"

    # Test 1: Connect to camera
    print("\n=== Test 1: Connect to camera ===")
    with patch("tapo_camera_mcp.server_v2.Tapo") as mock_tapo_class:
        # Setup mock
        mock_camera = AsyncMock()
        mock_camera.host = test_host
        mock_camera.getBasicInfo = AsyncMock(
            return_value={
                "device_info": {"device_model": "Tapo C200"},
                "firmware_version": "1.0.0",
                "mac": "00:11:22:33:44:55",
            }
        )
        mock_tapo_class.return_value = mock_camera

        # Call the connect_camera tool
        result = await server.mcp.call_tool(
            "connect_camera",
            {"host": test_host, "username": test_username, "password": test_password},
        )

        # Verify the result
        print("Connect result:", json.dumps(result.content, indent=2))
        assert result.content["status"] == "connected", "Failed to connect to camera"

        # Verify the camera was initialized correctly
        mock_tapo_class.assert_called_once_with(
            test_host, test_username, test_password, cloud_password=test_password
        )
        mock_camera.login.assert_awaited_once()
        print("✓ Test 1 passed: Successfully connected to camera")

    # Test 2: Get camera info
    print("\n=== Test 2: Get camera info ===")
    server.camera = mock_camera
    mock_camera.getBasicInfo = AsyncMock(
        return_value={
            "device_info": {"device_model": "Tapo C200"},
            "firmware_version": "1.0.0",
            "mac": "00:11:22:33:44:55",
        }
    )

    result = await server.mcp.call_tool("get_camera_info", {})
    print("Camera info:", json.dumps(result.content, indent=2))
    assert "model" in result.content, "Camera info missing model"
    assert result.content["model"] == "Tapo C200", "Incorrect camera model"
    print("✓ Test 2 passed: Successfully retrieved camera info")

    # Test 3: PTZ control
    print("\n=== Test 3: PTZ control ===")
    mock_camera.moveRight = AsyncMock()
    mock_camera.moveUp = AsyncMock()

    result = await server.mcp.call_tool(
        "move_ptz", {"pan": 0.5, "tilt": 0.3, "speed": 0.7}
    )

    print("PTZ result:", json.dumps(result.content, indent=2))
    assert result.content["status"] == "success", "PTZ move failed"
    mock_camera.moveRight.assert_awaited_with(35)  # 0.5 * 100 * 0.7 = 35
    mock_camera.moveUp.assert_awaited_with(21)  # 0.3 * 100 * 0.7 = 21
    print("✓ Test 3 passed: Successfully controlled PTZ")

    # Test 4: Motion detection
    print("\n=== Test 4: Motion detection ===")
    mock_camera.setMotionDetection = AsyncMock()

    # Enable motion detection
    result = await server.mcp.call_tool("set_motion_detection", {"enabled": True})
    print("Motion detection enable result:", json.dumps(result.content, indent=2))
    assert result.content["status"] == "success", "Failed to enable motion detection"
    assert result.content["motion_detection"] is True, "Motion detection not enabled"
    mock_camera.setMotionDetection.assert_awaited_once_with(True)
    print("✓ Test 4 passed: Successfully controlled motion detection")

    # Test 5: LED control
    print("\n=== Test 5: LED control ===")
    mock_camera.setLED = AsyncMock()

    # Enable LED
    result = await server.mcp.call_tool("set_led_enabled", {"enabled": True})
    print("LED enable result:", json.dumps(result.content, indent=2))
    assert result.content["status"] == "success", "Failed to enable LED"
    assert result.content["led_enabled"] is True, "LED not enabled"
    mock_camera.setLED.assert_awaited_once_with(True)
    print("✓ Test 5 passed: Successfully controlled LED")

    # Test 6: Privacy mode
    print("\n=== Test 6: Privacy mode ===")
    mock_camera.setPrivacyMode = AsyncMock()

    # Enable privacy mode
    result = await server.mcp.call_tool("set_privacy_mode", {"enabled": True})
    print("Privacy mode enable result:", json.dumps(result.content, indent=2))
    assert result.content["status"] == "success", "Failed to enable privacy mode"
    assert result.content["privacy_mode"] is True, "Privacy mode not enabled"
    mock_camera.setPrivacyMode.assert_awaited_once_with(True)
    print("✓ Test 6 passed: Successfully controlled privacy mode")

    # Test 7: Reboot camera
    print("\n=== Test 7: Reboot camera ===")
    mock_camera.reboot = AsyncMock()

    # Reboot camera
    result = await server.mcp.call_tool("reboot_camera", {})
    print("Reboot result:", json.dumps(result.content, indent=2))
    assert result.content["status"] == "success", "Failed to reboot camera"
    mock_camera.reboot.assert_awaited_once()
    print("✓ Test 7 passed: Successfully rebooted camera")

    print("\nAll tests completed successfully!")


if __name__ == "__main__":
    import os

    # Ensure we can import from the src directory
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))
    asyncio.run(run_tests())
