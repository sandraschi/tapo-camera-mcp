#!/usr/bin/env python3
"""
Tapo Camera MCP Server v2 - Fixed asyncio handling for Claude Desktop integration
Provides camera control capabilities through MCP protocol
"""

import os
import sys

# Suppress warnings before any imports to prevent JSON parsing issues in Claude Desktop
import warnings

# Set environment variable to suppress warnings globally
os.environ["PYTHONWARNINGS"] = "ignore"

# Redirect stderr to avoid warnings interfering with JSON parsing
original_stderr = sys.stderr
sys.stderr = open(os.devnull, "w")

# Apply warning filters
warnings.filterwarnings("ignore")
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=PendingDeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# Apply patch for ring_doorbell imports first
try:
    import patch_ring_doorbell

    patch_ring_doorbell.patch_ring_doorbell()
except Exception as e:
    # Use stderr for warnings to avoid JSON parsing issues
    print(f"Warning: Failed to apply ring_doorbell patch: {e}", file=original_stderr)

# Restore stderr after imports are complete
sys.stderr = original_stderr

import argparse
import logging
import sys

from tapo_camera_mcp.camera.tapo import Tapo

# Re-export Tapo for tests
Tapo = Tapo

# Configure enhanced logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stderr),  # Ensure logs go to stderr for Claude Desktop
    ],
)

logger = logging.getLogger(__name__)


def main():
    """Main entry point - synchronous to avoid event loop conflicts with Claude Desktop"""
    logger.info("=== TAPO CAMERA MCP SERVER STARTUP ===")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Command line args: {sys.argv}")

    parser = argparse.ArgumentParser(description="Tapo Camera MCP Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind the server to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind the server to")
    parser.add_argument(
        "--no-stdio", action="store_false", dest="stdio", help="Disable stdio transport"
    )
    parser.add_argument(
        "--direct",
        action="store_true",
        help="Use direct stdio mode (for Claude Desktop integration)",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    args = parser.parse_args()
    logger.info(f"Parsed arguments: {vars(args)}")

    # Configure logging level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.info("Starting Tapo Camera MCP Server...")

    try:
        # For Claude Desktop direct mode, we need pure sync handling
        if args.direct:
            logger.info("=== USING DIRECT STDIO MODE FOR CLAUDE DESKTOP ===")
            logger.info("This mode is optimized for Claude Desktop integration")
            import asyncio

            async def direct_main():
                """Direct mode for Claude Desktop"""
                logger.info("Initializing TapoCameraServer...")
                from tapo_camera_mcp.core.server import TapoCameraServer

                server = await TapoCameraServer.get_instance()
                logger.info("TapoCameraServer initialized successfully")

                logger.info("Starting server in direct stdio mode...")
                await server.run(host=args.host, port=args.port, stdio=args.stdio, direct=True)
                logger.info("Server started successfully in direct mode")

            # Run in direct mode
            logger.info("Calling asyncio.run(direct_main())...")
            asyncio.run(direct_main())
            logger.info("Direct mode completed")
        else:
            # Standard async mode
            logger.info("=== USING STANDARD ASYNC MODE ===")
            import asyncio

            async def async_main():
                """Async main for non-direct mode"""
                logger.info("Initializing TapoCameraServer...")
                from tapo_camera_mcp.core.server import TapoCameraServer

                server = await TapoCameraServer.get_instance()
                logger.info("TapoCameraServer initialized successfully")

                logger.info("Starting server in standard async mode...")
                await server.run(
                    host=args.host,
                    port=args.port,
                    stdio=args.stdio,
                    direct=False,  # Explicitly false for standard mode
                )
                logger.info("Server started successfully in standard mode")

            # Run with asyncio.run for standard mode
            logger.info("Calling asyncio.run(async_main())...")
            asyncio.run(async_main())
            logger.info("Standard mode completed")

    except KeyboardInterrupt:
        logger.info("=== SERVER SHUTDOWN REQUESTED (Ctrl+C) ===")
        print("Server shutdown requested", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        logger.error("=== SERVER FAILED TO START ===", exc_info=True)
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error message: {e}")
        print(f"Server failed to start: {e}", file=sys.stderr)
        sys.exit(1)

    logger.info("=== MAIN FUNCTION COMPLETE ===")
    print("Main function completed", file=sys.stderr)


if __name__ == "__main__":
    main()
