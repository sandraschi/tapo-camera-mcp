"""Grafana metrics collection tool."""
import asyncio
import time
from datetime import datetime
from typing import Dict, Any, List
from ..base_tool import BaseTool, ToolCategory

class GrafanaMetricsTool(BaseTool):
    """Tool for collecting camera metrics in Grafana-compatible format."""
    
    class Meta:
        name: str = "get_grafana_metrics"
        description: str = "Export comprehensive camera metrics for Grafana HTTP data source"
        category: ToolCategory = ToolCategory.UTILITY
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Collect all camera metrics for Grafana consumption."""
        try:
            # Get camera manager instance
            camera_manager = self.get_camera_manager()
            
            metrics = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "cameras": {},
                "system": {
                    "active_cameras": 0,
                    "total_cameras": len(camera_manager.cameras),
                    "alerts_pending": 0,
                    "recordings_active": 0,
                    "vienna_context": {
                        "timezone": "Europe/Vienna",
                        "season": self._get_vienna_season(),
                        "heating_period": self._is_heating_period(),
                        "local_time": datetime.now().strftime("%H:%M CET")
                    }
                }
            }
            
            # Collect metrics for each camera
            for camera_id, camera in camera_manager.cameras.items():
                try:
                    # Get camera status and info
                    status = await camera.get_device_info()
                    
                    camera_metrics = {
                        "status": "online" if status.get("online", False) else "offline",
                        "uptime_minutes": status.get("uptime", 0) // 60,
                        "motion_events_1h": await self._get_motion_events(camera_id, hours=1),
                        "motion_events_24h": await self._get_motion_events(camera_id, hours=24),
                        "last_motion_time": await self._get_last_motion_time(camera_id),
                        "recording_active": status.get("recording", False),
                        "temperature_celsius": status.get("temperature", 25.0),
                        "signal_strength_dbm": status.get("wifi_signal", -50),
                        "battery_level": status.get("battery_level", 100),
                        "storage_used_mb": status.get("storage_used", 0),
                        "storage_total_mb": status.get("storage_total", 32000)
                    }
                    
                    metrics["cameras"][camera_id] = camera_metrics
                    
                    # Update system counters
                    if camera_metrics["status"] == "online":
                        metrics["system"]["active_cameras"] += 1
                    if camera_metrics["recording_active"]:
                        metrics["system"]["recordings_active"] += 1
                        
                except Exception as e:
                    # Camera offline or error - provide default metrics
                    metrics["cameras"][camera_id] = {
                        "status": "offline",
                        "error": str(e),
                        "uptime_minutes": 0,
                        "motion_events_1h": 0,
                        "motion_events_24h": 0,
                        "recording_active": False
                    }
            
            return {
                "success": True,
                "data": metrics,
                "content_type": "application/json"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to collect metrics: {str(e)}",
                "data": {"timestamp": datetime.utcnow().isoformat() + "Z", "cameras": {}}
            }
    
    def _get_vienna_season(self) -> str:
        """Get current season in Vienna."""
        month = datetime.now().month
        if month in [12, 1, 2]:
            return "winter"
        elif month in [3, 4, 5]:
            return "spring" 
        elif month in [6, 7, 8]:
            return "summer"
        else:
            return "autumn"
    
    def _is_heating_period(self) -> bool:
        """Check if it's heating period in Vienna (Oct-May)."""
        month = datetime.now().month
        return month >= 10 or month <= 5
    
    async def _get_motion_events(self, camera_id: str, hours: int) -> int:
        """Get motion event count for specified time period."""
        # TODO: Implement motion event counting from camera logs
        # For now, return mock data - replace with actual implementation
        import random
        if hours == 1:
            return random.randint(0, 10)
        else:
            return random.randint(5, 50)
    
    async def _get_last_motion_time(self, camera_id: str) -> str:
        """Get timestamp of last motion detection."""
        # TODO: Implement from actual camera logs
        # For now, return recent time - replace with actual implementation
        recent_time = datetime.utcnow().replace(minute=45, second=23)
        return recent_time.isoformat() + "Z"
