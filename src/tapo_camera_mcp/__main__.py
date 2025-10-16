#!/usr/bin/env python3
"""
Main entry point for the Tapo Camera MCP server.
"""

import asyncio
import logging
import sys


def main():
    """Run the Tapo Camera MCP server."""
    from .core.server import main as server_main

    try:
        asyncio.run(server_main())
    except KeyboardInterrupt:
        logging.info("Server stopped by user")
        sys.exit(0)
    except Exception as e:
        logging.error(f"Error running server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
