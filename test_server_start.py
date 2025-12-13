#!/usr/bin/env python3
"""Test server startup with full error reporting."""

import logging
import sys
import traceback

# Setup detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('server_start.log')
    ]
)

logger = logging.getLogger(__name__)

print("=" * 70)
print("TAPO CAMERA MCP - SERVER STARTUP TEST")
print("=" * 70)

try:
    # Add src to path
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
    print("✅ Added src to path")

    # Test imports
    print("\n1. Testing imports...")
    from tapo_camera_mcp.config import get_config, get_model
    print("   ✅ Config imports OK")

    from tapo_camera_mcp.config.models import WebUISettings
    print("   ✅ WebUISettings import OK")

    print("   ✅ Logging import OK")

    from tapo_camera_mcp.web.server import WebServer
    print("   ✅ WebServer import OK")

    # Test config
    print("\n2. Testing configuration...")
    config = get_config()
    print(f"   ✅ Config loaded: {len(config)} keys")

    web_config = get_model(WebUISettings)
    print(f"   ✅ Web config: port={web_config.port}, host={web_config.host}")

    # Create server
    print("\n3. Creating server instance...")
    server = WebServer()
    print("   ✅ Server instance created")

    # Start server
    print("\n4. Starting server...")
    print(f"   🌐 Will start on: http://{web_config.host}:{web_config.port}")
    print("   🛑 Press Ctrl+C to stop")
    print("=" * 70)
    print()

    server.run(port=7777)

except KeyboardInterrupt:
    print("\n\n🛑 Server stopped by user")
    sys.exit(0)
except Exception as e:
    print(f"\n\n❌ ERROR: {type(e).__name__}: {e}")
    print("\n" + "=" * 70)
    print("FULL TRACEBACK:")
    print("=" * 70)
    traceback.print_exc()
    print("=" * 70)
    sys.exit(1)
