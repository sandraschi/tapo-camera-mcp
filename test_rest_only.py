#!/usr/bin/env python3
"""
Test script for REST-only server
"""

import asyncio
import logging
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_rest_server():
    """Test just the REST server"""
    try:
        logger.info("Testing REST server import...")
        from src.tapo_camera_mcp.dual_server import TapoCameraDualServer

        logger.info("Creating dual server instance...")
        server = TapoCameraDualServer()

        logger.info("Starting REST server on port 8124...")
        await server.start_rest_server(host="0.0.0.0", port=8124)

    except Exception as e:
        logger.error(f"Error testing REST server: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(test_rest_server())



