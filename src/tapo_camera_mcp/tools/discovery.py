"""
Tool discovery and registration for Tapo Camera MCP.

This module provides functionality to discover and register tools with the MCP server.
"""

import importlib
import inspect
import logging
import pkgutil
import traceback
from typing import Any, List, Set, Type

logger = logging.getLogger(__name__)

# Track imported modules to avoid duplicates
_imported_modules: Set[str] = set()


def is_tool_class(obj: Any) -> bool:
    """Check if an object is a valid tool class.

    Args:
        obj: The object to check

    Returns:
        bool: True if the object is a valid tool class, False otherwise
    """
    try:
        from .base_tool import BaseTool

        if not inspect.isclass(obj):
            return False

        # Check if it's a subclass of BaseTool but not BaseTool itself
        if not issubclass(obj, BaseTool) or obj is BaseTool:
            return False

        # Check for required attributes in FastMCP 2.12
        if not hasattr(obj, "Meta") or not hasattr(obj.Meta, "name") or not hasattr(obj, "execute"):
            return False

        # Check if the Meta class has the required Parameters class (optional for Pydantic-based tools)
        # Some tools use Pydantic fields directly instead of Parameters classes
        hasattr(obj.Meta, "Parameters")
        # For now, we'll accept tools with or without Parameters classes
        # TODO: Standardize on one approach across all tools

        return True

    except Exception as e:
        logger.debug(f"Error checking if {obj} is a tool class: {e}")
        return False


def discover_tools(package: str = "tapo_camera_mcp.tools") -> List[Type[Any]]:
    """
    Discover and return all available tools from the specified package.

    Args:
        package: The package to search for tools (default: 'tapo_camera_mcp.tools')

    Returns:
        List of tool classes that can be registered with the MCP server.
    """
    tools: List[Type[Any]] = []

    try:
        logger.debug(f"Starting tool discovery in package: {package}")

        # Import the package
        try:
            package_module = importlib.import_module(package)
            package_path = getattr(package_module, "__path__", [])

            if not package_path:
                logger.warning(f"Package {package} has no __path__ attribute")
                return tools

            logger.debug(f"Package {package} path: {package_path}")

            # Walk through all modules in the package
            for _finder, name, _is_pkg in pkgutil.walk_packages(package_path, prefix=f"{package}."):
                # Skip __pycache__ and other special directories
                if any(part.startswith("__") for part in name.split(".")):
                    continue

                try:
                    # Skip already imported modules to avoid re-processing
                    if name in _imported_modules:
                        continue

                    logger.debug(f"Importing module: {name}")
                    module = importlib.import_module(name)
                    _imported_modules.add(name)

                    # Find all tool classes in the module
                    for attr_name in dir(module):
                        try:
                            attr = getattr(module, attr_name)
                            if is_tool_class(attr):
                                tools.append(attr)
                                logger.info(f"Discovered tool: {attr.__name__} from {name}")
                        except Exception as e:
                            logger.warning(f"Error checking attribute {attr_name} in {name}: {e}")
                            logger.debug(traceback.format_exc())

                except ImportError as e:
                    logger.warning(f"Could not import module {name}: {e}")
                    logger.debug(traceback.format_exc())
                except Exception as e:
                    logger.exception(f"Error processing module {name}: {e}")
                    logger.debug(traceback.format_exc())

        except ImportError as e:
            logger.exception(f"Failed to import package {package}: {e}")
            logger.debug(traceback.format_exc())

    except Exception as e:
        logger.exception(f"Unexpected error in discover_tools: {e}")
        logger.debug(traceback.format_exc())

    logger.info(f"Discovered {len(tools)} tools from {package}")
    return tools
