"""
Base tool classes and decorators for Tapo Camera MCP tools.

This module provides the base functionality for all tools in the Tapo Camera MCP system,
including decorators for FastMCP 2.12 compatibility.
"""

from typing import Any, Dict, List, Optional, Type, TypeVar, Callable, Awaitable
from dataclasses import dataclass, field
from enum import Enum
import json
import logging

# Import from fastmcp directly as the structure might have changed
from fastmcp.tools import Tool, ToolResult
from fastmcp.tools.types import ToolParameter

logger = logging.getLogger(__name__)

# Type variable for tool classes
T = TypeVar('T', bound='BaseTool')

class ToolCategory(str, Enum):
    """Categories for organizing tools in the MCP interface."""
    CAMERA = "Camera"
    SYSTEM = "System"
    MEDIA = "Media"
    CONFIGURATION = "Configuration"
    UTILITY = "Utility"

@dataclass
class ToolDefinition:
    """Metadata for a tool."""
    name: str
    description: str
    category: ToolCategory
    parameters: List[ToolParameter] = field(default_factory=list)
    is_async: bool = False

class BaseTool(Tool):
    """Base class for all Tapo Camera MCP tools.
    
    This class provides common functionality and metadata for all tools.
    """
    
    # Tool metadata - must be overridden by subclasses
    name: str = "base_tool"
    description: str = "Base tool - should be overridden"
    category: ToolCategory = ToolCategory.UTILITY
    
    def __init_subclass__(cls, **kwargs):
        """Register the tool class when it's defined."""
        super().__init_subclass__(**kwargs)
        
        # Skip abstract base classes
        if cls.__name__.startswith('Base'):
            return
            
        # Register the tool
        from . import register_tool
        register_tool(cls)
    
    @classmethod
    def get_definition(cls) -> ToolDefinition:
        """Get the tool definition with metadata and parameters."""
        return ToolDefinition(
            name=cls.name,
            description=cls.description,
            category=cls.category,
            parameters=getattr(cls, 'parameters', []),
            is_async=hasattr(cls, 'execute_async') or False
        )
    
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with the given parameters.
        
        This method should be overridden by subclasses to implement the tool's functionality.
        """
        raise NotImplementedError("Subclasses must implement execute method")

def tool(
    name: str,
    description: str,
    category: ToolCategory = ToolCategory.UTILITY,
    parameters: Optional[List[ToolParameter]] = None
) -> Callable[[Type[T]], Type[T]]:
    """Decorator for defining a tool with metadata.
    
    Args:
        name: Unique identifier for the tool
        description: Human-readable description of what the tool does
        category: Category for organizing the tool
        parameters: List of parameters the tool accepts
        
    Returns:
        A decorator that adds the metadata to the tool class
    """
    if parameters is None:
        parameters = []
    
    def decorator(tool_class: Type[T]) -> Type[T]:
        tool_class.name = name
        tool_class.description = description
        tool_class.category = category
        tool_class.parameters = parameters
        return tool_class
    
    return decorator

def parameter(
    name: str,
    type: Type,
    description: str,
    required: bool = True,
    default: Any = None,
    enum: Optional[List[Any]] = None,
    **kwargs
) -> ToolParameter:
    """Create a parameter definition for a tool.
    
    Args:
        name: Name of the parameter
        type: Python type of the parameter
        description: Description of the parameter
        required: Whether the parameter is required
        default: Default value for the parameter
        enum: List of allowed values for the parameter
        **kwargs: Additional parameter attributes
        
    Returns:
        A ToolParameter instance
    """
    # Map Python types to JSON schema types
    type_mapping = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean",
        dict: "object",
        list: "array"
    }
    
    param_type = type_mapping.get(type, str(type).lower())
    
    # Create enum values if provided
    enum_values = None
    if enum is not None:
        enum_values = [str(v) if not isinstance(v, (str, int, float, bool)) else v for v in enum]
    
    return ToolParameter(
        name=name,
        type=param_type,
        description=description,
        required=required,
        default=default,
        enum=enum_values,
        **kwargs
    )
