"""
Robotics Management Portmanteau Tool

Consolidates all robotics-related operations into a single tool with action-based interface.
Currently supports Moorebot Scout robot with ROS 1.4 compatibility.
"""

import logging
from typing import Any, Literal

from fastmcp import FastMCP

from ...tools.robotics.moorebot_tools import (
    get_moorebot_client,
    initialize_moorebot_client,
    moorebot_get_camera_stream,
    moorebot_get_sensors,
    moorebot_get_status,
    moorebot_move,
    moorebot_patrol,
    moorebot_return_to_dock,
    moorebot_stop_patrol,
)

logger = logging.getLogger(__name__)

ROBOTICS_ACTIONS = {
    "get_status": "Get robot status (battery, position, sensors)",
    "move": "Move robot with specified velocities",
    "patrol": "Start autonomous patrol route",
    "stop_patrol": "Stop current patrol",
    "return_to_dock": "Return robot to charging dock",
    "get_sensors": "Get current sensor readings (ToF, IMU, light)",
    "get_camera_stream": "Get camera stream URLs (RTSP)",
    "initialize": "Initialize robot client connection",
}


def register_robotics_management_tool(mcp: FastMCP) -> None:
    """Register the robotics management portmanteau tool."""

    @mcp.tool()
    async def robotics_management(
        action: Literal[
            "get_status",
            "move",
            "patrol",
            "stop_patrol",
            "return_to_dock",
            "get_sensors",
            "get_camera_stream",
            "initialize",
        ],
        route: str | None = None,
        linear_velocity: float = 0.0,
        angular_velocity: float = 0.0,
        duration: float = 0.0,
        ip_address: str | None = None,
        mock_mode: bool = True,
    ) -> dict[str, Any]:
        """
        Comprehensive robotics management portmanteau tool for Moorebot Scout.

        PORTMANTEAU PATTERN RATIONALE:
        Consolidates robotics operations into a single interface to reduce tool explosion
        while maintaining full functionality. Supports Moorebot Scout with ROS 1.4 compatibility,
        including autonomous patrol, sensor integration, and camera streaming.

        Args:
            action (Literal, required): The operation to perform. Must be one of:
                - "get_status": Get robot status (battery, position, sensors)
                - "move": Move robot with specified velocities (requires: linear_velocity, angular_velocity, optional: duration)
                - "patrol": Start autonomous patrol route (optional: route name, default: "default")
                - "stop_patrol": Stop current patrol
                - "return_to_dock": Return robot to charging dock
                - "get_sensors": Get current sensor readings (ToF, IMU, light)
                - "get_camera_stream": Get camera stream URLs (RTSP)
                - "initialize": Initialize robot client connection (requires: ip_address, optional: mock_mode)

            route (str | None): Patrol route name for patrol action
                - "default": Living room -> Bedroom -> Kitchen -> Home
                - "perimeter": Full apartment perimeter
                - "rooms": Quick check of all rooms

            linear_velocity (float): Linear velocity in m/s for move action (range: -0.3 to 0.3)
                - Positive: forward, Negative: backward

            angular_velocity (float): Angular velocity in rad/s for move action (range: -2.0 to 2.0)
                - Positive: counter-clockwise, Negative: clockwise

            duration (float): Movement duration in seconds for move action (0 = continuous)

            ip_address (str | None): Robot IP address for initialize action

            mock_mode (bool): Use mock mode for testing (default: True)

        Returns:
            dict[str, Any]: Dictionary containing:
                - success (bool): Boolean indicating if operation succeeded
                - action (str): The action that was performed
                - data (dict): Operation-specific result data (status, sensors, streams, etc.)
                - error (str | None): Error message if success is False

        Examples:
            # Initialize robot client
            result = await robotics_management(action="initialize", ip_address="192.168.1.100", mock_mode=False)

            # Get robot status
            result = await robotics_management(action="get_status")

            # Move forward for 3 seconds
            result = await robotics_management(action="move", linear_velocity=0.2, duration=3.0)

            # Start default patrol
            result = await robotics_management(action="patrol", route="default")

            # Stop patrol
            result = await robotics_management(action="stop_patrol")

            # Return to dock
            result = await robotics_management(action="return_to_dock")

            # Get sensor readings
            result = await robotics_management(action="get_sensors")

            # Get camera streams
            result = await robotics_management(action="get_camera_stream")
        """
        try:
            if action not in ROBOTICS_ACTIONS:
                return {
                    "success": False,
                    "error": f"Invalid action '{action}'. Available: {list(ROBOTICS_ACTIONS.keys())}",
                }

            logger.info(f"Executing robotics management action: {action}")

            if action == "initialize":
                if not ip_address:
                    return {
                        "success": False,
                        "error": "ip_address is required for initialize action",
                    }
                initialize_moorebot_client(ip_address, mock_mode)
                return {
                    "success": True,
                    "action": action,
                    "data": {
                        "ip_address": ip_address,
                        "mock_mode": mock_mode,
                        "message": f"Moorebot client initialized at {ip_address} (mock: {mock_mode})",
                    },
                }

            # All other actions require a client
            try:
                get_moorebot_client()  # Check if initialized
            except RuntimeError:
                return {
                    "success": False,
                    "error": "Robot client not initialized. Use initialize action first.",
                }

            if action == "get_status":
                result = await moorebot_get_status()
                return {"success": True, "action": action, "data": result}

            if action == "move":
                result = await moorebot_move(linear_velocity, angular_velocity, duration)
                return {"success": True, "action": action, "data": result}

            if action == "patrol":
                patrol_route = route or "default"
                result = await moorebot_patrol(patrol_route)
                return {"success": True, "action": action, "data": result}

            if action == "stop_patrol":
                result = await moorebot_stop_patrol()
                return {"success": True, "action": action, "data": result}

            if action == "return_to_dock":
                result = await moorebot_return_to_dock()
                return {"success": True, "action": action, "data": result}

            if action == "get_sensors":
                result = await moorebot_get_sensors()
                return {"success": True, "action": action, "data": result}

            if action == "get_camera_stream":
                result = await moorebot_get_camera_stream()
                return {"success": True, "action": action, "data": result}

            return {"success": False, "error": f"Action '{action}' not implemented"}

        except Exception as e:
            logger.error(f"Error in robotics management action '{action}': {e}", exc_info=True)
            return {"success": False, "error": f"Failed to execute action '{action}': {e!s}"}
