#!/usr/bin/env python3
"""Test script to start the dashboard and see errors."""

import sys
import traceback

try:
    print("Importing WebServer...")
    from tapo_camera_mcp.web.server import WebServer
    print("✅ Import successful")

    print("Creating server instance...")
    server = WebServer()
    print("✅ Server created")

    print("Starting server on port 7777...")
    print("🌐 Dashboard will be available at: http://localhost:7777")
    server.run(port=7777)

except Exception as e:
    print(f"❌ ERROR: {e}")
    traceback.print_exc()
    sys.exit(1)
