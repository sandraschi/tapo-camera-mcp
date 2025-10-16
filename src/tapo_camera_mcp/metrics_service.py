"""
Metrics collection and serving for Grafana integration.

This module provides real-time camera metrics in a format compatible with Grafana.
"""

from datetime import datetime
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Any, Optional, Union
import asyncio
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class CameraStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    CONNECTING = "connecting"
    ERROR = "error"


@dataclass
class PTZPosition:
    """PTZ position data structure"""

    pan: float = 0.0  # -1.0 (left) to 1.0 (right)
    tilt: float = 0.0  # -1.0 (down) to 1.0 (up)
    zoom: float = 0.0  # 0.0 (wide) to 1.0 (tele)
    moving: bool = False
    preset_id: Optional[int] = None
    preset_name: Optional[str] = None


@dataclass
class CameraMetrics:
    """Camera metrics data structure"""

    camera_id: str
    name: str
    ip_address: str
    model: str = ""
    firmware: str = ""
    status: CameraStatus = CameraStatus.OFFLINE
    last_seen: Optional[datetime] = None
    uptime_seconds: int = 0
    temperature: Optional[float] = None
    motion_detected: bool = False
    motion_last_detected: Optional[datetime] = None
    motion_zones: List[Dict[str, Any]] = field(default_factory=list)
    cpu_usage: Optional[float] = None
    memory_usage: Optional[float] = None
    network_rx: Optional[int] = None  # bytes received
    network_tx: Optional[int] = None  # bytes transmitted
    signal_strength: Optional[int] = None  # WiFi signal strength in dBm
    last_error: Optional[str] = None
    custom_metadata: Dict[str, Any] = field(default_factory=dict)

    # PTZ related fields
    ptz_supported: bool = False
    ptz_position: PTZPosition = field(default_factory=PTZPosition)
    ptz_presets: Dict[int, str] = field(default_factory=dict)  # preset_id: preset_name

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary for JSON serialization"""
        data = asdict(self)
        # Convert datetime to ISO format
        for field in ["last_seen", "motion_last_detected"]:
            if data[field]:
                data[field] = data[field].isoformat()
        # Convert Enum to string
        if "status" in data and data["status"]:
            data["status"] = data["status"].value
        # Convert PTZPosition to dict
        if "ptz_position" in data and data["ptz_position"]:
            data["ptz_position"] = asdict(data["ptz_position"])
        return data


class MetricsCollector:
    """Collect and aggregate camera metrics"""

    def __init__(self, tapo_client):
        self.tapo_client = tapo_client
        self.metrics: Dict[str, CameraMetrics] = {}
        self._running = False
        self._task = None

    async def start(self):
        """Start the metrics collection service"""
        if self._running:
            return

        self._running = True
        self._task = asyncio.create_task(self._collect_loop())
        logger.info("Metrics collection service started")

    async def stop(self):
        """Stop the metrics collection service"""
        if not self._running:
            return

        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Metrics collection service stopped")

    async def _collect_loop(self):
        """Background task to collect metrics at regular intervals"""
        while self._running:
            try:
                await self.collect_metrics()
                await asyncio.sleep(30)  # Collect every 30 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in metrics collection: {e}")
                await asyncio.sleep(30)  # Wait before retry

    async def collect_metrics(self):
        """Collect metrics from all cameras"""
        # This would be implemented to collect actual metrics from Tapo cameras
        # For now, we'll just update the last_seen timestamp
        for camera_id, metrics in self.metrics.items():
            if metrics.status == CameraStatus.ONLINE:
                metrics.last_seen = datetime.now()

    def get_grafana_metrics(self) -> Dict[str, Any]:
        """Format metrics for Grafana consumption"""
        timestamp = datetime.now().isoformat()

        # Convert all metrics to Grafana-compatible format
        metrics = {"status": "success", "data": {"resultType": "matrix", "result": []}}

        # Add each metric as a separate time series
        for camera_id, camera_metrics in self.metrics.items():
            # Add status metric
            self._add_metric(
                metrics,
                "camera_status",
                {
                    "camera_id": camera_id,
                    "name": camera_metrics.name,
                    "model": camera_metrics.model,
                    "status": camera_metrics.status.value,
                },
                timestamp,
                1 if camera_metrics.status == CameraStatus.ONLINE else 0,
            )

            # Add temperature metric if available
            if camera_metrics.temperature is not None:
                self._add_metric(
                    metrics,
                    "camera_temperature",
                    {"camera_id": camera_id, "name": camera_metrics.name},
                    timestamp,
                    camera_metrics.temperature,
                )

            # Add motion detection metric
            self._add_metric(
                metrics,
                "motion_detected",
                {"camera_id": camera_id, "name": camera_metrics.name},
                timestamp,
                1 if camera_metrics.motion_detected else 0,
            )

            # Add network metrics if available
            if camera_metrics.network_rx is not None:
                self._add_metric(
                    metrics,
                    "network_rx_bytes",
                    {"camera_id": camera_id, "name": camera_metrics.name},
                    timestamp,
                    camera_metrics.network_rx,
                )

            if camera_metrics.network_tx is not None:
                self._add_metric(
                    metrics,
                    "network_tx_bytes",
                    {"camera_id": camera_id, "name": camera_metrics.name},
                    timestamp,
                    camera_metrics.network_tx,
                )

            # Add signal strength if available
            if camera_metrics.signal_strength is not None:
                self._add_metric(
                    metrics,
                    "signal_strength_dbm",
                    {"camera_id": camera_id, "name": camera_metrics.name},
                    timestamp,
                    camera_metrics.signal_strength,
                )

            # Add PTZ metrics if supported
            if camera_metrics.ptz_supported:
                # PTZ Position
                for axis in ["pan", "tilt", "zoom"]:
                    if hasattr(camera_metrics.ptz_position, axis):
                        self._add_metric(
                            metrics,
                            f"ptz_{axis}",
                            {"camera_id": camera_id, "name": camera_metrics.name},
                            timestamp,
                            getattr(camera_metrics.ptz_position, axis),
                        )

                # PTZ Moving state
                self._add_metric(
                    metrics,
                    "ptz_moving",
                    {"camera_id": camera_id, "name": camera_metrics.name},
                    timestamp,
                    1 if camera_metrics.ptz_position.moving else 0,
                )

                # PTZ Preset
                if camera_metrics.ptz_position.preset_id is not None:
                    self._add_metric(
                        metrics,
                        "ptz_preset",
                        {
                            "camera_id": camera_id,
                            "name": camera_metrics.name,
                            "preset_id": str(camera_metrics.ptz_position.preset_id),
                            "preset_name": camera_metrics.ptz_position.preset_name
                            or "",
                        },
                        timestamp,
                        camera_metrics.ptz_position.preset_id,
                    )

        return metrics

    def _add_metric(
        self,
        metrics: Dict[str, Any],
        metric_name: str,
        labels: Dict[str, str],
        timestamp: str,
        value: Union[int, float],
    ) -> None:
        """Add a metric to the Grafana response"""
        metric = {
            "metric": {"__name__": metric_name, **labels},
            "values": [[timestamp, value]],
        }
        metrics["data"]["result"].append(metric)


class MetricsServer:
    """HTTP server providing metrics endpoint for Grafana"""

    def __init__(
        self,
        metrics_collector: MetricsCollector,
        host: str = "0.0.0.0",
        port: int = 8080,
    ):
        self.metrics_collector = metrics_collector
        self.host = host
        self.port = port
        self._server = None

    async def start(self):
        """Start the metrics server"""
        try:
            from fastapi import FastAPI, HTTPException
            from fastapi.middleware.cors import CORSMiddleware
            import uvicorn

            app = FastAPI(title="Tapo Camera MCP Metrics")

            # Enable CORS
            app.add_middleware(
                CORSMiddleware,
                allow_origins=["*"],
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )

            @app.get("/api/health")
            async def health_check():
                return {"status": "ok"}

            @app.get("/api/metrics")
            async def get_metrics():
                return self.metrics_collector.get_grafana_metrics()

            @app.get("/api/cameras")
            async def list_cameras():
                return {
                    camera_id: metrics.to_dict()
                    for camera_id, metrics in self.metrics_collector.metrics.items()
                }

            config = uvicorn.Config(
                app, host=self.host, port=self.port, log_level="info"
            )
            self._server = uvicorn.Server(config)
            await self._server.serve()

        except ImportError as e:
            logger.error(f"Failed to start metrics server: {e}")
            logger.error(
                "Please install the required dependencies with: pip install fastapi uvicorn"
            )
            raise

    async def stop(self):
        """Stop the metrics server"""
        if self._server:
            self._server.should_exit = True
            await self._server.shutdown()
            self._server = None
