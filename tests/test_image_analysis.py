"""Tests for image capture and analysis functionality."""
import asyncio
import os
import shutil
import tempfile
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from tapo_camera_mcp.server_v2 import TapoCameraServer

class TestImageAnalysis(unittest.IsolatedAsyncioTestCase):
    """Test image capture and analysis functionality."""

    async def asyncSetUp(self):
        """Set up test fixtures."""
        self.server = TapoCameraServer()
        self.server.camera = AsyncMock()
        self.temp_dir = tempfile.mkdtemp()
        
        # Patch the temp directory for testing
        self.original_temp = os.path.join(tempfile.gettempdir(), "tapo_test")
        os.makedirs(self.original_temp, exist_ok=True)
        
    async def asyncTearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    @patch("PIL.Image.open")
    @patch("builtins.open", new_callable=unittest.mock.mock_open)
    async def test_analyze_image(self, mock_file, mock_image_open):
        """Test image analysis with mock data."""
        # Setup mock image
        mock_img = MagicMock()
        mock_img.mode = "RGB"
        mock_img.size = (1920, 1080)
        mock_img.convert.return_value = mock_img
        mock_image_open.return_value.__enter__.return_value = mock_img
        
        # Create a test image file
        test_image_path = os.path.join(self.temp_dir, "test.jpg")
        with open(test_image_path, "wb") as f:
            f.write(b"fake image data")
        
        # Test analysis
        result = await self.server._analyze_image(test_image_path, "Describe this image")
        
        # Verify results
        self.assertIn("image_base64", result)
        self.assertTrue(result["analysis_ready"])
        self.assertEqual(result["prompt"], "Describe this image")
    
    @patch("tapo_camera_mcp.server_v2.TapoCameraServer._analyze_image")
    async def test_capture_still(self, mock_analyze):
        """Test capturing a still image with analysis."""
        # Mock camera response
        self.server.camera.getSnapshot.return_value = b"fake image data"
        
        # Mock analysis response
        mock_analyze.return_value = {
            "analysis_ready": True,
            "prompt": "Test prompt",
            "image_base64": "base64_encoded_data"
        }
        
        # Test capture with analysis
        result = await self.server.capture_still({
            "save_to_temp": True,
            "analyze": True,
            "prompt": "Test prompt",
            "camera_name": "test_cam"
        })
        
        # Verify results
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["camera"], "test_cam")
        self.assertIn("saved_path", result)
        self.assertIn("analysis", result)
        self.assertTrue(os.path.exists(result["saved_path"]))
    
    @patch("tapo_camera_mcp.server_v2.TapoCameraServer.capture_still")
    async def test_security_scan(self, mock_capture):
        """Test security scan functionality."""
        # Mock capture response
        mock_capture.return_value = {
            "status": "success",
            "saved_path": "/tmp/security_scan_test.jpg",
            "analysis": {"analysis_ready": True}
        }
        
        # Test security scan
        result = await self.server.security_scan({
            "threat_types": ["person", "package"],
            "save_images": True
        })
        
        # Verify results
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["scan_type"], "security")
        self.assertEqual(len(result["results"]), 1)
        self.assertIn("threat_types_monitored", result)
        self.assertEqual(result["threat_types_monitored"], ["person", "package"])


if __name__ == "__main__":
    unittest.main()
