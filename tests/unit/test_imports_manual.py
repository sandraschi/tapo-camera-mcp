"""
Manual import test script for Tapo Camera MCP.
"""
import sys
import os
from pathlib import Path

def test_import(module_name):
    """Test importing a module and print the result."""
    try:
        __import__(module_name)
        print(f"✅ Successfully imported: {module_name}")
        return True
    except ImportError as e:
        print(f"❌ Failed to import {module_name}: {e}")
        return False
    except Exception as e:
        print(f"⚠️ Error importing {module_name}: {e}")
        return False

def main():
    """Main function to test imports."""
    # Add the src directory to the Python path
    src_dir = str(Path(__file__).parent.absolute() / "src")
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)
    
    print(f"Python path: {sys.path}\n")
    
    # Test importing main package
    print("Testing main package import...")
    test_import("tapo_camera_mcp")
    
    # Test importing core modules
    print("\nTesting core modules...")
    core_modules = [
        "tapo_camera_mcp.core.server",
        "tapo_camera_mcp.tools.base_tool",
        "tapo_camera_mcp.camera.manager",
        "tapo_camera_mcp.api.v1.endpoints.cameras",
        "tapo_camera_mcp.config.models",
    ]
    
    for module in core_modules:
        test_import(module)

if __name__ == "__main__":
    main()
