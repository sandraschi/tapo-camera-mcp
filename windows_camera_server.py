#!/usr/bin/env python3
"""
Windows USB Camera Server for Tapo Camera MCP.

This server runs on Windows host and provides HTTP access to USB cameras
that can't be accessed from Docker containers on Windows.
"""

import asyncio
import logging
import os
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import cv2
import numpy as np
from PIL import Image
import io

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from tapo_camera_mcp.utils.logging import setup_logging

# Suppress OpenCV warnings
os.environ["OPENCV_LOG_LEVEL"] = "ERROR"
cv2.setLogLevel(0)

logger = logging.getLogger(__name__)

class CameraManager:
    """Manages USB cameras on Windows."""

    def __init__(self):
        self.cameras = {}
        self.frames = {}
        self.capture_threads = {}
        self.lock = threading.Lock()

    def add_camera(self, camera_id: int, name: str):
        """Add a camera by device ID."""
        with self.lock:
            if camera_id in self.cameras:
                logger.warning(f"Camera {camera_id} already exists")
                return

            cap = cv2.VideoCapture(camera_id)
            if not cap.isOpened():
                logger.error(f"Failed to open camera {camera_id}")
                return

            self.cameras[camera_id] = {
                'name': name,
                'cap': cap,
                'last_frame': None,
                'last_frame_time': 0,
                'thread': None,
                'active': True
            }

            # Start capture thread
            thread = threading.Thread(
                target=self._capture_loop,
                args=(camera_id,),
                daemon=True
            )
            thread.start()
            self.capture_threads[camera_id] = thread

            logger.info(f"Added camera {camera_id}: {name}")

    def _capture_loop(self, camera_id: int):
        """Background capture loop for a camera."""
        camera = self.cameras.get(camera_id)
        if not camera:
            return

        cap = camera['cap']
        while camera['active']:
            try:
                ret, frame = cap.read()
                if ret:
                    # Convert BGR to RGB and store
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    pil_image = Image.fromarray(rgb_frame)

                    with self.lock:
                        camera['last_frame'] = pil_image
                        camera['last_frame_time'] = time.time()
                else:
                    logger.warning(f"No frame from camera {camera_id}")
            except Exception as e:
                logger.error(f"Error capturing from camera {camera_id}: {e}")

            time.sleep(0.1)  # 10 FPS

    def get_snapshot(self, camera_id: int):
        """Get snapshot from camera."""
        with self.lock:
            camera = self.cameras.get(camera_id)
            if not camera or not camera['last_frame']:
                return None
            return camera['last_frame'].copy()

    def get_mjpeg_stream(self, camera_id: int):
        """Get MJPEG stream generator for camera."""
        def generate():
            while True:
                frame = self.get_snapshot(camera_id)
                if frame:
                    # Convert to JPEG
                    buf = io.BytesIO()
                    frame.save(buf, format='JPEG', quality=80)
                    jpeg_data = buf.getvalue()

                    # MJPEG frame
                    yield b'--frame\r\n'
                    yield b'Content-Type: image/jpeg\r\n'
                    yield f'Content-Length: {len(jpeg_data)}\r\n\r\n'.encode()
                    yield jpeg_data
                    yield b'\r\n'

                time.sleep(0.1)  # 10 FPS

        return generate()

    def close_camera(self, camera_id: int):
        """Close a camera."""
        with self.lock:
            camera = self.cameras.get(camera_id)
            if camera:
                camera['active'] = False
                if camera['cap']:
                    camera['cap'].release()
                logger.info(f"Closed camera {camera_id}")

    def close_all(self):
        """Close all cameras."""
        for camera_id in list(self.cameras.keys()):
            self.close_camera(camera_id)

class CameraHTTPRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for camera server."""

    def __init__(self, *args, camera_manager=None, **kwargs):
        self.camera_manager = camera_manager
        super().__init__(*args, **kwargs)

    def do_GET(self):
        """Handle GET requests."""
        parsed_path = urlparse(self.path)
        path_parts = parsed_path.path.strip('/').split('/')

        if len(path_parts) >= 2 and path_parts[0] == 'camera':
            try:
                camera_id = int(path_parts[1])

                if len(path_parts) >= 3 and path_parts[2] == 'snapshot':
                    # Get snapshot
                    frame = self.camera_manager.get_snapshot(camera_id)
                    if frame:
                        buf = io.BytesIO()
                        frame.save(buf, format='JPEG', quality=80)
                        jpeg_data = buf.getvalue()

                        self.send_response(200)
                        self.send_header('Content-Type', 'image/jpeg')
                        self.send_header('Content-Length', str(len(jpeg_data)))
                        self.end_headers()
                        self.wfile.write(jpeg_data)
                    else:
                        self.send_error(404, "No frame available")

                elif len(path_parts) >= 3 and path_parts[2] == 'mjpeg':
                    # Get MJPEG stream
                    self.send_response(200)
                    self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=frame')
                    self.send_header('Cache-Control', 'no-cache')
                    self.end_headers()

                    try:
                        for frame_data in self.camera_manager.get_mjpeg_stream(camera_id):
                            self.wfile.write(frame_data)
                    except (BrokenPipeError, ConnectionResetError):
                        # Client disconnected
                        pass

                else:
                    self.send_error(404, "Invalid endpoint")

            except (ValueError, IndexError):
                self.send_error(400, "Invalid camera ID")

        elif parsed_path.path == '/status':
            # Status endpoint
            status = {
                'cameras': {}
            }

            for cam_id, camera in self.camera_manager.cameras.items():
                status['cameras'][str(cam_id)] = {
                    'name': camera['name'],
                    'active': camera['active'],
                    'has_frame': camera['last_frame'] is not None,
                    'last_frame_time': camera['last_frame_time']
                }

            import json
            response = json.dumps(status).encode()

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(response)))
            self.end_headers()
            self.wfile.write(response)

        else:
            self.send_error(404, "Not found")

    def log_message(self, format, *args):
        """Override to use our logger."""
        logger.info(format % args)

def run_server(camera_manager, port=7778):
    """Run the HTTP server."""
    def handler_class(*args, **kwargs):
        return CameraHTTPRequestHandler(*args, camera_manager=camera_manager, **kwargs)

    server = HTTPServer(('localhost', port), handler_class)
    logger.info(f"Windows Camera Server started on http://localhost:{port}")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Server stopped")
    finally:
        camera_manager.close_all()

async def main():
    """Main function."""
    setup_logging()
    logger.info("Starting Windows USB Camera Server")

    camera_manager = CameraManager()

    # Add cameras (microscope on 0, webcam on 1)
    camera_manager.add_camera(0, "Microscope Camera")
    camera_manager.add_camera(1, "Webcam Camera")

    # Give cameras time to initialize
    await asyncio.sleep(2)

    # Check which cameras are working
    for cam_id, camera in camera_manager.cameras.items():
        if camera['last_frame']:
            logger.info(f"Camera {cam_id} ({camera['name']}) is working")
        else:
            logger.warning(f"Camera {cam_id} ({camera['name']}) is not providing frames")

    # Start HTTP server in a thread
    server_thread = threading.Thread(
        target=run_server,
        args=(camera_manager, 7778),
        daemon=True
    )
    server_thread.start()

    logger.info("Windows Camera Server running. Press Ctrl+C to stop.")
    logger.info("Available endpoints:")
    logger.info("  GET /status - Camera status")
    logger.info("  GET /camera/0/snapshot - Microscope snapshot")
    logger.info("  GET /camera/1/snapshot - Webcam snapshot")
    logger.info("  GET /camera/0/mjpeg - Microscope MJPEG stream")
    logger.info("  GET /camera/1/mjpeg - Webcam MJPEG stream")

    try:
        # Keep running
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping...")
    finally:
        camera_manager.close_all()

if __name__ == '__main__':
    asyncio.run(main())



