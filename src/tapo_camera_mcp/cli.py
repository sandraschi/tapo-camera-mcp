"""
Command-line interface for Tapo Camera MCP.
"""
import argparse
import asyncio
import json
import sys
from typing import Dict, Any, Optional

from .server import TapoCameraMCP
from .exceptions import TapoCameraError

# ANSI color codes
COLOR_RED = "\033[91m"
COLOR_GREEN = "\033[92m"
COLOR_YELLOW = "\033[93m"
COLOR_BLUE = "\033[94m"
COLOR_END = "\033[0m"

def print_success(message: str) -> None:
    """Print a success message."""
    print(f"{COLOR_GREEN}✓ {message}{COLOR_END}")

def print_error(message: str) -> None:
    """Print an error message."""
    print(f"{COLOR_RED}✗ {message}{COLOR_END}", file=sys.stderr)

def print_warning(message: str) -> None:
    """Print a warning message."""
    print(f"{COLOR_YELLOW}⚠ {message}{COLOR_END}")

def print_info(message: str) -> None:
    """Print an info message."""
    print(f"{COLOR_BLUE}ℹ {message}{COLOR_END}")

class TapoCameraCLI:
    """Command-line interface for Tapo Camera MCP."""
    
    def __init__(self):
        self.parser = self._create_parser()
        self.app = None
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """Create the argument parser."""
        parser = argparse.ArgumentParser(description="Tapo Camera MCP CLI")
        parser.add_argument("--config", "-c", help="Path to config file")
        parser.add_argument("--host", help="Camera hostname or IP address")
        parser.add_argument("--port", type=int, help="Camera port")
        parser.add_argument("--username", help="Camera username")
        parser.add_argument("--password", help="Camera password")
        parser.add_argument("--debug", action="store_true", help="Enable debug output")
        
        # Subcommands
        subparsers = parser.add_subparsers(dest="command", required=True)
        
        # Server commands
        server_parser = subparsers.add_parser("serve", help="Start the MCP server")
        server_parser.add_argument("--bind", default="0.0.0.0", help="Host to bind to")
        server_parser.add_argument("--mcp-port", type=int, default=8000, help="Port to listen on")
        
        # Camera commands
        camera_parser = subparsers.add_parser("camera", help="Camera operations")
        camera_subparsers = camera_parser.add_subparsers(dest="camera_command", required=True)
        
        # Camera info
        camera_subparsers.add_parser("info", help="Get camera information")
        
        # Camera status
        camera_subparsers.add_parser("status", help="Get camera status")
        
        # Camera config
        config_parser = camera_subparsers.add_parser("config", help="Manage camera configuration")
        config_parser.add_argument("action", choices=["get", "set"], help="Action to perform")
        config_parser.add_argument("--key", help="Configuration key to get/set")
        config_parser.add_argument("--value", help="Value to set")
        
        # PTZ commands
        ptz_parser = camera_subparsers.add_parser("ptz", help="PTZ control")
        ptz_parser.add_argument("action", choices=["move", "preset", "home"], help="PTZ action")
        ptz_parser.add_argument("--direction", choices=["up", "down", "left", "right", "stop"], 
                              help="Direction to move")
        ptz_parser.add_argument("--speed", type=float, default=0.5, help="Movement speed (0.0-1.0)")
        ptz_parser.add_argument("--preset-action", choices=["list", "set", "goto", "remove"], 
                               help="Preset action")
        ptz_parser.add_argument("--preset-name", help="Preset name")
        
        # Stream commands
        stream_parser = camera_subparsers.add_parser("stream", help="Stream operations")
        stream_parser.add_argument("action", choices=["start", "stop"], help="Action to perform")
        stream_parser.add_argument("--stream-id", default="default", help="Stream ID")
        stream_parser.add_argument("--type", choices=["rtsp", "rtmp", "hls"], 
                                 help="Stream type")
        stream_parser.add_argument("--quality", choices=["high", "medium", "low"], 
                                 help="Stream quality")
        
        # Motion detection
        motion_parser = camera_subparsers.add_parser("motion", help="Motion detection")
        motion_parser.add_argument("action", choices=["start", "stop", "status"], 
                                 help="Action to perform")
        
        # Recording
        record_parser = camera_subparsers.add_parser("record", help="Recording operations")
        record_parser.add_argument("action", choices=["start", "stop"], help="Action to perform")
        record_parser.add_argument("--recording-id", help="Recording ID")
        record_parser.add_argument("--duration", type=int, help="Recording duration in seconds")
        
        # Snapshot
        camera_subparsers.add_parser("snapshot", help="Take a snapshot")
        
        return parser
    
    async def run(self, args=None):
        """Run the CLI."""
        if args is None:
            args = self.parser.parse_args()
        
        try:
            # Initialize the MCP application
            config = {}
            if args.config:
                with open(args.config) as f:
                    import yaml
                    config = yaml.safe_load(f)
            
            # Override config with command-line arguments
            if args.host:
                config["host"] = args.host
            if args.port:
                config["port"] = args.port
            if args.username:
                config["username"] = args.username
            if args.password:
                config["password"] = args.password
            
            self.app = TapoCameraMCP(config=config)
            
            # Connect to the camera for camera commands
            if args.command == "camera" and args.camera_command != "info":
                await self.app.connect()
            
            # Handle commands
            if args.command == "serve":
                await self._handle_serve(args)
            elif args.command == "camera":
                await self._handle_camera(args)
            else:
                self.parser.print_help()
                return 1
                
        except TapoCameraError as e:
            print_error(str(e))
            return 1
        except Exception as e:
            if args.debug:
                import traceback
                traceback.print_exc()
            print_error(f"An error occurred: {str(e)}")
            return 1
        finally:
            if hasattr(self, 'app') and self.app:
                await self.app.disconnect()
        
        return 0
    
    async def _handle_serve(self, args):
        """Handle the serve command."""
        print_info(f"Starting Tapo Camera MCP server on {args.bind}:{args.mcp_port}")
        await self.app.start(host=args.bind, port=args.mcp_port)
        
        try:
            while True:
                await asyncio.sleep(3600)  # Run forever
        except KeyboardInterrupt:
            print_info("Shutting down...")
            await self.app.stop()
    
    async def _handle_camera(self, args):
        """Handle camera commands."""
        if args.camera_command == "info":
            info = await self.app.handle_get_info(None)
            self._print_json(info)
            
        elif args.camera_command == "status":
            status = await self.app.handle_get_status(None)
            self._print_json(status)
            
        elif args.camera_command == "config":
            if args.action == "get":
                if args.key:
                    config = await self.app.handle_get_config(None)
                    self._print_json(config.get(args.key))
                else:
                    config = await self.app.handle_get_config(None)
                    self._print_json(config)
            else:  # set
                if not args.key or args.value is None:
                    print_error("Both --key and --value are required for set operation")
                    return
                
                update_data = {args.key: args.value}
                result = await self.app.handle_update_config(
                    McpMessage(type="camera_update_config", data={"config": update_data})
                )
                print_success("Configuration updated")
                self._print_json(result)
                
        elif args.camera_command == "ptz":
            if args.action == "move":
                if not args.direction:
                    print_error("--direction is required for move action")
                    return
                    
                result = await self.app.handle_ptz_move(
                    McpMessage(type="ptz_move", data={
                        "direction": args.direction,
                        "speed": args.speed
                    })
                )
                print_success(f"PTZ moved {args.direction}")
                self._print_json(result)
                
            elif args.action == "preset":
                if not args.preset_action:
                    print_error("Preset action is required")
                    return
                    
                result = await self.app.handle_ptz_preset(
                    McpMessage(type="ptz_preset", data={
                        "action": args.preset_action,
                        "preset_name": args.preset_name
                    })
                )
                print_success(f"PTZ preset {args.preset_action} completed")
                self._print_json(result)
                
            elif args.action == "home":
                result = await self.app.handle_ptz_home(None)
                print_success("PTZ moved to home position")
                self._print_json(result)
                
        elif args.camera_command == "stream":
            if args.action == "start":
                result = await self.app.handle_start_stream(
                    McpMessage(type="stream_start", data={
                        "stream_id": args.stream_id,
                        "stream_type": args.type,
                        "quality": args.quality
                    })
                )
                print_success(f"Stream {args.stream_id} started")
                print(f"Stream URL: {result.get('stream_url')}")
                
            elif args.action == "stop":
                result = await self.app.handle_stop_stream(
                    McpMessage(type="stream_stop", data={"stream_id": args.stream_id})
                )
                print_success(f"Stream {args.stream_id} stopped")
                self._print_json(result)
                
        elif args.camera_command == "motion":
            result = await self.app.handle_motion_detection(
                McpMessage(type="motion_detection", data={"action": args.action})
            )
            print_success(f"Motion detection {args.action}ed")
            self._print_json(result)
            
        elif args.camera_command == "record":
            if args.action == "start":
                result = await self.app.handle_start_recording(
                    McpMessage(type="recording_start", data={
                        "recording_id": args.recording_id,
                        "duration": args.duration
                    })
                )
                print_success(f"Recording started with ID: {result.get('recording_id')}")
                self._print_json(result)
                
            elif args.action == "stop":
                result = await self.app.handle_stop_recording(
                    McpMessage(type="recording_stop", data={"recording_id": args.recording_id})
                )
                print_success("Recording stopped")
                self._print_json(result)
                
        elif args.camera_command == "snapshot":
            result = await self.app.handle_snapshot(None)
            print_success("Snapshot taken")
            
            # Save snapshot to file
            if "snapshot" in result and result["snapshot"].startswith("data:image"):
                import base64
                from datetime import datetime
                
                # Extract image data
                img_data = result["snapshot"].split(",", 1)[1]
                img_bytes = base64.b64decode(img_data)
                
                # Generate filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"snapshot_{timestamp}.jpg"
                
                # Save to file
                with open(filename, "wb") as f:
                    f.write(img_bytes)
                
                print(f"Snapshot saved to {filename}")
            
            self._print_json({"timestamp": result.get("timestamp")})
    
    def _print_json(self, data: Any) -> None:
        """Print data as formatted JSON."""
        if data is None:
            return
            
        if isinstance(data, (dict, list)):
            print(json.dumps(data, indent=2, default=str))
        else:
            print(data)

def main():
    """Entry point for the CLI."""
    cli = TapoCameraCLI()
    return asyncio.run(cli.run())

if __name__ == "__main__":
    sys.exit(main())
