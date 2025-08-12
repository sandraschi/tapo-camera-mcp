"""
Tests for the Tapo Camera MCP server (FastMCP 2.10).
"""
import asyncio
import json
import os
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastmcp import Client

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tapo_camera_mcp.server_v2 import TapoCameraServer, CameraInfo, CameraStatus, StreamInfo

class TestTapoCameraServer(unittest.IsolatedAsyncioTestCase):
    """Test cases for the TapoCameraServer class."""
    
    async def asyncSetUp(self):
        """Set up test fixtures."""
        self.server = TapoCameraServer()
        self.test_host = "192.168.1.100"
        self.test_username = "testuser"
        self.test_password = "testpass"
        
        # Mock the Tapo camera
        self.mock_camera = AsyncMock()
        self.mock_camera.host = self.test_host
        
        # Patch the Tapo class to return our mock
        self.patcher = patch('tapo_camera_mcp.server_v2.Tapo', return_value=self.mock_camera)
        self.mock_tapo_class = self.patcher.start()
        
        # Connect to the server
        self.client = Client(transport="stdio")
        self.server_process = None
    
    async def asyncTearDown(self):
        """Clean up test fixtures."""
        self.patcher.stop()
        if self.server_process:
            self.server_process.terminate()
            await self.server_process.wait()
    
    async def test_connect_camera_success(self):
        """Test successful camera connection."""
        # Mock the camera's login and getBasicInfo methods
        self.mock_camera.login = AsyncMock()
        self.mock_camera.getBasicInfo = AsyncMock(return_value={
            "device_info": {"device_model": "Tapo C200"},
            "firmware_version": "1.0.0",
            "mac": "00:11:22:33:44:55"
        })
        
        # Call the connect_camera tool
        result = await self.server.mcp.call_tool("connect_camera", {
            "host": self.test_host,
            "username": self.test_username,
            "password": self.test_password
        })
        
        # Verify the result
        self.assertEqual(result.content["status"], "connected")
        self.assertEqual(result.content["camera_info"]["model"], "Tapo C200")
        
        # Verify the camera was initialized correctly
        self.mock_tapo_class.assert_called_once_with(
            self.test_host, 
            self.test_username, 
            self.test_password, 
            cloud_password=self.test_password
        )
        self.mock_camera.login.assert_awaited_once()
    
    async def test_get_camera_info(self):
        """Test getting camera information."""
        # Set up the test with a connected camera
        self.server.camera = self.mock_camera
        self.mock_camera.getBasicInfo = AsyncMock(return_value={
            "device_info": {
                "device_model": "Tapo C200",
                "device_id": "TEST123"
            },
            "firmware_version": "1.0.0",
            "mac": "00:11:22:33:44:55",
            "signal_level": 80,
            "ssid": "MyWiFi"
        })
        
        # Call the get_camera_info tool
        result = await self.server.mcp.call_tool("get_camera_info", {})
        
        # Verify the result
        self.assertIsInstance(result.content, dict)
        self.assertEqual(result.content["model"], "Tapo C200")
        self.assertEqual(result.content["firmware_version"], "1.0.0")
        self.assertEqual(result.content["mac_address"], "00:11:22:33:44:55")
    
    async def test_ptz_control(self):
        """Test PTZ control."""
        # Set up the test with a connected camera
        self.server.camera = self.mock_camera
        self.mock_camera.moveRight = AsyncMock()
        self.mock_camera.moveUp = AsyncMock()
        
        # Call the move_ptz tool
        result = await self.server.mcp.call_tool("move_ptz", {
            "pan": 0.5,
            "tilt": 0.3,
            "speed": 0.7
        })
        
        # Verify the result
        self.assertEqual(result.content["status"], "success")
        self.mock_camera.moveRight.assert_awaited_with(35)  # 0.5 * 100 * 0.7 = 35
        self.mock_camera.moveUp.assert_awaited_with(21)     # 0.3 * 100 * 0.7 = 21
    
    async def test_motion_detection(self):
        """Test motion detection control."""
        # Set up the test with a connected camera
        self.server.camera = self.mock_camera
        self.mock_camera.setMotionDetection = AsyncMock()
        
        # Test enabling motion detection
        result = await self.server.mcp.call_tool("set_motion_detection", {"enabled": True})
        self.assertEqual(result.content["status"], "success")
        self.assertTrue(result.content["motion_detection"])
        self.mock_camera.setMotionDetection.assert_awaited_once_with(True)
        
        # Test disabling motion detection
        self.mock_camera.setMotionDetection.reset_mock()
        result = await self.server.mcp.call_tool("set_motion_detection", {"enabled": False})
        self.assertEqual(result.content["status"], "success")
        self.assertFalse(result.content["motion_detection"])
        self.mock_camera.setMotionDetection.assert_awaited_once_with(False)
    
    async def test_led_control(self):
        """Test LED control."""
        # Set up the test with a connected camera
        self.server.camera = self.mock_camera
        self.mock_camera.setLED = AsyncMock()
        
        # Test enabling LED
        result = await self.server.mcp.call_tool("set_led_enabled", {"enabled": True})
        self.assertEqual(result.content["status"], "success")
        self.assertTrue(result.content["led_enabled"])
        self.mock_camera.setLED.assert_awaited_once_with(True)
        
        # Test disabling LED
        self.mock_camera.setLED.reset_mock()
        result = await self.server.mcp.call_tool("set_led_enabled", {"enabled": False})
        self.assertEqual(result.content["status"], "success")
        self.assertFalse(result.content["led_enabled"])
        self.mock_camera.setLED.assert_awaited_once_with(False)
    
    async def test_privacy_mode(self):
        """Test privacy mode control."""
        # Set up the test with a connected camera
        self.server.camera = self.mock_camera
        self.mock_camera.setPrivacyMode = AsyncMock()
        
        # Test enabling privacy mode
        result = await self.server.mcp.call_tool("set_privacy_mode", {"enabled": True})
        self.assertEqual(result.content["status"], "success")
        self.assertTrue(result.content["privacy_mode"])
        self.mock_camera.setPrivacyMode.assert_awaited_once_with(True)
        
        # Test disabling privacy mode
        self.mock_camera.setPrivacyMode.reset_mock()
        result = await self.server.mcp.call_tool("set_privacy_mode", {"enabled": False})
        self.assertEqual(result.content["status"], "success")
        self.assertFalse(result.content["privacy_mode"])
        self.mock_camera.setPrivacyMode.assert_awaited_once_with(False)
    
    async def test_reboot_camera(self):
        """Test rebooting the camera."""
        # Set up the test with a connected camera
        self.server.camera = self.mock_camera
        self.mock_camera.reboot = AsyncMock()
        
        # Test rebooting the camera
        result = await self.server.mcp.call_tool("reboot_camera", {})
        self.assertEqual(result.content["status"], "success")
        self.assertEqual(result.content["message"], "Camera is rebooting")
        self.mock_camera.reboot.assert_awaited_once()

if __name__ == "__main__":
    unittest.main()
