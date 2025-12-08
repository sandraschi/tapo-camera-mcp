"""Entry point for running the web server as a module."""

from .server import WebServer
import argparse
from ..utils.logging import setup_logging

if __name__ == "__main__":
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

    # Setup logging
    setup_logging()

    # Create and run the server
    server = WebServer()

    # Override config with command line args if provided
    host = args.host
    port = args.port

    server.run(host=host, port=port)
