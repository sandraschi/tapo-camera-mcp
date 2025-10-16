import sys
import os
import platform
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

    # Test importing base_tool
    print_section("Testing base_tool Import")
    try:
        import tapo_camera_mcp.tools.base_tool as base_tool

        print("✅ Successfully imported tapo_camera_mcp.tools.base_tool")
        print(f"  Location: {base_tool.__file__}")
    except Exception as e:
        print(f"❌ Failed to import base_tool: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
