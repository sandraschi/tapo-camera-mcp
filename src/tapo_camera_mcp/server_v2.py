#!/usr/bin/env python3
"""
Tapo Camera MCP Server v2 - Fixed asyncio handling for Claude Desktop integration
Provides camera control capabilities through MCP protocol
"""

import argparse
import logging
import os
import sys
import warnings

# Defer Tapo import to avoid PyO3 initialization issues
# Will be imported in main() after Python interpreter is ready
Tapo = None

# Suppress warnings to prevent noise in logs
os.environ["PYTHONWARNINGS"] = "ignore"
warnings.filterwarnings("ignore")
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=PendingDeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# Configure enhanced logging (to stderr - won't corrupt MCP stdout JSON-RPC)
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stderr),
    ],
)

logger = logging.getLogger(__name__)

# Apply patch for ring_doorbell imports (optional - Ring integration)
# Done AFTER logging is configured so messages are visible
try:
    from . import patch_ring_doorbell
    patch_ring_doorbell.patch_ring_doorbell()
except Exception as e:
    logger.warning(f"Ring patch skipped: {e}")

# Re-export Tapo for tests
# PLW0127: Self-assignment is intentional for re-export pattern
Tapo = Tapo

# Import and re-export TapoCameraServer for tests


def main():
    """Main entry point - synchronous to avoid event loop conflicts with Claude Desktop"""
    logger.info("=== TAPO CAMERA MCP SERVER STARTUP ===")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Command line args: {sys.argv}")

    parser = argparse.ArgumentParser(description="Tapo Camera MCP Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind the server to")  # nosec B104
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

            # Import Tapo library BEFORE starting asyncio to avoid PyO3 initialization issues
            logger.info("Importing Tapo library...")
            from tapo_camera_mcp.camera.tapo import Tapo

            import asyncio

            async def direct_main():
                """Direct mode for Claude Desktop"""
                logger.info("Initializing TapoCameraServer...")
                from tapo_camera_mcp.core.server import TapoCameraServer

                server = await TapoCameraServer.get_instance()
                logger.info("TapoCameraServer initialized successfully")

                logger.info("Starting server in direct stdio mode...")
                # run_stdio_async() blocks indefinitely - this should never return
                await server.run(host=args.host, port=args.port, stdio=args.stdio, direct=True)
                # This line should never be reached - if it is, something went wrong
                logger.error("ERROR: run_stdio_async() returned unexpectedly!")

            # Run in direct mode - this blocks until server exits
            logger.info("Calling asyncio.run(direct_main())...")
            asyncio.run(direct_main())
            # Only reached if server exits (should not happen normally)
            logger.warning("Server exited - this should not happen in normal operation")
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
        sys.exit(0)
    except Exception as e:
        logger.error("=== SERVER FAILED TO START ===", exc_info=True)
        logger.exception(f"Error type: {type(e).__name__}")
        logger.exception("Error message")
        sys.exit(1)

    logger.info("=== MAIN FUNCTION COMPLETE ===")


if __name__ == "__main__":
    main()
