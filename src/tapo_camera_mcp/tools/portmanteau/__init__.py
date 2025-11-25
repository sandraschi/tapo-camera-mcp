"""
Portmanteau Tools Module

Consolidates multiple related tools into single, action-based tools to reduce
the tool explosion problem and improve MCP client usability.

Production mode: Portmanteau tools only (cleaner UI)
Testing mode: Individual tools also available
"""

import logging

from fastmcp import FastMCP

from .camera_management import register_camera_management_tool
from .configuration_management import register_configuration_management_tool
from .energy_management import register_energy_management_tool
from .media_management import register_media_management_tool
from .ptz_management import register_ptz_management_tool
from .security_management import register_security_management_tool
from .system_management import register_system_management_tool
from .weather_management import register_weather_management_tool

logger = logging.getLogger(__name__)


def register_all_portmanteau_tools(mcp: FastMCP) -> None:
    """Register all portmanteau tools with the FastMCP server.

    Args:
        mcp: The FastMCP instance to register tools with
    """
    # Core portmanteau tools (always registered)
    register_camera_management_tool(mcp)
    register_ptz_management_tool(mcp)
    register_media_management_tool(mcp)
    register_energy_management_tool(mcp)
    register_security_management_tool(mcp)
    register_system_management_tool(mcp)
    register_weather_management_tool(mcp)
    register_configuration_management_tool(mcp)

    logger.info("All portmanteau tools registered successfully")


# Export the registration function
__all__ = ["register_all_portmanteau_tools"]

