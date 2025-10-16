"""
Tapo Camera MCP Tools Package

This package contains all the tools for the Tapo Camera MCP server,
organized into logical modules for better maintainability.
"""

# Import types first to avoid circular imports
from typing import Dict, Type, List, Optional, TYPE_CHECKING, Any

# Import base tool components
from tapo_camera_mcp.tools.base_tool import (
    BaseTool,
    register_tool,
    get_tool as _get_tool,
    get_all_tools as _get_all_tools,
    ToolCategory,
    ToolDefinition,
    ToolResult,
    _tool_registry as tools_registry,
)

# Import discovery functions
from tapo_camera_mcp.tools.discovery import discover_tools

# Import standard library modules
from importlib import import_module
import pkgutil
import os
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Re-export functions from base_tool
get_tool = _get_tool
get_all_tools = _get_all_tools


def discover_tools(package: Optional[str] = None) -> List[Type[BaseTool]]:
    """Discover and import all tools in the specified package.

    Args:
        package: The package to search for tools (default: current package)

    Returns:
        List of discovered tool classes
    """
    if package is None:
        package = __name__

    # Get the directory containing the tools
    package_path = os.path.dirname(os.path.abspath(__file__))

    # Determine subpackage directory names to avoid importing same-named .py modules
    subpackage_dirs = {
        name
        for name in os.listdir(package_path)
        if os.path.isdir(os.path.join(package_path, name))
    }

    # Import all modules in the tools directory
    for finder, module_name, is_pkg in pkgutil.iter_modules([package_path]):
        # Skip the base module and private modules
        if module_name == "base_tool" or module_name.startswith("_"):
            continue

        # If there exists a subpackage with the same name, skip importing the .py module to avoid conflicts
        if not is_pkg and module_name in subpackage_dirs:
            continue

        full_module_name = f"{package}.{module_name}"
        try:
            # Use finder.find_spec to properly handle package imports
            spec = finder.find_spec(module_name)
            if spec is not None:
                module = import_module(full_module_name)
                if is_pkg:
                    # Recursively discover tools in subpackages
                    subpackage_path = os.path.join(package_path, module_name)
                    discover_tools_in_path(subpackage_path, full_module_name)
        except ImportError as e:
            logger.error(f"Failed to import tool module {full_module_name}: {e}")

    return _get_all_tools()


def discover_tools_in_path(package_path: str, package_name: str) -> None:
    """Discover tools in a specific package path.

    Args:
        package_path: The directory path to search
        package_name: The full package name for imports
    """
    # Import all modules in the subpackage directory
    for finder, module_name, is_pkg in pkgutil.iter_modules([package_path]):
        # Skip private modules
        if module_name.startswith("_"):
            continue

        full_module_name = f"{package_name}.{module_name}"
        try:
            # Use finder.find_spec to properly handle package imports
            spec = finder.find_spec(module_name)
            if spec is not None:
                import_module(full_module_name)
                if is_pkg:
                    # Recursively discover tools in deeper subpackages
                    subpackage_path = os.path.join(package_path, module_name)
                    discover_tools_in_path(subpackage_path, full_module_name)
        except ImportError as e:
            logger.error(f"Failed to import tool module {full_module_name}: {e}")


# Re-export functions from base_tool
get_tool = _get_tool
get_all_tools = _get_all_tools

# Discover tools when the package is imported
discover_tools()

__all__ = [
    "BaseTool",
    "ToolCategory",
    "ToolResult",
    "register_tool",
    "get_tool",
    "get_all_tools",
    "discover_tools",
    "tools_registry",
    "ToolDefinition",
]
