"""
Connection Supervisor - Ensures all devices stay connected and healthy.

Polls all devices at regular intervals, auto-reconnects on failure,
and provides comprehensive health monitoring for demo reliability.
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class DeviceHealth:
    """Health status for a device."""
    device_id: str
    device_type: str  # camera, plug, light, weather, ring
    name: str
    connected: bool
    last_check: datetime
    last_success: Optional[datetime]
    error_count: int
    last_error: Optional[str]
    details: Dict[str, Any]


class ConnectionSupervisor:
    """
    Supervisor that polls all devices and maintains connections.
    
    Features:
    - Regular health checks (configurable interval)
    - Auto-reconnect on failure
    - Connection statistics
    - Alert generation for offline devices
    - Graceful degradation (one device failure doesn't crash others)
    """
    
    def __init__(self, poll_interval: int = 60):
        """
        Initialize supervisor.
        
        Args:
            poll_interval: Seconds between health checks (default 60)
        """
        self.poll_interval = poll_interval
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self.device_health: Dict[str, DeviceHealth] = {}
        
        # Messaging service integration
        from .messaging_service import get_messaging_service, MessageSeverity, MessageCategory
        self.messaging = get_messaging_service()
        self.MessageSeverity = MessageSeverity
        self.MessageCategory = MessageCategory
        
    async def start(self):
        """Start the supervisor polling loop."""
        if self._running:
            logger.warning("Supervisor already running")
            return
            
        self._running = True
        self._task = asyncio.create_task(self._poll_loop())
        logger.info(f"Connection supervisor started (polling every {self.poll_interval}s)")
        
    async def stop(self):
        """Stop the supervisor."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Connection supervisor stopped")
        
    async def _poll_loop(self):
        """Main polling loop."""
        while self._running:
            try:
                await self._check_all_devices()
            except Exception:
                logger.exception("Error in supervisor poll loop")
            
            # Wait before next poll
            await asyncio.sleep(self.poll_interval)
            
    async def _check_all_devices(self):
        """Check health of all devices."""
        logger.debug("Supervisor: Checking all devices...")
        
        # Check devices in parallel for speed
        await asyncio.gather(
            self._check_cameras(),
            self._check_plugs(),
            self._check_hue_bridge(),
            self._check_netatmo(),
            self._check_ring(),
            return_exceptions=True  # Don't let one failure crash others
        )
        
    async def _check_cameras(self):
        """Check all cameras."""
        try:
            from ..camera.manager import CameraManager
            from ..core.server import TapoCameraServer
            
            # Add timeout to prevent blocking
            try:
                server = await asyncio.wait_for(
                    TapoCameraServer.get_instance(),
                    timeout=5.0
                )
                cameras = await asyncio.wait_for(
                    server.camera_manager.list_cameras(),
                    timeout=5.0
                )
            except asyncio.TimeoutError:
                logger.warning("Camera manager access timed out - skipping camera checks this cycle")
                return
            
            for cam in cameras:
                device_id = f"camera_{cam['name']}"
                status = cam.get('status', {})
                connected = status.get('connected', False) if isinstance(status, dict) else False
                cam_type = cam.get('type', 'unknown')
                
                # Check if USB camera is in use by another application
                in_use = status.get('in_use_by_another_app', False) if isinstance(status, dict) else False
                in_use_error = status.get('in_use_error') or status.get('warning') if isinstance(status, dict) else None
                
                # Determine error message
                error_msg = None
                if in_use:
                    error_msg = in_use_error or "Camera in use by another application (e.g., Microsoft Teams, Zoom)"
                elif not connected:
                    error_msg = "Camera offline"
                
                self._update_health(
                    device_id=device_id,
                    device_type="camera",
                    name=cam['name'],
                    connected=connected and not in_use,  # Mark as not connected if in use
                    error=error_msg,
                    details={
                        'model': status.get('model', 'Unknown') if isinstance(status, dict) else 'Unknown',
                        'type': cam_type,
                        'streaming': status.get('streaming', False) if isinstance(status, dict) else False,
                        'in_use_by_another_app': in_use,
                        'device_id': status.get('device_id') if isinstance(status, dict) else None
                    }
                )
                
                # Log warning and send alert if camera is in use
                if in_use:
                    device_id_display = status.get('device_id', '?') if isinstance(status, dict) else '?'
                    warning_msg = f"Camera {cam['name']} (USB device {device_id_display}) is in use by another application. Close Microsoft Teams, Zoom, or other video apps."
                    logger.warning(warning_msg)
                    
                    # Send alert message
                    try:
                        from .messaging_service import get_messaging_service, MessageSeverity, MessageCategory
                        messaging = get_messaging_service()
                        messaging.add_message(
                            severity=MessageSeverity.WARNING,
                            category=MessageCategory.DEVICE_CONNECTION,
                            source=device_id,
                            title=f"Camera {cam['name']} Locked by Another Application",
                            description=in_use_error or warning_msg,
                            details={
                                "device_type": "camera",
                                "device_id": device_id,
                                "camera_name": cam['name'],
                                "usb_device_id": status.get('device_id') if isinstance(status, dict) else None,
                                "in_use_by_another_app": True
                            }
                        )
                    except Exception:
                        pass  # Don't fail if messaging service unavailable
                
                # Auto-reconnect if offline (but not if in use - that requires user action)
                if not connected and not in_use and cam_type in ['onvif', 'tapo']:
                    logger.warning(f"Camera {cam['name']} offline, attempting reconnect...")
                    try:
                        # Try to reconnect camera
                        pass  # Camera manager handles reconnection
                    except Exception as e:
                        logger.error(f"Failed to reconnect {cam['name']}: {e}")
                        
        except Exception as e:
            logger.exception("Error checking cameras")
            
    async def _check_plugs(self):
        """Check Tapo P115 smart plugs."""
        try:
            # Check if tapo library available
            try:
                import tapo
                tapo_available = True
            except ImportError:
                tapo_available = False
                logger.warning("tapo library not installed - cannot check P115 plugs")
                self._update_health(
                    device_id="plugs_system",
                    device_type="plug",
                    name="Tapo P115 System",
                    connected=False,
                    error="tapo library not installed",
                    details={'library_missing': True}
                )
                return
            
            from ..config import get_config
            config = get_config()
            plugs_config = config.get('energy', {}).get('tapo_p115', {}).get('devices', [])
            
            for plug_cfg in plugs_config:
                device_id = plug_cfg.get('device_id', 'unknown')
                name = plug_cfg.get('name', device_id)
                host = plug_cfg.get('host')
                
                # Try to query plug
                try:
                    account_email = config.get('energy', {}).get('tapo_p115', {}).get('account', {}).get('email')
                    account_password = config.get('energy', {}).get('tapo_p115', {}).get('account', {}).get('password')
                    
                    if not account_email or not account_password:
                        raise ValueError("Missing Tapo account credentials")
                    
                    # Quick connection test
                    device = await tapo.ApiClient(account_email, account_password).p115(host)
                    info = await device.get_device_info()
                    energy = await device.get_energy_usage()
                    
                    self._update_health(
                        device_id=f"plug_{device_id}",
                        device_type="plug",
                        name=name,
                        connected=True,
                        error=None,
                        details={
                            'power': energy.current_power if energy else 0,
                            'host': host,
                            'model': info.model if info else 'P115'
                        }
                    )
                except Exception as e:
                    self._update_health(
                        device_id=f"plug_{device_id}",
                        device_type="plug",
                        name=name,
                        connected=False,
                        error=str(e),
                        details={'host': host}
                    )
                    logger.warning(f"Plug {name} offline: {e}")
                    
        except Exception:
            logger.exception("Error checking plugs")
            
    async def _check_hue_bridge(self):
        """Check Philips Hue Bridge."""
        try:
            from ..tools.lighting.hue_tools import hue_manager
            
            # Check if phue available
            try:
                import phue
                phue_available = True
            except ImportError:
                phue_available = False
                self._update_health(
                    device_id="hue_bridge",
                    device_type="light",
                    name="Philips Hue Bridge",
                    connected=False,
                    error="phue library not installed",
                    details={'library_missing': True}
                )
                return
            
            # Check connection
            if not hue_manager._initialized:
                await hue_manager.initialize()
            
            connected = hue_manager._initialized and hue_manager._bridge is not None
            
            self._update_health(
                device_id="hue_bridge",
                device_type="light",
                name="Philips Hue Bridge",
                connected=connected,
                error=hue_manager._connection_error if not connected else None,
                details={
                    'bridge_ip': hue_manager._bridge_ip,
                    'lights_count': len(hue_manager.lights),
                    'groups_count': len(hue_manager.groups),
                    'scenes_count': len(hue_manager.scenes)
                }
            )
            
        except Exception:
            logger.exception("Error checking Hue Bridge")
            
    async def _check_netatmo(self):
        """Check Netatmo weather station."""
        try:
            # Check if pyatmo available
            try:
                import pyatmo
                pyatmo_available = True
            except ImportError:
                pyatmo_available = False
                self._update_health(
                    device_id="netatmo_weather",
                    device_type="weather",
                    name="Netatmo Weather Station",
                    connected=False,
                    error="pyatmo library not installed",
                    details={'library_missing': True}
                )
                return
            
            from ..integrations.netatmo_client import NetatmoService
            service = None
            try:
                service = NetatmoService()
                await service.initialize()
                
                connected = service._use_real_api and service._account is not None
                
                if connected:
                    try:
                        stations = await service.list_stations()
                        station_count = len(stations)
                        module_count = sum(len(s.get('modules', [])) for s in stations)
                        
                        self._update_health(
                            device_id="netatmo_weather",
                            device_type="weather",
                            name="Netatmo Weather Station",
                            connected=True,
                            error=None,
                            details={
                                'stations': station_count,
                                'modules': module_count
                            }
                        )
                    except Exception as e:
                        error_msg = str(e)
                        error_type = type(e).__name__
                        
                        # Handle DNS/network errors with specific messages
                        if "getaddrinfo failed" in error_msg or "ClientConnectorDNSError" in error_type:
                            error_msg = "DNS resolution failed (Python/aiohttp resolver issue - may be IPv6/IPv4 conflict)"
                        elif "Cannot connect to host" in error_msg:
                            error_msg = f"Cannot connect to api.netatmo.com (firewall/proxy blocking or IPv6 issue)"
                        elif "timeout" in error_msg.lower():
                            error_msg = "Connection timeout to Netatmo API"
                        elif "SSL" in error_type or "certificate" in error_msg.lower():
                            error_msg = "SSL/TLS error connecting to Netatmo API"
                        
                        logger.warning(f"Netatmo API call failed: {error_type}: {error_msg}")
                        self._update_health(
                            device_id="netatmo_weather",
                            device_type="weather",
                            name="Netatmo Weather Station",
                            connected=False,
                            error=error_msg,
                            details={'error_type': error_type, 'network_error': True}
                        )
                else:
                    self._update_health(
                        device_id="netatmo_weather",
                        device_type="weather",
                        name="Netatmo Weather Station",
                        connected=False,
                        error="Not initialized or no account",
                        details={}
                    )
            finally:
                # Always close service if it was created
                if service:
                    try:
                        await service.close()
                    except Exception:
                        pass  # Ignore errors during cleanup
            
        except Exception as e:
            # Catch all exceptions including network errors
            error_msg = str(e)
            error_type = type(e).__name__
            
            # Provide specific error messages
            if "getaddrinfo failed" in error_msg or "ClientConnectorDNSError" in error_type:
                error_msg = "DNS resolution failed (Python/aiohttp resolver issue - may be IPv6/IPv4 conflict)"
            elif "Cannot connect to host" in error_msg:
                error_msg = f"Cannot connect to api.netatmo.com (firewall/proxy blocking or IPv6 issue)"
            elif "timeout" in error_msg.lower():
                error_msg = "Connection timeout to Netatmo API"
            elif "SSL" in error_type or "certificate" in error_msg.lower():
                error_msg = "SSL/TLS error connecting to Netatmo API"
            
            logger.warning(f"Error checking Netatmo: {error_type}: {error_msg}")
            self._update_health(
                device_id="netatmo_weather",
                device_type="weather",
                name="Netatmo Weather Station",
                connected=False,
                error=error_msg,
                details={'error_type': error_type, 'raw_error': str(e)}
            )
            
    async def _check_ring(self):
        """Check Ring doorbell."""
        try:
            from ..integrations.ring_client import get_ring_client
            
            client = get_ring_client()
            if client and client.is_initialized:
                try:
                    summary = await client.get_summary()
                    doorbell_count = summary.get('doorbell_count', 0)
                    
                    self._update_health(
                        device_id="ring_doorbell",
                        device_type="ring",
                        name="Ring Doorbell",
                        connected=True,
                        error=None,
                        details={
                            'doorbells': doorbell_count,
                            'alarm_capable': summary.get('alarm_capable', False)
                        }
                    )
                except Exception as e:
                    self._update_health(
                        device_id="ring_doorbell",
                        device_type="ring",
                        name="Ring Doorbell",
                        connected=False,
                        error=f"API call failed: {e}",
                        details={}
                    )
            else:
                self._update_health(
                    device_id="ring_doorbell",
                    device_type="ring",
                    name="Ring Doorbell",
                    connected=False,
                    error="Not initialized - run 2FA setup",
                    details={'needs_setup': True}
                )
                
        except Exception:
            logger.exception("Error checking Ring")
            
    def _update_health(self, device_id: str, device_type: str, name: str, 
                      connected: bool, error: Optional[str], details: Dict[str, Any]):
        """Update health status for a device and generate alerts."""
        now = datetime.now()
        
        if device_id in self.device_health:
            health = self.device_health[device_id]
            previous_state = health.connected
            
            health.connected = connected
            health.last_check = now
            
            if connected:
                # Device came back online
                if not previous_state:
                    self.messaging.info(
                        category=self.MessageCategory.DEVICE_CONNECTION,
                        source=device_id,
                        title=f"{name} Reconnected",
                        description=f"{device_type.upper()} device reconnected successfully",
                        device_type=device_type,
                        device_name=name
                    )
                    logger.info(f"Device {name} reconnected")
                
                health.last_success = now
                health.error_count = 0
                health.last_error = None
            else:
                # Device went offline
                if previous_state:
                    # First failure - WARNING
                    self.messaging.warning(
                        category=self.MessageCategory.DEVICE_CONNECTION,
                        source=device_id,
                        title=f"{name} Offline",
                        description=f"{device_type.upper()} device connection lost: {error}",
                        device_type=device_type,
                        device_name=name,
                        error=error
                    )
                    logger.warning(f"Device {name} went offline: {error}")
                
                health.error_count += 1
                health.last_error = error
                
                # Escalate to ALARM after 3 consecutive failures
                if health.error_count == 3:
                    self.messaging.alarm(
                        category=self.MessageCategory.DEVICE_CONNECTION,
                        source=device_id,
                        title=f"{name} CRITICAL",
                        description=f"{device_type.upper()} device offline for 3 checks ({3 * self.poll_interval}s). Check device and network.",
                        device_type=device_type,
                        device_name=name,
                        error_count=3,
                        duration_seconds=3 * self.poll_interval
                    )
                    logger.error(f"Device {name} CRITICAL - offline for {3 * self.poll_interval}s")
                
            health.details = details
        else:
            # New device discovered
            self.device_health[device_id] = DeviceHealth(
                device_id=device_id,
                device_type=device_type,
                name=name,
                connected=connected,
                last_check=now,
                last_success=now if connected else None,
                error_count=0 if connected else 1,
                last_error=None if connected else error,
                details=details
            )
            
            # Generate discovery message
            if connected:
                self.messaging.info(
                    category=self.MessageCategory.DEVICE_STATUS,
                    source=device_id,
                    title=f"{name} Discovered",
                    description=f"New {device_type.upper()} device detected and connected",
                    device_type=device_type,
                    device_name=name
                )
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get overall system health summary."""
        total_devices = len(self.device_health)
        online_devices = sum(1 for h in self.device_health.values() if h.connected)
        offline_devices = total_devices - online_devices
        
        # Group by type
        by_type = {}
        for health in self.device_health.values():
            device_type = health.device_type
            if device_type not in by_type:
                by_type[device_type] = {'online': 0, 'offline': 0}
            
            if health.connected:
                by_type[device_type]['online'] += 1
            else:
                by_type[device_type]['offline'] += 1
        
        return {
            'total_devices': total_devices,
            'online': online_devices,
            'offline': offline_devices,
            'health_percentage': round((online_devices / total_devices * 100) if total_devices > 0 else 0, 1),
            'by_type': by_type,
            'devices': [
                {
                    'device_id': h.device_id,
                    'type': h.device_type,
                    'name': h.name,
                    'connected': h.connected,
                    'last_check': h.last_check.isoformat(),
                    'last_success': h.last_success.isoformat() if h.last_success else None,
                    'error_count': h.error_count,
                    'last_error': h.last_error,
                    'details': h.details
                }
                for h in self.device_health.values()
            ]
        }
    
    def get_offline_devices(self) -> List[DeviceHealth]:
        """Get list of offline devices."""
        return [h for h in self.device_health.values() if not h.connected]
    
    def get_device_status(self) -> List[Dict[str, Any]]:
        """Get device status as list of dicts for API/metrics export."""
        return [
            {
                'device_id': h.device_id,
                'type': h.device_type,
                'name': h.name,
                'connected': h.connected,
                'last_check': int(h.last_check.timestamp()) if h.last_check else 0,
                'last_success': int(h.last_success.timestamp()) if h.last_success else 0,
                'error_count': h.error_count,
                'last_error': h.last_error,
                'details': h.details
            }
            for h in self.device_health.values()
        ]


# Global supervisor instance
_supervisor: Optional[ConnectionSupervisor] = None


def get_supervisor() -> ConnectionSupervisor:
    """Get or create global supervisor instance."""
    global _supervisor
    if _supervisor is None:
        _supervisor = ConnectionSupervisor(poll_interval=60)
    return _supervisor

