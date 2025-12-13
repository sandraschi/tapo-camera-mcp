#!/usr/bin/env python3
"""Debug script to start dashboard and show all output."""

import logging
import sys
import traceback

# Enable all logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

print("=" * 60)
print("Starting Tapo Camera MCP Dashboard")
print("=" * 60)

try:
    print("\n1. Adding src to path...")
    sys.path.insert(0, 'src')
    print("   ✅ Path added")

    print("\n2. Importing WebServer...")
    from tapo_camera_mcp.web.server import WebServer
    print("   ✅ Import successful")

    print("\n3. Creating server instance...")
    server = WebServer()
    print("   ✅ Server created")

    print("\n4. Starting server on port 7777...")
    print("   🌐 Dashboard will be available at: http://localhost:7777")
    print("   🛑 Press Ctrl+C to stop")
    print("=" * 60)
    print()

    server.run(port=7777)

except KeyboardInterrupt:
    print("\n\n🛑 Server stopped by user")
    sys.exit(0)
except Exception as e:
    print(f"\n\n❌ ERROR: {type(e).__name__}: {e}")
    print("\nFull traceback:")
    traceback.print_exc()
    sys.exit(1)
