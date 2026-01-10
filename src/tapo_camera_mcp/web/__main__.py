"""Entry point for running the web server as a module."""

import argparse
import logging
import sys
import warnings
from pathlib import Path

# Suppress websocket deprecation warnings
warnings.filterwarnings("ignore", message="websockets.legacy is deprecated")
warnings.filterwarnings("ignore", message="websockets.server.WebSocketServerProtocol is deprecated")

from ..utils.logging import setup_logging
from .server import WebServer

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser(description="Tapo Camera MCP Web Server")
        parser.add_argument(
            "--host", default=None, help="Host to bind the server to (default: from config)"
        )
        parser.add_argument(
            "--port",
            type=int,
            default=None,
            help="Port to bind the server to (default: from config)",
        )
        parser.add_argument("--debug", action="store_true", help="Enable debug mode")

        args = parser.parse_args()

        # Setup logging - handles both Docker and native environments
        import os

        is_docker = os.getenv("CONTAINER") == "yes" or os.path.exists("/.dockerenv")

        # Enable lazy hardware initialization for immediate dashboard access
        # Temporarily disable lazy init to fix hardware initialization issues
        # os.environ["TAPO_MCP_LAZY_INIT"] = "true"
        if is_docker:
            # In Docker: Log to stdout (Docker json-file driver) and mounted volume
            # Promtail reads from /app/logs/tapo_mcp.log (mounted to host)
            setup_logging(log_file="/app/logs/tapo_mcp.log")
        else:
            # Native: Log to project root
            log_file = Path(__file__).parent.parent.parent.parent / "tapo_mcp.log"
            setup_logging(log_file=str(log_file))
        logger.info("=" * 80)
        logger.info("Tapo Camera MCP Web Server - Starting")
        logger.info(f"Python: {sys.version.split()[0]}")
        logger.info(f"Platform: {sys.platform}")
        logger.info(f"Working directory: {Path.cwd()}")
        logger.info(f"Log file: {log_file}")
        logger.info("=" * 80)

        # Create and run the server
        server = WebServer()

        # Override config with command line args if provided
        host = args.host
        port = args.port

        server.run(host=host, port=port)
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        sys.exit(1)
