"""
Status tool for monitoring system health and camera status in Tapo Camera MCP.
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import psutil
import os

from ...mcp_integration import tool, ToolCategory, BaseTool

class SystemStatus(BaseModel):
    cpu_percent: float = Field(..., description="CPU usage percentage")
    memory_percent: float = Field(..., description="Memory usage percentage")
    disk_usage: float = Field(..., description="Disk usage percentage")
    uptime: str = Field(..., description="System uptime")
    active_cameras: int = Field(..., description="Number of active camera connections")
    active_streams: int = Field(..., description="Number of active streams")
    last_updated: str = Field(..., description="Timestamp of last status update")

class CameraStatus(BaseModel):
    camera_id: str = Field(..., description="Unique camera identifier")
    model: str = Field(..., description="Camera model")
    status: str = Field(..., description="Connection status")
    last_seen: str = Field(..., description="Last successful connection time")
    stream_status: str = Field(..., description="Current stream status")
    fps: float = Field(..., description="Current FPS if streaming")
    resolution: str = Field(..., description="Current stream resolution")

@tool(name="get_status")
class StatusTool(BaseTool):
    """Tool to get system and camera status information."""
    
    class Meta:
        category = ToolCategory.SYSTEM
    
    detail_level: str = Field(
        default="basic",
        enum=["basic", "detailed", "cameras"],
        description="Level of detail in the status report"
    )

    def __init__(self, **data):
        super().__init__(**data)
        from ...core.server import TapoCameraServer
        self.server = TapoCameraServer.get_instance()
        self.camera_manager = self.server.camera_manager

    async def execute(self) -> Dict[str, Any]:
        """Return system and camera status information."""
        status = self._get_system_status()
        
        # Get camera status if needed
        if self.detail_level in ["detailed", "cameras"] and self.camera_manager:
            status["cameras"] = await self._get_camera_statuses()
            
            # Include additional system details for detailed mode
            if self.detail_level == "detailed":
                status.update(await self._get_detailed_system_status())
        
        return status

    async def _get_system_status(self) -> Dict[str, Any]:
        """Get basic system status information."""
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent,
            "uptime": self._format_uptime(psutil.boot_time()),
            "active_cameras": len(self.camera_manager.get_active_cameras()) if self.camera_manager else 0,
            "active_streams": len(self.camera_manager.get_active_streams()) if self.camera_manager else 0,
            "last_updated": datetime.utcnow().isoformat()
        }

    async def _get_cameras_status(self) -> List[Dict[str, Any]]:
        """Get status for all cameras."""
        if not self.camera_manager:
            return []
            
        cameras_status = []
        for camera in self.camera_manager.get_cameras():
            stream = self.camera_manager.get_camera_stream(camera.id)
            cameras_status.append({
                "camera_id": camera.id,
                "model": camera.model,
                "status": "online" if camera.is_online() else "offline",
                "last_seen": camera.last_seen.isoformat() if camera.last_seen else "never",
                "stream_status": "active" if stream and stream.is_active() else "inactive",
                "fps": stream.get_fps() if stream else 0.0,
                "resolution": f"{stream.width}x{stream.height}" if stream else "N/A"
            })
        return cameras_status

    def _get_grafana_status(self) -> Dict[str, Any]:
        """Get Grafana integration status."""
        return {
            "plugin_installed": os.path.exists("/var/lib/grafana/plugins/tapo-camera-stream"),
            "dashboards_imported": len(self._find_grafana_dashboards()) > 0,
            "api_accessible": self._check_grafana_api()
        }

    def _get_storage_status(self) -> Dict[str, Any]:
        """Get storage usage information."""
        return {
            "total_recordings": self._count_recordings(),
            "storage_used_gb": self._get_storage_used_gb(),
            "retention_days": self._get_retention_days()
        }

    def _get_network_status(self) -> Dict[str, Any]:
        """Get network status information."""
        net_io = psutil.net_io_counters()
        return {
            "bytes_sent_mb": net_io.bytes_sent / (1024 * 1024),
            "bytes_recv_mb": net_io.bytes_recv / (1024 * 1024),
            "active_connections": len(psutil.net_connections())
        }

    def _format_uptime(self, boot_time: float) -> str:
        """Format system uptime as a human-readable string."""
        uptime_seconds = datetime.now().timestamp() - boot_time
        days, remainder = divmod(int(uptime_seconds), 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, _ = divmod(remainder, 60)
        return f"{days}d {hours}h {minutes}m"

    def _find_grafana_dashboards(self) -> List[str]:
        """Find all Grafana dashboards."""
        # Implementation depends on your dashboard storage
        return []

    def _check_grafana_api(self) -> bool:
        """Check if Grafana API is accessible."""
        # Implementation depends on your setup
        return False

    def _count_recordings(self) -> int:
        """Count number of stored recordings."""
        # Implementation depends on your storage
        return 0

    def _get_storage_used_gb(self) -> float:
        """Get storage used in GB."""
        # Implementation depends on your storage
        return 0.0

    def _get_retention_days(self) -> int:
        """Get configured retention period in days."""
        # Implementation depends on your configuration
        return 30
