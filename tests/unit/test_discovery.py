"""
Test script for tool discovery functionality.
"""

import sys
import logging
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def test_tool_discovery():
    """Test the tool discovery functionality."""
    try:
        logger.info("Starting tool discovery test...")

        # Import the discovery module
        from tapo_camera_mcp.tools.discovery import discover_tools

        # Discover tools
        tools = discover_tools("tapo_camera_mcp.tools")

        logger.info(f"Discovered {len(tools)} tools:")
        for tool in tools:
            logger.info(f"- {tool.__name__}")

        return True
    except Exception as e:
        logger.error(f"Error in test_tool_discovery: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    if test_tool_discovery():
        logger.info("Tool discovery test completed successfully!")
        sys.exit(0)
    else:
        logger.error("Tool discovery test failed!")
        sys.exit(1)
