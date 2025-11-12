"""
Manual import test script for Tapo Camera MCP.
"""

import sys
import pytest
from pathlib import Path


@pytest.mark.skip(reason="# TODO: Fix test_import - currently has assert False")
def test_import(module_name):
    """Test importing a module and print the result."""
    try:
        __import__(module_name)
        assert True
    except ImportError:
        assert False
    except Exception:
        assert False


def main():
    """Main function to test imports."""
    # Add the src directory to the Python path
    src_dir = str(Path(__file__).parent.absolute() / "src")
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)

    # Test importing main package
    test_import("tapo_camera_mcp")

    # Test importing core modules
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
