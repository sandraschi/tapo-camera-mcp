"""
Tapo-Camera-MCP - FastMCP 2.10 server for controlling TP-Link Tapo cameras.
"""
import asyncio
import logging
from typing import Any, Dict, Optional, Set

import aiohttp
from fastmcp import FastMCP, McpMessage

from .exceptions import TapoCameraError, AuthenticationError, ConnectionError
from .models import CameraConfig, CameraStatus, CameraInfo, PTZPosition, MotionEvent

logger = logging.getLogger(__name__)

class TapoCameraMCP(FastMCP):
    """Tapo Camera MCP server implementation."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, **kwargs):
        """Initialize the Tapo Camera MCP server."""
        kwargs.setdefault("name", "Tapo-Camera-MCP")
        kwargs.setdefault("version", "0.1.0")
        
        super().__init__(**kwargs)
        
        # Initialize configuration
        self.config = CameraConfig(**(config or {}))
        
        # Camera connection state
        self._session: Optional[aiohttp.ClientSession] = None
        self._is_connected = False
        self._motion_detected = False
        self._motion_listeners: Set[callable] = set()
        
        # Register message handlers
        self._register_handlers()
    
    def _register_handlers(self):
        """Register all message handlers."""
        handlers = {
            "camera_connect": self.handle_connect,
            "camera_disconnect": self.handle_disconnect,
            "camera_info": self.handle_get_info,
            "camera_status": self.handle_get_status,
            "camera_config": self.handle_get_config,
            "camera_update_config": self.handle_update_config,
            "camera_reboot": self.handle_reboot,
            "stream_start": self.handle_start_stream,
            "stream_stop": self.handle_stop_stream,
            "ptz_move": self.handle_ptz_move,
            "ptz_preset": self.handle_ptz_preset,
            "ptz_home": self.handle_ptz_home,
            "motion_detection": self.handle_motion_detection,
            "recording_start": self.handle_start_recording,
            "recording_stop": self.handle_stop_recording,
            "snapshot": self.handle_snapshot,
        }
        
        for msg_type, handler in handlers.items():
            self.register_message_handler(msg_type, handler)
    
    # ===== Connection Management =====
    
    async def connect(self) -> None:
        """Connect to the Tapo camera."""
        if self._is_connected:
            return
        
        try:
            self._session = aiohttp.ClientSession(
                base_url=f"http{'s' if self.config.use_https else ''}://{self.config.host}:{self.config.port}",
                timeout=aiohttp.ClientTimeout(total=self.config.timeout),
                connector=aiohttp.TCPConnector(ssl=self.config.verify_ssl)
            )
            
            # Test connection
            await self._send_request("POST", "/")
            
            self._is_connected = True
            logger.info(f"Connected to camera at {self.config.host}")
            
        except aiohttp.ClientError as e:
            await self._cleanup()
            raise ConnectionError(f"Failed to connect to camera: {str(e)}")
        except Exception as e:
            await self._cleanup()
            if "401" in str(e):
                raise AuthenticationError("Invalid username or password")
            raise ConnectionError(f"Failed to connect to camera: {str(e)}")
    
    async def disconnect(self) -> None:
        """Disconnect from the Tapo camera."""
        await self._cleanup()
        logger.info(f"Disconnected from camera at {self.config.host}")
    
    async def _cleanup(self):
        """Clean up resources."""
        if self._session and not self._session.closed:
            await self._session.close()
        self._session = None
        self._is_connected = False
    
    async def _send_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Send an authenticated request to the camera."""
        if not self._session or self._session.closed:
            raise ConnectionError("Not connected to camera")
        
        try:
            # Add authentication
            auth = aiohttp.BasicAuth(self.config.username, self.config.password)
            kwargs.setdefault("auth", auth)
            
            # Send request
            async with self._session.request(method, endpoint, **kwargs) as response:
                response.raise_for_status()
                return await response.json()
                
        except aiohttp.ClientResponseError as e:
            if e.status == 401:
                raise AuthenticationError("Invalid username or password")
            raise ConnectionError(f"Camera API error: {str(e)}")
        except aiohttp.ClientError as e:
            raise ConnectionError(f"Network error: {str(e)}")
    
    # ===== Message Handlers =====
    
    async def handle_connect(self, message: McpMessage) -> Dict[str, Any]:
        """Handle camera connect request."""
        try:
            await self.connect()
            return {"status": "connected", "message": f"Connected to camera at {self.config.host}"}
        except Exception as e:
            raise ConnectionError(f"Failed to connect to camera: {str(e)}")
    
    async def handle_disconnect(self, message: McpMessage) -> Dict[str, Any]:
        """Handle camera disconnect request."""
        try:
            await self.disconnect()
            return {"status": "disconnected", "message": "Disconnected from camera"}
        except Exception as e:
            raise ConnectionError(f"Failed to disconnect from camera: {str(e)}")
    
    async def handle_get_info(self, message: McpMessage) -> Dict[str, Any]:
        """Handle get camera info request."""
        if not self._is_connected:
            await self.connect()
        
        try:
            # In a real implementation, this would fetch actual camera info
            info = CameraInfo(
                model="Tapo C200",
                serial_number="T1234567890",
                mac_address="00:11:22:33:44:55",
                firmware_version="1.0.0",
                hardware_version="1.0",
                uptime=3600,
                ip_address=self.config.host,
                wifi_signal=80,
                wifi_ssid="MyWiFi"
            )
            return info.dict()
            
        except Exception as e:
            raise ConnectionError(f"Failed to get camera info: {str(e)}")
    
    async def handle_get_status(self, message: McpMessage) -> Dict[str, Any]:
        """Handle get camera status request."""
        if not self._is_connected:
            await self.connect()
        
        try:
            status = CameraStatus(
                online=True,
                recording=False,
                motion_detected=self._motion_detected,
                audio_detected=False,
                privacy_mode=False,
                led_enabled=True,
                firmware_version="1.0.0",
                uptime=3600,
                storage={"total": 64000000000, "used": 3200000000, "free": 60800000000}
            )
            return status.dict()
            
        except Exception as e:
            raise ConnectionError(f"Failed to get camera status: {str(e)}")
    
    async def handle_get_config(self, message: McpMessage) -> Dict[str, Any]:
        """Handle get camera config request."""
        return self.config.dict()
    
    async def handle_update_config(self, message: McpMessage) -> Dict[str, Any]:
        """Handle update camera config request."""
        try:
            update_data = message.data.get("config", {})
            self.config = CameraConfig(**{**self.config.dict(), **update_data})
            
            if self._is_connected:
                await self.disconnect()
                await self.connect()
            
            return {"status": "success", "message": "Configuration updated"}
            
        except Exception as e:
            raise ConnectionError(f"Failed to update config: {str(e)}")
    
    async def handle_reboot(self, message: McpMessage) -> Dict[str, Any]:
        """Handle camera reboot request."""
        if not self._is_connected:
            await self.connect()
        
        try:
            # In a real implementation, this would send a reboot command
            await asyncio.sleep(1)  # Simulate reboot delay
            await self.disconnect()
            
            return {"status": "success", "message": "Camera is rebooting"}
            
        except Exception as e:
            raise ConnectionError(f"Failed to reboot camera: {str(e)}")
    
    async def handle_start_stream(self, message: McpMessage) -> Dict[str, Any]:
        """Handle start stream request."""
        if not self._is_connected:
            await self.connect()
        
        stream_id = message.data.get("stream_id", "default")
        stream_type = message.data.get("stream_type", self.config.stream_type)
        
        try:
            # In a real implementation, this would start a video stream
            stream_url = f"rtsp://{self.config.host}:{self.config.rtsp_port}/stream1"
            
            return {
                "status": "success",
                "stream_id": stream_id,
                "stream_type": stream_type,
                "stream_url": stream_url
            }
            
        except Exception as e:
            raise ConnectionError(f"Failed to start stream: {str(e)}")
    
    async def handle_stop_stream(self, message: McpMessage) -> Dict[str, Any]:
        """Handle stop stream request."""
        stream_id = message.data.get("stream_id", "all")
        return {"status": "success", "message": f"Stream {stream_id} stopped"}
    
    async def handle_ptz_move(self, message: McpMessage) -> Dict[str, Any]:
        """Handle PTZ move request."""
        if not self._is_connected:
            await self.connect()
        
        try:
            direction = message.data.get("direction")
            speed = message.data.get("speed", 0.5)
            
            # In a real implementation, this would move the camera
            return {"status": "success", "message": f"PTZ moved {direction} at speed {speed}"}
            
        except Exception as e:
            raise ConnectionError(f"Failed to move PTZ: {str(e)}")
    
    async def handle_ptz_preset(self, message: McpMessage) -> Dict[str, Any]:
        """Handle PTZ preset request."""
        action = message.data.get("action", "list")
        preset_name = message.data.get("preset_name")
        
        try:
            if action == "list":
                return {"status": "success", "presets": [
                    {"name": "Home", "position": {"pan": 0, "tilt": 0, "zoom": 0}},
                    {"name": "Left", "position": {"pan": -0.5, "tilt": 0, "zoom": 0}},
                    {"name": "Right", "position": {"pan": 0.5, "tilt": 0, "zoom": 0}}
                ]}
            else:
                return {"status": "success", "message": f"Preset {action} {preset_name}"}
                
        except Exception as e:
            raise ConnectionError(f"Failed to handle PTZ preset: {str(e)}")
    
    async def handle_ptz_home(self, message: McpMessage) -> Dict[str, Any]:
        """Handle PTZ home position request."""
        if not self._is_connected:
            await self.connect()
        
        try:
            # In a real implementation, this would move the camera to home position
            return {"status": "success", "message": "PTZ moved to home position"}
            
        except Exception as e:
            raise ConnectionError(f"Failed to move PTZ to home: {str(e)}")
    
    async def handle_motion_detection(self, message: McpMessage) -> Dict[str, Any]:
        """Handle motion detection request."""
        action = message.data.get("action", "status")
        
        try:
            if action == "start":
                self._motion_detected = True
                return {"status": "success", "message": "Motion detection started"}
                
            elif action == "stop":
                self._motion_detected = False
                return {"status": "success", "message": "Motion detection stopped"}
                
            else:  # status
                return {
                    "status": "success",
                    "enabled": self._motion_detected,
                    "motion_detected": self._motion_detected,
                    "sensitivity": self.config.motion_sensitivity
                }
                
        except Exception as e:
            raise ConnectionError(f"Failed to handle motion detection: {str(e)}")
    
    async def handle_start_recording(self, message: McpMessage) -> Dict[str, Any]:
        """Handle start recording request."""
        recording_id = message.data.get("recording_id", f"rec_{int(time.time())}")
        
        try:
            # In a real implementation, this would start recording
            return {
                "status": "success",
                "recording_id": recording_id,
                "start_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            raise ConnectionError(f"Failed to start recording: {str(e)}")
    
    async def handle_stop_recording(self, message: McpMessage) -> Dict[str, Any]:
        """Handle stop recording request."""
        recording_id = message.data.get("recording_id", "all")
        return {"status": "success", "message": f"Stopped recording {recording_id}"}
    
    async def handle_snapshot(self, message: McpMessage) -> Dict[str, Any]:
        """Handle snapshot request."""
        if not self._is_connected:
            await self.connect()
        
        try:
            # In a real implementation, this would capture a snapshot
            snapshot_data = b""  # Placeholder for actual image data
            
            return {
                "status": "success",
                "snapshot": f"data:image/jpeg;base64,{base64.b64encode(snapshot_data).decode()}",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            raise ConnectionError(f"Failed to capture snapshot: {str(e)}")

def create_app(config: Optional[Dict[str, Any]] = None) -> TapoCameraMCP:
    """Create and configure a Tapo Camera MCP application."""
    return TapoCameraMCP(config=config)

async def main():
    """Run the Tapo Camera MCP server."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Tapo Camera MCP Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("-p", "--port", type=int, default=8000, help="Port to listen on")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    args = parser.parse_args()
    
    app = create_app()
    
    try:
        await app.start(host=args.host, port=args.port, debug=args.debug)
        logger.info(f"Tapo Camera MCP server started on {args.host}:{args.port}")
        
        while True:
            await asyncio.sleep(3600)  # Run forever
            
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.exception("Server error:")
    finally:
        await app.stop()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
