import sys
import os
import platform
import importlib
from pathlib import Path


def print_section(title):
    print(f"\n{'-' * 40}")
    print(f"{title}")
    print(f"{'-' * 40}")


def main():
    # Print Python environment info
    print_section("Python Environment")
    print(f"Python Version: {platform.python_version()}")
    print(f"Python Executable: {sys.executable}")
    print(f"Working Directory: {os.getcwd()}")
    print(f"Python Path: {sys.path}")

    # Add src to path
    src_dir = str(Path(__file__).parent.absolute() / "src")
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)
    print(f"\nAdded to path: {src_dir}")

    # Test basic imports
    print_section("Testing Basic Imports")

    # Test importing base_tool
    try:
        import tapo_camera_mcp.tools.base_tool

        print("✅ Successfully imported tapo_camera_mcp.tools.base_tool")
        print(f"  Location: {tapo_camera_mcp.tools.base_tool.__file__}")
    except ImportError as e:
        print(f"❌ Failed to import base_tool: {e}")

    # Test importing tools/__init__.py
    try:
        import tapo_camera_mcp.tools

        print("✅ Successfully imported tapo_camera_mcp.tools")
        print(f"  Location: {tapo_camera_mcp.tools.__file__}")
    except ImportError as e:
        print(f"❌ Failed to import tools: {e}")

    # Test importing a tool module
    print_section("Testing Tool Module Imports")

    tool_modules = [
        "tapo_camera_mcp.tools.camera",
        "tapo_camera_mcp.tools.system",
        "tapo_camera_mcp.tools.ptz",
        "tapo_camera_mcp.tools.media",
        "tapo_camera_mcp.tools.grafana",
    ]

    for module_name in tool_modules:
        try:
            module = importlib.import_module(module_name)
            print(f"✅ Successfully imported {module_name}")
            print(f"  Location: {module.__file__}")
        except ImportError as e:
            print(f"❌ Failed to import {module_name}: {e}")

    # Test tool registration
    print_section("Testing Tool Registration")
    try:
        from tapo_camera_mcp.tools import get_all_tools

        tools = get_all_tools()
        print(f"✅ Successfully got {len(tools)} registered tools")
        for tool in tools:
            print(f"  - {tool.name}: {tool.__module__}.{tool.__name__}")
    except Exception as e:
        print(f"❌ Error testing tool registration: {e}")


if __name__ == "__main__":
    main()
