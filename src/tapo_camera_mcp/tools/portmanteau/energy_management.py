"""
Energy Management Portmanteau Tool

Consolidates all energy-related operations into a single tool with action-based interface.
"""

import logging
from typing import Any, Literal

from fastmcp import FastMCP

from tapo_camera_mcp.tools.energy.energy_management_tool import EnergyManagementTool

logger = logging.getLogger(__name__)

ENERGY_ACTIONS = {
    "status": "Get smart plug status",
    "control": "Control smart plug (on/off)",
    "consumption": "Get energy consumption data",
    "cost": "Get energy cost analysis",
}


def register_energy_management_tool(mcp: FastMCP) -> None:
    """Register the energy management portmanteau tool."""

    @mcp.tool()
    async def energy_management(
        action: Literal["status", "control", "consumption", "cost"],
        device_id: str | None = None,
        power_state: str | None = None,
        time_range: str = "24h",
    ) -> dict[str, Any]:
        """
        Comprehensive energy management portmanteau tool.

        PORTMANTEAU PATTERN RATIONALE:
        Instead of creating 4+ separate tools (one per operation), this tool consolidates related
        energy operations into a single interface. Prevents tool explosion (4+ tools → 1 tool) while maintaining
        full functionality and improving discoverability. Follows FastMCP 2.12+ best practices.

        Args:
            action (Literal, required): The operation to perform. Must be one of: "status", "control",
                "consumption", "cost".
                - "status": Get smart plug status (optional: device_id for specific device)
                - "control": Control smart plug power (requires: device_id, power_state)
                - "consumption": Get energy consumption data (optional: device_id, time_range)
                - "cost": Get energy cost analysis (optional: device_id, time_range)
            
            device_id (str | None): Smart plug device ID. Required for: control operation.
                Optional for: status, consumption, cost operations (filters to specific device).
            
            power_state (str | None): Power state for control. Required for: control operation.
                Valid: "on", "off", "toggle"
            
            time_range (str): Time range for consumption/cost analysis. Used by: consumption, cost operations.
                Default: "24h". Valid: "1h", "24h", "7d", "30d"

        Returns:
            dict[str, Any]: Dictionary containing:
                - success (bool): Boolean indicating if operation succeeded
                - action (str): The action that was performed
                - data (dict): Operation-specific result data (status, consumption, cost, etc.)
                - error (str | None): Error message if success is False

        Examples:
            # Get status of all devices
            result = await energy_management(action="status")

            # Control specific device
            result = await energy_management(action="control", device_id="tapo_001", power_state="on")

            # Get consumption data
            result = await energy_management(action="consumption", time_range="7d")

            # Get cost analysis
            result = await energy_management(action="cost", device_id="tapo_001", time_range="30d")
        """
        try:
            if action not in ENERGY_ACTIONS:
                return {
                    "success": False,
                    "error": f"Invalid action '{action}'. Available: {list(ENERGY_ACTIONS.keys())}",
                }

            logger.info(f"Executing energy management action: {action}")

            tool = EnergyManagementTool()
            result = await tool.execute(
                operation=action,
                device_id=device_id,
                action=power_state,
                time_range=time_range,
            )
            return {"success": True, "action": action, "data": result}

        except Exception as e:
            logger.error(f"Error in energy management action '{action}': {e}", exc_info=True)
            return {"success": False, "error": f"Failed to execute action '{action}': {str(e)}"}

