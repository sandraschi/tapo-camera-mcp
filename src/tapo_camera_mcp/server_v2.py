#!/usr/bin/env python3
"""
Tapo Camera MCP Server v2 - Fixed asyncio handling for Claude Desktop integration
Provides camera control capabilities through MCP protocol
"""

import logging
import argparse
import sys
from typing import Dict, Any, Optional

from fastmcp.server import FastMCP
from tapo_camera_mcp.camera.tapo import Tapo
from tapo_camera_mcp.tools.discovery import discover_tools
from tapo_camera_mcp.tools.base_tool import ToolResult
from tapo_camera_mcp.core.server import TapoCameraServer

# Re-export Tapo for tests
Tapo = Tapo

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    """Main entry point - synchronous to avoid event loop conflicts with Claude Desktop"""
    parser = argparse.ArgumentParser(description="Tapo Camera MCP Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind the server to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind the server to")
    parser.add_argument("--no-stdio", action="store_false", dest="stdio", 
                       help="Disable stdio transport")
    parser.add_argument("--direct", action="store_true", 
                       help="Use direct stdio mode (for Claude Desktop integration)")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        
    logger.info("Starting Tapo Camera MCP Server...")
    
    try:
        # For Claude Desktop direct mode, we need pure sync handling
        if args.direct:
            logger.info("Using direct stdio mode for Claude Desktop")
            import asyncio
            
            async def direct_main():
                """Direct mode for Claude Desktop"""
                from tapo_camera_mcp.core.server import TapoCameraServer
                server = await TapoCameraServer.get_instance()
                await server.run(
                    host=args.host,
                    port=args.port,
                    stdio=args.stdio,
                    direct=True
                )
            
            # Run in direct mode
            asyncio.run(direct_main())
        else:
            # Standard async mode
            logger.info("Using standard async mode")
            import asyncio
            
            async def async_main():
                """Async main for non-direct mode"""
                from tapo_camera_mcp.core.server import TapoCameraServer
                server = await TapoCameraServer.get_instance()
                await server.run(
                    host=args.host,
                    port=args.port, 
                    stdio=args.stdio,
                    direct=False  # Explicitly false for standard mode
                )
            
            # Run with asyncio.run for standard mode
            asyncio.run(async_main())
            
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Server failed to start: {e}")
        logger.exception("Full traceback:")
        sys.exit(1)

if __name__ == "__main__":
    main()

