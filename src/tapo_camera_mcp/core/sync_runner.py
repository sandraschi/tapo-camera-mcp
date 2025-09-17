"""
Synchronous runner for Tapo Camera MCP Server in direct mode.
This module provides a completely synchronous way to run the MCP server 
for Claude Desktop integration, avoiding asyncio event loop conflicts.
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional

from fastmcp import FastMCP

logger = logging.getLogger(__name__)

def create_mcp_server() -> FastMCP:
    """Create and configure the FastMCP server synchronously."""
    # Initialize FastMCP
    mcp = FastMCP(
        name="Tapo-Camera-MCP",
        version="0.4.0"
    )
    
    # Import and register tools synchronously
    from ..tools.discovery import discover_tools
    
    tools = discover_tools('tapo_camera_mcp.tools')
    
    for tool_cls in tools:
        # Get the tool name and description from the Meta class or class attributes
        tool_name = getattr(tool_cls, 'name', getattr(tool_cls.Meta, 'name', tool_cls.__name__))
        tool_description = getattr(tool_cls, 'description', getattr(tool_cls.Meta, 'description', ''))
        
        try:
            # Try to create an instance with default values
            try:
                tool_instance = tool_cls()
                logger.debug(f"Successfully instantiated tool: {tool_name}")
            except Exception as e:
                # If we can't create with defaults, skip this tool
                logger.warning(f"Skipping tool {tool_name}: Could not instantiate with defaults: {str(e)}")
                continue
                
            logger.debug(f"Registering tool: {tool_name}")
            
            # If the tool has a sync initialize method, call it
            if hasattr(tool_instance, 'initialize') and callable(tool_instance.initialize):
                try:
                    # Check if it's async (has __await__ method)
                    if not hasattr(tool_instance.initialize, '__await__'):
                        tool_instance.initialize()
                        logger.debug(f"Initialized tool: {tool_name}")
                    else:
                        logger.debug(f"Skipping async initialization for tool: {tool_name}")
                except Exception as e:
                    logger.warning(f"Failed to initialize tool {tool_name}: {str(e)}")
                    continue
            
            # Create a synchronous wrapper for the tool
            def create_sync_tool_wrapper(tool_instance, tool_name):
                """Create a synchronous tool wrapper."""
                
                def sync_tool_wrapper(*args, **kwargs):
                    """Synchronous wrapper for tool execution."""
                    try:
                        # Try to call the tool synchronously
                        if hasattr(tool_instance, 'execute'):
                            # Call execute method directly (sync)
                            result = tool_instance.execute(**kwargs)
                        elif callable(tool_instance):
                            # Call the instance directly
                            result = tool_instance(**kwargs)
                        else:
                            result = {"error": "Tool not callable", "success": False}
                        
                        return result
                        
                    except Exception as e:
                        logger.error(f"Error executing tool {tool_name}: {e}")
                        return {"error": str(e), "success": False}
                
                return sync_tool_wrapper
            
            # Create the wrapper with the correct tool name
            tool_wrapper = create_sync_tool_wrapper(tool_instance, tool_name)
            
            # Register with FastMCP using from_function
            try:
                from fastmcp.tools import Tool
                fastmcp_tool = Tool.from_function(
                    fn=tool_wrapper,
                    name=tool_name,
                    description=tool_description
                )
                
                # Add to MCP server
                mcp.add_tool(fastmcp_tool)
                logger.info(f"Successfully registered tool: {tool_name}")
                
            except Exception as e:
                logger.warning(f"Failed to register tool {tool_name}: {e}")
                continue
                
        except Exception as e:
            logger.error(f"Unexpected error processing tool {tool_name}: {str(e)}", exc_info=True)
            continue
    
    logger.info(f"Registered {len(tools)} tools")
    return mcp

def run_direct_server():
    """Run the MCP server in direct stdio mode for Claude Desktop."""
    logger.info("Initializing direct mode MCP server...")
    
    try:
        # Create temp directory
        temp_dir = Path('/tmp/tapo-mcp')
        temp_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Using temp directory: {temp_dir}")
        
        # Create MCP server
        mcp = create_mcp_server()
        
        # Run in stdio transport mode - this is the key fix!
        # FastMCP.run() handles the event loop internally in a safe way
        logger.info("Starting MCP server with stdio transport...")
        mcp.run(transport="stdio")
        
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Direct server error: {e}")
        logger.exception("Full traceback:")
        raise
