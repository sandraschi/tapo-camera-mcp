"""
Test script to verify tool imports and registration.
"""
import sys
import os
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def add_src_to_path():
    """Add the src directory to the Python path."""
    src_dir = str(Path(__file__).parent.absolute() / "src")
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)
    logger.info(f"Added to path: {src_dir}")

def test_import(module_name):
    """Test importing a module and print the result."""
    try:
        __import__(module_name)
        logger.info(f"✅ Successfully imported: {module_name}")
        return True
    except ImportError as e:
        logger.error(f"❌ Failed to import {module_name}: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        logger.error(f"⚠️ Error importing {module_name}: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function to test imports."""
    add_src_to_path()
    
    # Test importing the tools package
    test_import("tapo_camera_mcp.tools")
    
    # Test importing tool modules
    modules_to_test = [
        "tapo_camera_mcp.tools.camera",
        "tapo_camera_mcp.tools.system",
        "tapo_camera_mcp.tools.ptz",
        "tapo_camera_mcp.tools.media",
        "tapo_camera_mcp.tools.grafana"
    ]
    
    for module in modules_to_test:
        test_import(module)
    
    # Test tool registration
    try:
        from tapo_camera_mcp.tools import get_all_tools
        tools = get_all_tools()
        logger.info("\n=== Registered Tools ===")
        for tool in tools:
            logger.info(f"- {tool.name}: {tool.__module__}.{tool.__name__}")
    except Exception as e:
        logger.error(f"Failed to get registered tools: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
