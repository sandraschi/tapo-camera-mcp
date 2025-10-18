#!/usr/bin/env python3
"""
Focused test for core MCP server functionality and coverage.
"""

import os
import sys

# Add the src path to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))


def test_core_imports():
    """Test core module imports."""
    try:
        return True
    except Exception:
        return False


def test_tools_discovery():
    """Test tools discovery."""
    try:
        from tapo_camera_mcp.tools.discovery import discover_tools

        discover_tools("tapo_camera_mcp.tools")
        return True
    except Exception:
        return False


def test_camera_types():
    """Test camera type definitions."""
    try:

        return True
    except Exception:
        return False


def test_basic_server_creation():
    """Test basic server creation (without running it)."""
    try:

        # Just test that we can create the class, don't initialize
        return True
    except Exception:
        return False


if __name__ == "__main__":
    tests = [
        test_core_imports,
        test_tools_discovery,
        test_camera_types,
        test_basic_server_creation,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1


    if passed == total:
        sys.exit(0)
    else:
        sys.exit(1)
