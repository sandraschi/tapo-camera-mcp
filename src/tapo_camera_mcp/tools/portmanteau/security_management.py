"""
Security Management Portmanteau Tool

Consolidates all security-related operations into a single tool with action-based interface.
"""

import logging
from typing import Any, Literal

from fastmcp import FastMCP

from tapo_camera_mcp.tools.alarms.nest_protect_tool import NestProtectTool
from tapo_camera_mcp.tools.alarms.security_analysis_tool import SecurityAnalysisTool

logger = logging.getLogger(__name__)

SECURITY_ACTIONS = {
    "nest_status": "Get Nest Protect status",
    "nest_alerts": "Get Nest Protect alerts",
    "nest_battery": "Get Nest Protect battery status",
    "test_nest": "Test Nest Protect device",
    "correlate_events": "Correlate Nest camera events",
    "security_scan": "Perform security scan",
    "analyze_scene": "Analyze camera scene",
}


def register_security_management_tool(mcp: FastMCP) -> None:
    """Register the security management portmanteau tool."""

    @mcp.tool()
    async def security_management(
        action: Literal[
            "nest_status", "nest_alerts", "nest_battery", "test_nest", "correlate_events", "security_scan", "analyze_scene"
        ],
        device_id: str | None = None,
        camera_name: str | None = None,
        hours: int = 24,
        alert_id: str | None = None,
        time_window_minutes: int = 5,
        threat_types: list[str] | None = None,
        save_images: bool = False,
        analysis_type: str | None = None,
        confidence_threshold: float = 0.5,
    ) -> dict[str, Any]:
        """
        Comprehensive security management portmanteau tool.

        PORTMANTEAU PATTERN RATIONALE:
        Instead of creating 7+ separate tools (one per operation), this tool consolidates related
        security operations into a single interface. Prevents tool explosion (7+ tools → 1 tool) while maintaining
        full functionality and improving discoverability. Follows FastMCP 2.12+ best practices.

        Args:
            action (Literal, required): The operation to perform. Must be one of: "nest_status", "nest_alerts",
                "nest_battery", "test_nest", "correlate_events", "security_scan", "analyze_scene".
                - "nest_status": Get Nest Protect status (optional: device_id)
                - "nest_alerts": Get Nest Protect alerts (optional: device_id, hours)
                - "nest_battery": Get Nest Protect battery status (optional: device_id)
                - "test_nest": Test Nest Protect device (optional: device_id)
                - "correlate_events": Correlate Nest camera events (optional: alert_id, time_window_minutes)
                - "security_scan": Perform security scan (requires: camera_name, threat_types)
                - "analyze_scene": Analyze camera scene (requires: camera_name, analysis_type)
            
            device_id (str | None): Device ID for Nest Protect operations. Used by: nest_status, nest_alerts,
                nest_battery, test_nest operations.
            
            camera_name (str | None): Camera name for security scan/analysis. Required for: security_scan,
                analyze_scene operations.
            
            hours (int): Hours to look back for alerts. Used by: nest_alerts operation. Default: 24
            
            alert_id (str | None): Alert ID for correlation. Used by: correlate_events operation.
            
            time_window_minutes (int): Time window for event correlation. Used by: correlate_events operation.
                Default: 5
            
            threat_types (list[str] | None): Threat types to detect. Required for: security_scan operation.
                Default: ["person", "package"]. Valid: "person", "package", "vehicle", "animal"
            
            save_images (bool): Save images from scan. Used by: security_scan, analyze_scene operations.
                Default: False
            
            analysis_type (str | None): Type of scene analysis. Required for: analyze_scene operation.
                Valid: "objects", "faces", "motion", "security"
            
            confidence_threshold (float): Confidence threshold for analysis. Used by: analyze_scene operation.
                Default: 0.5. Range: 0.0 to 1.0

        Returns:
            dict[str, Any]: Dictionary containing:
                - success (bool): Boolean indicating if operation succeeded
                - action (str): The action that was performed
                - data (dict): Operation-specific result data (status, alerts, threats, etc.)
                - error (str | None): Error message if success is False

        Examples:
            # Get Nest Protect status
            result = await security_management(action="nest_status", device_id="nest_001")

            # Get alerts
            result = await security_management(action="nest_alerts", hours=48)

            # Security scan
            result = await security_management(action="security_scan", camera_name="Front Door", threat_types=["person", "package"])

            # Analyze scene
            result = await security_management(action="analyze_scene", camera_name="Front Door", analysis_type="security")
        """
        try:
            if action not in SECURITY_ACTIONS:
                return {
                    "success": False,
                    "error": f"Invalid action '{action}'. Available: {list(SECURITY_ACTIONS.keys())}",
                }

            logger.info(f"Executing security management action: {action}")

            if action in ["nest_status", "nest_alerts", "nest_battery", "test_nest", "correlate_events"]:
                tool = NestProtectTool()
                operation_map = {
                    "nest_status": "status",
                    "nest_alerts": "alerts",
                    "nest_battery": "battery",
                    "test_nest": "test",
                    "correlate_events": "correlate",
                }
                result = await tool.execute(
                    operation=operation_map[action],
                    device_id=device_id,
                    hours=hours,
                    alert_id=alert_id,
                    time_window_minutes=time_window_minutes,
                )
                return {"success": True, "action": action, "data": result}

            elif action in ["security_scan", "analyze_scene"]:
                tool = SecurityAnalysisTool()
                result = await tool.execute(
                    operation=action,
                    camera_name=camera_name,
                    threat_types=threat_types or ["person", "package"],
                    save_images=save_images,
                    analysis_type=analysis_type,
                    confidence_threshold=confidence_threshold,
                )
                return {"success": True, "action": action, "data": result}

            return {"success": False, "error": f"Action '{action}' not implemented"}

        except Exception as e:
            logger.error(f"Error in security management action '{action}': {e}", exc_info=True)
            return {"success": False, "error": f"Failed to execute action '{action}': {str(e)}"}

