"""
FastMCP Tool Registration for tapo-camera-mcp

This module registers all tapo-camera-mcp tools with FastMCP.
"""

import logging

from fastmcp import FastMCP

logger = logging.getLogger(__name__)


def register_all_tools(mcp: FastMCP, tool_mode: str = "production") -> None:
    """Register tapo-camera-mcp tools with the FastMCP server.

    Args:
        mcp: The FastMCP instance to register tools with
        tool_mode: Registration mode:
            - "production": Only portmanteau tools (cleaner UI)
            - "testing" or "all": Individual + portmanteau tools (for testing)
    """
    # Check if tools are already registered to this FastMCP instance
    if hasattr(mcp, '_tapo_tools_registered') and mcp._tapo_tools_registered:
        logger.debug("Tools already registered to this FastMCP instance, skipping")
        return
    
    # Always register portmanteau tools (consolidated tools)
    from tapo_camera_mcp.tools.portmanteau import register_all_portmanteau_tools

    register_all_portmanteau_tools(mcp)
    mcp._tapo_tools_registered = True  # Mark as registered
    logger.info("Portmanteau tools registered successfully")

    # Register individual tools only in testing/all mode
    if tool_mode.lower() in ["testing", "all"]:
        logger.info(f"Tool mode: {tool_mode} - Registering individual tools for testing")
        _register_individual_tools(mcp)
    else:
        logger.info(f"Tool mode: {tool_mode} - Using portmanteau tools only (production mode)")


def _register_individual_tools(mcp: FastMCP) -> None:
    """Register individual tools for backward compatibility and testing.

    Args:
        mcp: The FastMCP instance to register tools with
    """
    # This would register individual tools if needed for testing
    # For now, we rely on portmanteau tools only
    logger.info("Individual tools registration skipped (using portmanteau tools only)")

