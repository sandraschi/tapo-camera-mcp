"""
Tapo Camera MCP Tools Package

This package contains all the tools for the Tapo Camera MCP server,
organized into logical modules for better maintainability.
"""

from fastmcp.tools import Tool
from typing import Dict, Type, List, Optional
from importlib import import_module
import pkgutil
import os
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Dictionary to store all registered tools
tools_registry: Dict[str, Type[Tool]] = {}

def register_tool(tool_cls: Type[Tool]) -> Type[Tool]:
    """Decorator to register a tool class.
    
    Args:
        tool_cls: The tool class to register
        
    Returns:
        The registered tool class
        
    Raises:
        ValueError: If the tool class is missing required attributes
    """
    if not hasattr(tool_cls, 'name'):
        raise ValueError(f"Tool class {tool_cls.__name__} must have a 'name' class attribute")
    
    if not hasattr(tool_cls, 'description'):
        raise ValueError(f"Tool class {tool_cls.__name__} must have a 'description' class attribute")
    
    tools_registry[tool_cls.name] = tool_cls
    logger.debug(f"Registered tool: {tool_cls.name}")
    return tool_cls

def get_tool(name: str) -> Optional[Type[Tool]]:
    """Get a registered tool by name.
    
    Args:
        name: The name of the tool to retrieve
        
    Returns:
        The tool class if found, None otherwise
    """
    return tools_registry.get(name)

def discover_tools(package: str = None) -> List[Type[Tool]]:
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
    
    # Import all modules in the tools directory
    for _, module_name, is_pkg in pkgutil.iter_modules([package_path]):
        # Skip the base module and private modules
        if module_name == 'base_tool' or module_name.startswith('_'):
            continue
            
        full_module_name = f"{package}.{module_name}"
        try:
            import_module(full_module_name)
            if is_pkg:
                # Recursively discover tools in subpackages
                discover_tools(full_module_name)
        except ImportError as e:
            logger.error(f"Failed to import tool module {full_module_name}: {e}")
    
    return list(tools_registry.values())

def get_all_tools() -> List[Type[Tool]]:
    """Get all registered tools.
    
    Returns:
        List of all registered tool classes
    """
    return list(tools_registry.values())

# Discover tools when the package is imported
discover_tools()

__all__ = [
    'Tool',
    'register_tool',
    'get_tool',
    'discover_tools',
    'get_all_tools',
    'tools_registry'
]
