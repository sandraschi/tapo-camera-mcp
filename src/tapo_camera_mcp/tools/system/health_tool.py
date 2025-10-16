"""
Dedicated health check tool for comprehensive system monitoring.
"""

import logging
import time
from datetime import datetime
from typing import Any, Dict

from pydantic import BaseModel, Field

from tapo_camera_mcp.tools.base_tool import BaseTool, ToolCategory, tool

logger = logging.getLogger(__name__)


class HealthCheckResult(BaseModel):
    """Result of a comprehensive health check."""

    status: str = Field(..., description="Overall health status: healthy/warning/critical")
    checks: Dict[str, Any] = Field(..., description="Individual health check results")
    response_time_ms: float = Field(..., description="Time taken for health check")
    timestamp: str = Field(..., description="Timestamp of health check")


@tool(name="health_check")
class HealthCheckTool(BaseTool):
    """Tool for comprehensive health monitoring and diagnostics."""

    class Meta:
        name = "health_check"
        description = "Perform comprehensive health check of the MCP server and cameras"
        category = ToolCategory.SYSTEM

        class Parameters:
            include_cameras: bool = Field(
                True, description="Whether to include camera health checks"
            )
            include_performance: bool = Field(
                True, description="Whether to include performance metrics"
            )

    include_cameras: bool = True
    include_performance: bool = True

    def __init__(self, **data):
        super().__init__(**data)
        self._performance_metrics = {
            "response_times": [],
            "last_reset": datetime.utcnow(),
        }

    async def execute(self) -> Dict[str, Any]:
        """Perform comprehensive health check."""
        start_time = time.time()

        try:
            # Core server health
            server_health = await self._check_server_health()

            # System resource health
            system_health = await self._check_system_health()

            # Camera health (if requested)
            camera_health = {}
            if self.include_cameras:
                camera_health = await self._check_camera_health()

            # Performance metrics (if requested)
            performance_metrics = {}
            if self.include_performance:
                performance_metrics = await self._get_performance_metrics()

            # Overall status determination
            all_checks = {
                "server": server_health,
                "system": system_health,
                **camera_health,
                **performance_metrics,
            }

            # Determine overall status
            critical_issues = [
                name for name, check in all_checks.items() if check.get("status") == "critical"
            ]
            warning_issues = [
                name for name, check in all_checks.items() if check.get("status") == "warning"
            ]

            if critical_issues:
                overall_status = "critical"
            elif warning_issues:
                overall_status = "warning"
            else:
                overall_status = "healthy"

            response_time_ms = (time.time() - start_time) * 1000

            result = HealthCheckResult(
                status=overall_status,
                checks=all_checks,
                response_time_ms=response_time_ms,
                timestamp=datetime.utcnow().isoformat(),
            )

            logger.info(f"Health check completed: {overall_status} ({response_time_ms:.1f}ms)")
            return result.dict()

        except Exception as e:
            logger.exception(f"Health check failed: {e}")
            response_time_ms = (time.time() - start_time) * 1000
            return HealthCheckResult(
                status="critical",
                checks={"error": {"status": "critical", "message": str(e)}},
                response_time_ms=response_time_ms,
                timestamp=datetime.utcnow().isoformat(),
            ).dict()

    async def _check_server_health(self) -> Dict[str, Any]:
        """Check MCP server health."""
        try:
            # Check if server is responsive by testing basic operations
            from tapo_camera_mcp.core.server import TapoCameraServer

            server = await TapoCameraServer.get_instance()

            # Basic responsiveness check
            server_responsive = hasattr(server, "mcp") and server.mcp is not None

            # Check for registered tools
            tools_count = len(server.mcp.list_tools()) if server_responsive else 0

            issues = []
            if not server_responsive:
                issues.append("Server not properly initialized")

            status = "critical" if issues else "healthy"

            return {
                "status": status,
                "responsive": server_responsive,
                "tools_registered": tools_count,
                "issues": issues,
            }

        except Exception as e:
            logger.exception(f"Server health check failed: {e}")
            return {"status": "critical", "error": str(e), "issues": [str(e)]}

    async def _check_system_health(self) -> Dict[str, Any]:
        """Check system resource health."""
        try:
            import psutil

            # Get resource usage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            issues = []

            # Check thresholds
            if cpu_percent > 90:
                issues.append(f"Critical CPU usage: {cpu_percent}%")
            elif cpu_percent > 80:
                issues.append(f"High CPU usage: {cpu_percent}%")

            if memory.percent > 95:
                issues.append(f"Critical memory usage: {memory.percent}%")
            elif memory.percent > 85:
                issues.append(f"High memory usage: {memory.percent}%")

            if disk.percent > 95:
                issues.append(f"Critical disk usage: {disk.percent}%")
            elif disk.percent > 90:
                issues.append(f"High disk usage: {disk.percent}%")

            # Determine status
            if any("Critical" in issue for issue in issues):
                status = "critical"
            elif issues:
                status = "warning"
            else:
                status = "healthy"

            return {
                "status": status,
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": disk.percent,
                "issues": issues,
            }

        except Exception as e:
            logger.exception(f"System health check failed: {e}")
            return {"status": "critical", "error": str(e), "issues": [str(e)]}

    async def _check_camera_health(self) -> Dict[str, Any]:
        """Check camera connectivity and health."""
        try:
            from tapo_camera_mcp.core.server import TapoCameraServer

            server = await TapoCameraServer.get_instance()
            camera_manager = server.camera_manager

            if not camera_manager:
                return {
                    "status": "no_manager",
                    "issues": ["No camera manager available"],
                }

            cameras = camera_manager.get_cameras()
            total_cameras = len(cameras)
            online_cameras = 0
            issues = []

            # Check each camera
            for camera in cameras:
                try:
                    if camera.is_online():
                        online_cameras += 1
                    else:
                        issues.append(f"Camera {camera.id} is offline")
                except Exception as e:
                    issues.append(f"Error checking camera {camera.id}: {e!s}")

            # Overall camera health
            if total_cameras == 0:
                camera_status = "no_cameras"
            elif online_cameras == 0:
                camera_status = "critical"
                issues.append("No cameras are online")
            elif online_cameras < total_cameras:
                camera_status = "warning"
            else:
                camera_status = "healthy"

            return {
                "status": camera_status,
                "total_cameras": total_cameras,
                "online_cameras": online_cameras,
                "issues": issues,
            }

        except Exception as e:
            logger.exception(f"Camera health check failed: {e}")
            return {"status": "critical", "error": str(e), "issues": [str(e)]}

    async def _get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance monitoring metrics."""
        try:
            # Record this health check response time
            self._performance_metrics["response_times"].append(time.time())

            # Clean old metrics (keep last 100)
            if len(self._performance_metrics["response_times"]) > 100:
                self._performance_metrics["response_times"] = self._performance_metrics[
                    "response_times"
                ][-100:]

            # Calculate metrics
            response_times = self._performance_metrics["response_times"]
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0

            import psutil

            process = psutil.Process()
            memory_mb = process.memory_info().rss / (1024 * 1024)

            return {
                "status": "healthy",
                "avg_response_time_ms": avg_response_time * 1000,
                "memory_usage_mb": memory_mb,
                "cpu_usage_percent": process.cpu_percent(),
                "health_checks_count": len(response_times),
            }

        except Exception as e:
            logger.exception(f"Performance metrics failed: {e}")
            return {"status": "warning", "error": str(e)}
