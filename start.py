#!/usr/bin/env python3
"""
Quick start script for Tapo Camera MCP Dashboard

This script provides easy commands to start different components of the system.
"""

import sys
import subprocess
import asyncio
import argparse
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_command(cmd, description):
    """Run a command and handle errors."""
    logger.info(f"🚀 {description}")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        logger.info(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ {description} failed: {e}")
        logger.error(f"Error output: {e.stderr}")
        return False

def start_mcp_server(debug=False):
    """Start the MCP server."""
    cmd = f"python -m tapo_camera_mcp.server_v2 --direct"
    if debug:
        cmd += " --debug"
    
    logger.info("🔧 Starting MCP Server...")
    logger.info("📡 MCP Server will be available for Claude Desktop integration")
    logger.info("🛑 Press Ctrl+C to stop the server")
    
    try:
        subprocess.run(cmd, shell=True)
    except KeyboardInterrupt:
        logger.info("🛑 MCP Server stopped")

def start_web_dashboard():
    """Start the web dashboard."""
    logger.info("🌐 Starting Web Dashboard...")
    logger.info("📺 Dashboard will be available at: http://localhost:7777")
    logger.info("🛑 Press Ctrl+C to stop the dashboard")
    
    try:
        subprocess.run("python -m tapo_camera_mcp.web.server", shell=True)
    except KeyboardInterrupt:
        logger.info("🛑 Web Dashboard stopped")

def test_webcam():
    """Test webcam functionality."""
    logger.info("📹 Testing webcam functionality...")
    
    if run_command("python test_webcam_streaming.py", "Webcam test"):
        logger.info("✅ Webcam test completed successfully!")
        logger.info("🎥 Your webcam is ready for streaming")
    else:
        logger.error("❌ Webcam test failed")
        logger.error("💡 Make sure you have a USB webcam connected")

def check_dependencies():
    """Check if all dependencies are installed."""
    logger.info("🔍 Checking dependencies...")
    
    try:
        import cv2
        logger.info("✅ OpenCV installed")
    except ImportError:
        logger.error("❌ OpenCV not installed. Run: pip install opencv-python")
        return False
    
    try:
        import fastapi
        logger.info("✅ FastAPI installed")
    except ImportError:
        logger.error("❌ FastAPI not installed. Run: pip install fastapi")
        return False
    
    try:
        import uvicorn
        logger.info("✅ Uvicorn installed")
    except ImportError:
        logger.error("❌ Uvicorn not installed. Run: pip install uvicorn")
        return False
    
    logger.info("✅ All dependencies are installed!")
    return True

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Tapo Camera MCP Quick Start")
    parser.add_argument("command", choices=[
        "mcp", "dashboard", "webcam", "test", "check", "both"
    ], help="Command to run")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()
    
    print("🎥 Tapo Camera MCP - Quick Start")
    print("=" * 40)
    
    if args.command == "check":
        check_dependencies()
    elif args.command == "test":
        test_webcam()
    elif args.command == "mcp":
        start_mcp_server(args.debug)
    elif args.command == "dashboard":
        start_web_dashboard()
    elif args.command == "webcam":
        test_webcam()
        print("\n" + "=" * 40)
        start_web_dashboard()
    elif args.command == "both":
        print("🚀 Starting both MCP server and web dashboard...")
        print("📡 MCP Server: Available for Claude Desktop")
        print("🌐 Web Dashboard: http://localhost:7777")
        print("🛑 Press Ctrl+C to stop both services")
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



