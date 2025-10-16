#!/usr/bin/env python3
"""Test script to verify all imports in the project."""

import importlib
import os
import sys
from pathlib import Path
from typing import Any, Optional


def import_module_safe(module_name: str) -> Optional[Any]:
    """Safely import a module and return it, or None if it fails."""
    try:
        module = importlib.import_module(module_name)
        print(f"✓ Imported: {module_name}")
        return module
    except ImportError as e:
        print(f"✗ Failed to import {module_name}: {e}")
        import traceback

        traceback.print_exc()
        return None
    except Exception as e:
        print(f"⚠ Unexpected error importing {module_name}: {e}")
        import traceback

        traceback.print_exc()
        return None


def test_imports():
    """Test importing all main modules and packages."""
    print("\n=== Testing Tapo Camera MCP Imports ===")

    # Add the project root to the Python path
    project_root = str(Path(__file__).parent.absolute())
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    # Test importing main package
    print("\nTesting main package import...")
    tapo_pkg = import_module_safe("tapo_camera_mcp")
    if not tapo_pkg:
        print("❌ Failed to import main package")
        return False

    # List of core modules to test
    core_modules = [
        "tapo_camera_mcp.core.server",
        "tapo_camera_mcp.tools.base_tool",
        "tapo_camera_mcp.camera.manager",
        "tapo_camera_mcp.api.v1.endpoints.cameras",
        "tapo_camera_mcp.config.models",
    ]

    print("\nTesting core module imports...")
    all_imports_ok = True

    for module_name in core_modules:
        if not import_module_safe(module_name):
            all_imports_ok = False

    # Test tool imports
    print("\nTesting tool imports...")
    tools_dir = os.path.join(os.path.dirname(__file__), "src", "tapo_camera_mcp", "tools")
    if os.path.exists(tools_dir):
        for filename in os.listdir(tools_dir):
            if filename.endswith(".py") and not filename.startswith("_"):
                module_name = f"tapo_camera_mcp.tools.{filename[:-3]}"
                if module_name.endswith(".py"):
                    module_name = module_name[:-3]
                if not import_module_safe(module_name):
                    all_imports_ok = False

    if all_imports_ok:
        print("\n✅ All imports successful!")
    else:
        print("\n❌ Some imports failed. See above for details.")

    return all_imports_ok


def main():
    """Main entry point for the import test."""
    print("=== Starting import test script ===")
    success = test_imports()

    # Test specific modules that might have issues
    test_modules = [
        "tapo_camera_mcp.core.server",
        "tapo_camera_mcp.cli_v2",
        "tapo_camera_mcp.web.server",
        "tapo_camera_mcp.api.v1.endpoints.cameras",
    ]

    print("\nTesting additional modules...")
    for module_name in test_modules:
        if not import_module_safe(module_name):
            success = False

    if success:
        print("\n✅ All imports completed successfully!")
    else:
        print("\n❌ Some imports failed. Please check the output above for details.")

    return 0 if success else 1


if __name__ == "__main__":
    import sys

    sys.exit(main())
