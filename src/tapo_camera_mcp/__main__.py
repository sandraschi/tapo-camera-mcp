#!/usr/bin/env python3
"""
Main entry point for the Tapo Camera MCP server.
"""

import asyncio
import logging
import sys

from .core.server import main as server_main


def main():
    """Run the Tapo Camera MCP server."""
    try:
        asyncio.run(server_main())
    except KeyboardInterrupt:
        logging.info("Server stopped by user")
        sys.exit(0)
    except Exception:
        logging.exception("Error running server")
        sys.exit(1)


if __name__ == "__main__":
    main()
