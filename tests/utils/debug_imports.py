import logging
import sys
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def add_src_to_path():
    """Add the src directory to the Python path."""
    src_dir = str(Path(__file__).parent.absolute() / "src")
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)
    logger.info(f"Added to path: {src_dir}")


def test_import(module_name):
    """Test importing a module and print the result."""
    logger.info(f"\n=== Testing import of {module_name} ===")
    try:
        module = __import__(module_name, fromlist=["*"])
        logger.info(f"✅ Successfully imported {module_name}")

        # List available attributes
        attrs = [attr for attr in dir(module) if not attr.startswith("_")]
        logger.info(f"Available attributes: {', '.join(attrs)}\n")
        return True
    except ImportError as e:
        logger.error(f"❌ Failed to import {module_name}: {e}")
        import traceback

        logger.error(traceback.format_exc())
        return False
    except Exception as e:
        logger.error(f"⚠️ Unexpected error importing {module_name}: {e}")
        import traceback

        logger.error(traceback.format_exc())
        return False


def main():
    """Main function to test imports."""
    add_src_to_path()

    # Test importing base_tool first
    test_import("tapo_camera_mcp.tools.base_tool")

    # Test importing tools/__init__.py
    test_import("tapo_camera_mcp.tools")

    # Test importing tool modules
    modules = [
        "tapo_camera_mcp.tools.camera",
        "tapo_camera_mcp.tools.system",
        "tapo_camera_mcp.tools.ptz",
        "tapo_camera_mcp.tools.media",
        "tapo_camera_mcp.tools.grafana",
    ]

    for module in modules:
        test_import(module)

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
