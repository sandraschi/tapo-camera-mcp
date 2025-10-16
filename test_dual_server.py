#!/usr/bin/env python3
"""
Test script for the dual server implementation
"""

import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_dual_server():
    """Test the dual server startup"""
    try:
        logger.info("Testing dual server import...")
        from src.tapo_camera_mcp.dual_server import TapoCameraDualServer

        logger.info("Creating dual server instance...")
        server = TapoCameraDualServer()

        logger.info("Testing REST app creation...")
        rest_app = server._create_rest_app()

        logger.info("Dual server created successfully!")
        logger.info(f"REST app: {rest_app}")
        logger.info(f"Routes: {[route.path for route in rest_app.routes]}")

    except Exception as e:
        logger.error(f"Error testing dual server: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(test_dual_server())


