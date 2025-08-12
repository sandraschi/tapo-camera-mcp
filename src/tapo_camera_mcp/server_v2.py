"""
Tapo-Camera-MCP - FastMCP 2.10 server for controlling TP-Link Tapo cameras.
"""
import asyncio
import logging
from typing import Any, Dict, List, Optional, Set, Union

from fastmcp import FastMCP, mcp_tool
from pydantic import BaseModel, Field, HttpUrl
from pytapo import Tapo

# Configure logging
logger = logging.getLogger(__name__)

# Pydantic models for request/response validation
class CameraConfig(BaseModel):
    """Camera configuration model."""
    host: str = Field(..., description="Camera IP address or hostname")
    username: str = Field(..., description="Camera username")
    password: str = Field(..., description="Camera password")
    stream_quality: str = Field("hd", description="Stream quality (hd/sd)")
    verify_ssl: bool = Field(True, description="Verify SSL certificate")

class PTZPosition(BaseModel):
    """PTZ position model."""
    pan: float = Field(0.0, ge=-1.0, le=1.0, description="Pan position (-1.0 to 1.0)")
    tilt: float = Field(0.0, ge=-1.0, le=1.0, description="Tilt position (-1.0 to 1.0)")
    zoom: float = Field(0.0, ge=0.0, le=1.0, description="Zoom level (0.0 to 1.0)")

class CameraInfo(BaseModel):
    """Camera information model."""
    model: str = Field(..., description="Camera model name")
    serial_number: str = Field(..., description="Camera serial number")
    firmware_version: str = Field(..., description="Firmware version")
    mac_address: str = Field(..., description="MAC address")
    ip_address: str = Field(..., description="IP address")
    wifi_signal: int = Field(..., description="WiFi signal strength (0-100)")
    wifi_ssid: str = Field(..., description="Connected WiFi SSID")

class CameraStatus(BaseModel):
    """Camera status model."""
    online: bool = Field(..., description="Camera online status")
    recording: bool = Field(..., description="Recording status")
    motion_detected: bool = Field(..., description="Motion detection status")
    privacy_mode: bool = Field(..., description="Privacy mode status")
    led_enabled: bool = Field(..., description="LED status")
    uptime: int = Field(..., description="Uptime in seconds")
    storage: Dict[str, int] = Field(..., description="Storage information")

class StreamInfo(BaseModel):
    """Stream information model."""
    url: HttpUrl = Field(..., description="Stream URL")
    type: str = Field(..., description="Stream type (rtsp/rtmp)")
    quality: str = Field(..., description="Stream quality (hd/sd)")

class TapoCameraServer:
    """Tapo Camera MCP server implementation using FastMCP 2.10."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the Tapo Camera MCP server."""
        self.config = CameraConfig(**(config or {}))
        self.camera: Optional[Tapo] = None
        self.mcp = FastMCP(
            name="Tapo-Camera-MCP",
            version="0.2.0",
            description="FastMCP 2.10 server for TP-Link Tapo cameras"
        )
        self._register_tools()
    
    def _register_tools(self) -> None:
        """Register all MCP tools."""
        # Help tool (standard for all MCP servers)
        @self.mcp.tool()
        async def help(params: dict = None) -> str:
            """
            Get help about available tools and their usage.
            
            Args:
                params: Dictionary containing any parameters (unused)
                
            Returns:
                str: Help message with available tools and descriptions.
            """
            return self.mcp.get_help()
        
        # Camera connection management
        @self.mcp.tool()
        async def connect_camera(params: dict) -> Dict[str, Any]:
            """
            Connect to a Tapo camera.
            
            Args:
                params: Dictionary containing connection parameters:
                    - host: Camera IP address or hostname
                    - username: Camera username
                    - password: Camera password
                    - verify_ssl: Verify SSL certificate (optional, default: True)
                
            Returns:
                dict: Connection status and camera information
            """
            try:
                host = params.get("host")
                username = params.get("username")
                password = params.get("password")
                verify_ssl = params.get("verify_ssl", True)
                
                if not all([host, username, password]):
                    raise ValueError("Missing required parameters: host, username, password")
                
                if self.camera:
                    await self.camera.close()
                
                self.camera = Tapo(host, username, password, cloud_password=password)
                await self.camera.login()
                info = await self.camera.getBasicInfo()
                
                return {
                    "status": "connected",
                    "camera_info": {
                        "model": info.get("device_info", {}).get("device_model"),
                        "firmware": info.get("firmware_version"),
                        "mac_address": info.get("mac"),
                        "ip_address": host,
                        "host": host,
                        "username": username,
                        "password": password
                    }
                }
            except Exception as e:
                logger.error(f"Failed to connect to camera: {str(e)}")
                return {"status": "error", "message": str(e)}
        
        @self.mcp.tool()
        async def disconnect_camera(params: dict = None) -> Dict[str, str]:
            """
            Disconnect from the Tapo camera.
            
            Args:
                params: Dictionary containing any parameters (unused)
                
            Returns:
                dict: Disconnection status
            """
            if self.camera:
                await self.camera.close()
                self.camera = None
            return {"status": "disconnected"}
        
        # Camera information and status
        @self.mcp.tool()
        async def get_camera_info(params: dict = None) -> Dict[str, Any]:
            """
            Get detailed information about the connected camera.
            
            Args:
                params: Dictionary containing any parameters (unused)
                
            Returns:
                dict: Camera information
            """
            if not self.camera:
                raise ValueError("Not connected to a camera. Call connect_camera first.")
            
            try:
                info = await self.camera.getBasicInfo()
                device_info = info.get("device_info", {})
                
                return {
                    "status": "success",
                    "model": device_info.get("device_model", "Unknown"),
                    "serial_number": device_info.get("device_id", ""),
                    "firmware_version": info.get("firmware_version", ""),
                    "mac_address": info.get("mac", ""),
                    "ip_address": self.camera.host,
                    "wifi_signal": info.get("signal_level", 0),
                    "wifi_ssid": info.get("ssid", "")
                }
            except Exception as e:
                logger.error(f"Failed to get camera info: {str(e)}")
                return {"status": "error", "message": str(e)}
        
        @self.mcp.tool()
        async def get_camera_status(params: dict = None) -> Dict[str, Any]:
            """
            Get the current status of the camera.
            
            Args:
                params: Dictionary containing any parameters (unused)
                
            Returns:
                dict: Current camera status
            """
            if not self.camera:
                return {"status": "error", "message": "Not connected to a camera. Call connect_camera first."}
            
            try:
                info = await self.camera.getBasicInfo()
                motion_detection = await self.camera.getMotionDetection()
                led_status = await self.camera.getLED()
                
                return {
                    "status": "success",
                    "online": True,
                    "recording": info.get("record", {}).get("recording", False),
                    "motion_detected": motion_detection.get("enabled", False),
                    "privacy_mode": info.get("lens_mask", {}).get("lens_mask", False),
                    "led_enabled": led_status.get("enabled", True),
                    "uptime": info.get("device_info", {}).get("up_time", 0),
                    "storage": {
                        "total": 0,  # These would come from camera.getStorageInfo()
                        "used": 0,
                        "free": 0
                    }
                }
            except Exception as e:
                error_msg = f"Failed to get camera status: {str(e)}"
                logger.error(error_msg)
                return {"status": "error", "message": error_msg}
        
        # PTZ control
        @self.mcp.tool()
        async def move_ptz(params: dict) -> Dict[str, Any]:
            """
            Move the camera PTZ (Pan-Tilt-Zoom).
            
            Args:
                params: Dictionary containing PTZ parameters:
                    - pan: Pan position (-1.0 to 1.0, default: 0.0)
                    - tilt: Tilt position (-1.0 to 1.0, default: 0.0)
                    - zoom: Zoom level (0.0 to 1.0, default: 0.0)
                
            Returns:
                dict: Operation status
            """
            if not self.camera:
                return {"status": "error", "message": "Not connected to a camera. Call connect_camera first."}
            
            try:
                pan = float(params.get("pan", 0.0))
                tilt = float(params.get("tilt", 0.0))
                zoom = float(params.get("zoom", 0.0))
                
                # Validate parameter ranges
                if not (-1.0 <= pan <= 1.0):
                    raise ValueError("Pan value must be between -1.0 and 1.0")
                if not (-1.0 <= tilt <= 1.0):
                    raise ValueError("Tilt value must be between -1.0 and 1.0")
                if not (0.0 <= zoom <= 1.0):
                    raise ValueError("Zoom value must be between 0.0 and 1.0")
                
                # Move the camera PTZ
                if pan != 0 or tilt != 0:
                    await self.camera.moveMotor(pan, tilt)
                if zoom != 0:
                    await self.camera.zoom(zoom)
                
                return {
                    "status": "success", 
                    "message": "PTZ movement completed",
                    "position": {"pan": pan, "tilt": tilt, "zoom": zoom}
                }
            except Exception as e:
                logger.error(f"Failed to move PTZ: {str(e)}")
                return {"status": "error", "message": str(e)}
        
        # Stream management
        @self.mcp.tool()
        async def get_stream_url(quality: str = "hd") -> StreamInfo:
            """
            Get the RTSP stream URL.
            
            Args:
                quality: Stream quality (hd/sd)
                
            Returns:
                StreamInfo: Stream information
            """
            if not self.camera:
                raise ValueError("Not connected to a camera. Call connect_camera first.")
            
            try:
                # In a real implementation, this would get the actual RTSP URL from the camera
                # This is a simplified version that assumes a standard RTSP URL format
                rtsp_url = f"rtsp://{self.camera.host}/stream1"
                
                return StreamInfo(
                    url=rtsp_url,
                    type="rtsp",
                    quality=quality
                )
            except Exception as e:
                logger.error(f"Failed to get stream URL: {str(e)}")
                raise
        
        # Motion detection control
        @self.mcp.tool()
        async def set_motion_detection(
            enabled: bool = Field(..., description="Enable or disable motion detection")
        ) -> Dict[str, Any]:
            """
            Enable or disable motion detection.
            
            Args:
                enabled: Whether to enable motion detection
                
            Returns:
                dict: Operation status
            """
            if not self.camera:
                raise ValueError("Not connected to a camera. Call connect_camera first.")
            
            try:
                await self.camera.setMotionDetection(enabled)
                return {"status": "success", "motion_detection": enabled}
            except Exception as e:
                logger.error(f"Failed to set motion detection: {str(e)}")
                return {"status": "error", "message": str(e)}
        
        # LED control
        @self.mcp.tool()
        async def set_led_enabled(
            enabled: bool = Field(..., description="Enable or disable the camera LED")
        ) -> Dict[str, Any]:
            """
            Enable or disable the camera LED.
            
            Args:
                enabled: Whether to enable the LED
                
            Returns:
                dict: Operation status
            """
            if not self.camera:
                raise ValueError("Not connected to a camera. Call connect_camera first.")
            
            try:
                await self.camera.setLED(enabled)
                return {"status": "success", "led_enabled": enabled}
            except Exception as e:
                logger.error(f"Failed to set LED state: {str(e)}")
                return {"status": "error", "message": str(e)}
        
        # Privacy mode control
        @self.mcp.tool()
        async def set_privacy_mode(
            enabled: bool = Field(..., description="Enable or disable privacy mode")
        ) -> Dict[str, Any]:
            """
            Enable or disable privacy mode (lens mask).
            
            Args:
                enabled: Whether to enable privacy mode
                
            Returns:
                dict: Operation status
            """
            if not self.camera:
                raise ValueError("Not connected to a camera. Call connect_camera first.")
            
            try:
                await self.camera.setPrivacyMode(enabled)
                return {"status": "success", "privacy_mode": enabled}
            except Exception as e:
                logger.error(f"Failed to set privacy mode: {str(e)}")
                return {"status": "error", "message": str(e)}
        
        # Reboot camera
        @self.mcp.tool()
        async def reboot_camera(params: Dict[str, Any] = None) -> Dict[str, Any]:
            """
            Reboot the camera.
            
            Args:
                params: Dictionary containing any parameters (unused, for API consistency)
                
            Returns:
                dict: Operation status
            """
            if not self.camera:
                raise ValueError("Not connected to a camera. Call connect_camera first.")
            
            try:
                await self.camera.reboot()
                return {"status": "success", "message": "Camera is rebooting"}
            except Exception as e:
                logger.error(f"Failed to reboot camera: {str(e)}")
                return {"status": "error", "message": str(e)}
        
        # Get camera presets
        @self.mcp.tool()
        async def get_ptz_presets() -> Dict[str, Any]:
            """
            Get all saved PTZ presets.
            
            Returns:
                dict: Dictionary of preset names and their positions
            """
            if not self.camera:
                raise ValueError("Not connected to a camera. Call connect_camera first.")
            
            try:
                presets = await self.camera.getPresets()
                return {"status": "success", "presets": presets}
            except Exception as e:
                logger.error(f"Failed to get PTZ presets: {str(e)}")
                return {"status": "error", "message": str(e)}
    
    def run(self, host: str = "0.0.0.0", port: int = 8000, stdio: bool = True):
        """
        Run the MCP server with both HTTP and stdio transports.
        
        Args:
            host: Host to bind the HTTP server to
            port: Port to bind the HTTP server to
            stdio: Enable stdio transport
        """
        # Start HTTP server
        http_server = self.mcp.create_http_server(host=host, port=port)
        
        # Start stdio server if requested
        stdio_server = None
        if stdio:
            stdio_server = self.mcp.create_stdio_server()
        
        # Run the event loop
        loop = asyncio.get_event_loop()
        
        try:
            logger.info(f"Starting MCP server on http://{host}:{port}")
            if stdio:
                logger.info("Stdio transport enabled")
            
            loop.run_forever()
        except KeyboardInterrupt:
            logger.info("Shutting down...")
        finally:
            # Clean up
            if stdio_server:
                stdio_server.close()
                loop.run_until_complete(stdio_server.wait_closed())
            
            http_server.close()
            loop.run_until_complete(http_server.wait_closed())
            
            # Close camera connection if open
            if self.camera:
                loop.run_until_complete(self.camera.close())
            
            loop.close()


def main():
    """Main entry point for the Tapo Camera MCP server."""
    import argparse
    
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Tapo Camera MCP Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind the HTTP server to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind the HTTP server to")
    parser.add_argument("--no-stdio", action="store_false", dest="stdio", 
                       help="Disable stdio transport")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()
    
    # Configure logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Create and run the server
    server = TapoCameraServer()
    
    try:
        server.run(host=args.host, port=args.port, stdio=args.stdio)
    except Exception as e:
        logger.error(f"Server error: {str(e)}", exc_info=args.debug)
        return 1
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
