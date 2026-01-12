#!/usr/bin/env python3
"""
Quick start script for Tapo Camera MCP Dashboard

This script provides easy commands to start different components of the system.
"""

import argparse
import logging
import os
import subprocess

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def run_command(cmd, description):
    """Run a command and handle errors."""
    logger.info(f"START: {description}")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        logger.info(f"SUCCESS: {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"ERROR: {description} failed: {e}")
        logger.error(f"Error output: {e.stderr}")
        return False


def start_mcp_server(debug=False):
    """Start the MCP server."""
    # Use python -c to ensure proper PyO3 initialization for Rust libraries
    import_cmd = "import sys; sys.path.insert(0, 'src'); from tapo_camera_mcp.server_v2 import main; main()"
    cmd = f'python -c "{import_cmd}" --direct'
    if debug:
        cmd += " --debug"

    logger.info("Starting MCP Server...")
    logger.info("MCP Server will be available for Claude Desktop integration")
    logger.info("Press Ctrl+C to stop the server")
    logger.info("Note: Server runs until stopped - this is normal behavior")

    try:
        # Run the server - this blocks until server exits
        result = subprocess.run(cmd, check=False, shell=True)
        if result.returncode != 0:
            logger.error(f"MCP Server exited with code {result.returncode}")
        else:
            logger.info("MCP Server exited normally")
    except KeyboardInterrupt:
        logger.info("MCP Server stopped by user")
    except Exception as e:
        logger.error(f"Error starting MCP Server: {e}", exc_info=True)


def start_dual_server():
    """Start the dual interface server (MCP + REST API)."""
    logger.info("🔄 Starting Dual Interface Server...")
    logger.info("📡 MCP Server: Available for Claude Desktop integration")
    logger.info("🌐 REST API: Available at http://localhost:8123")
    logger.info("📺 Dashboard: Available at http://localhost:7777")
    logger.info("🛑 Press Ctrl+C to stop the server")

    cmd = 'python -c "import asyncio; from src.tapo_camera_mcp.dual_server import start_dual_server; asyncio.run(start_dual_server())"'

    try:
        subprocess.run(cmd, check=False, shell=True)
    except KeyboardInterrupt:
        logger.info("🛑 Dual Server stopped")


def start_web_dashboard(port: int = 7777):
    """Start the web dashboard."""
    logger.info("Starting Web Dashboard...")
    logger.info(f"Dashboard will be available at: http://localhost:{port}")
    logger.info("Press Ctrl+C to stop the dashboard")

    try:
        # Use system Python directly - no venv needed if dependencies are installed
        # Check for PORT environment variable
        env_port = os.getenv("PORT")
        if env_port:
            port = int(env_port)
            logger.info(f"Using port from PORT environment variable: {port}")

        cmd = f"python -m tapo_camera_mcp.web.server --port {port}"
        subprocess.run(cmd, check=False, shell=True)
    except KeyboardInterrupt:
        logger.info("Web Dashboard stopped")


def test_webcam():
    """Test webcam functionality."""
    logger.info("CAMERA: Testing webcam functionality...")

    if run_command("python test_webcam_streaming.py", "Webcam test"):
        logger.info("SUCCESS: Webcam test completed successfully!")
        logger.info("STREAM: Your webcam is ready for streaming")
    else:
        logger.error("ERROR: Webcam test failed")
        logger.error("HINT: Make sure you have a USB webcam connected")


def check_dependencies():
    """Check if all dependencies are installed."""
    logger.info("CHECK: Checking dependencies...")

    try:
        import cv2

        logger.info("SUCCESS: OpenCV installed")
    except ImportError:
        logger.error("ERROR: OpenCV not installed. Run: pip install opencv-python")
        return False

    try:
        import fastapi

        logger.info("SUCCESS: FastAPI installed")
    except ImportError:
        logger.error("ERROR: FastAPI not installed. Run: pip install fastapi")
        return False

    try:
        import uvicorn

        logger.info("SUCCESS: Uvicorn installed")
    except ImportError:
        logger.error("ERROR: Uvicorn not installed. Run: pip install uvicorn")
        return False

    logger.info("SUCCESS: All dependencies are installed!")
    return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Tapo Camera MCP Quick Start")
    parser.add_argument(
        "command",
        choices=["mcp", "dashboard", "dual", "webcam", "test", "check", "both"],
        help="Command to run",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    print("Tapo Camera MCP - Quick Start")
    print("=" * 40)

    if args.command == "check":
        check_dependencies()
    elif args.command == "test":
        test_webcam()
    elif args.command == "mcp":
        start_mcp_server(args.debug)
    elif args.command == "dual":
        start_dual_server()
    elif args.command == "dashboard":
        start_web_dashboard()
    elif args.command == "webcam":
        test_webcam()
        print("\n" + "=" * 40)
        start_web_dashboard()
    elif args.command == "both":
        print("START: Starting both MCP server and web dashboard...")
        print("SERVER: MCP Server: Available for Claude Desktop")
        print("WEB: Web Dashboard: http://localhost:7777")
        print("STOP: Press Ctrl+C to stop both services")
        print("\n" + "=" * 40)

        # Start both services
        import threading

        def run_mcp():
            start_mcp_server(args.debug)

        def run_dashboard():
            start_web_dashboard()

        mcp_thread = threading.Thread(target=run_mcp)
        dashboard_thread = threading.Thread(target=run_dashboard)

        mcp_thread.start()
        dashboard_thread.start()

        try:
            mcp_thread.join()
            dashboard_thread.join()
        except KeyboardInterrupt:
            logger.info("🛑 Both services stopped")


if __name__ == "__main__":
    main()
