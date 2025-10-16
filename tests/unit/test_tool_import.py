"""
Test script to verify tool imports and registration.
"""

import sys
import logging
from pathlib import Path

# Add src to path
src_dir = str(Path(__file__).parent.absolute() / "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)
    print(f"Added to path: {src_dir}")

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def test_import(module_name):
    """Test importing a module and print the result."""
    try:
        __import__(module_name)
        logger.info(f"✅ Successfully imported: {module_name}")
        return True
    except ImportError as e:
        logger.error(f"❌ Failed to import {module_name}: {e}")
        import traceback

        logger.error(traceback.format_exc())
        return False
    except Exception as e:
        logger.error(f"⚠️ Error importing {module_name}: {e}")
        import traceback

        logger.error(traceback.format_exc())
        return False


def main():
    """Main function to test imports."""
    # Test importing base_tool
    test_import("tapo_camera_mcp.tools.base_tool")

    # Test importing tools/__init__.py
    test_import("tapo_camera_mcp.tools")

    # Test tool registration
    try:
        from tapo_camera_mcp.tools import get_all_tools

        tools = get_all_tools()
        logger.info("\n=== Registered Tools ===")
        for tool in tools:
            logger.info(f"- {tool.name}: {tool.__module__}.{tool.__name__}")
        logger.info(f"Total tools registered: {len(tools)}")
    except Exception as e:
        logger.error(f"\n❌ Error getting registered tools: {e}")
        import traceback

        logger.error(traceback.format_exc())


if __name__ == "__main__":
    main()
