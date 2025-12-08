"""
Hardware Initialization Module

Ensures all hardware (cameras, Hue, Tapo plugs, Netatmo, Ring) is properly
initialized and tested at startup with connection verification.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class HardwareInitializer:
    """Initialize and test all hardware connections at startup."""
    
    def __init__(self):
        self.initialization_results: Dict[str, Dict] = {}
        self._initialized = False
    
    async def initialize_all(self) -> Dict[str, Dict]:
        """
        Initialize all hardware components and test connections.
        
        Returns:
            Dictionary with initialization results for each component
        """
        if self._initialized:
            return self.initialization_results
        
        logger.info("=" * 60)
        logger.info("HARDWARE INITIALIZATION - Starting...")
        logger.info("=" * 60)
        
        # Log environment info for debugging
        import os
        import socket
        logger.info(f"Container environment: {os.getenv('CONTAINER', 'No')}")
        logger.info(f"Hostname: {socket.gethostname()}")
        try:
            host_ip = socket.gethostbyname(socket.gethostname())
            logger.info(f"Container IP: {host_ip}")
        except Exception:
            pass
        
        # Check config file location
        from ..config import get_config
        config = get_config()
        logger.info(f"Config loaded: {len(config)} top-level keys")
        logger.info(f"Cameras configured: {len(config.get('cameras', {}))}")
        logger.info(f"Hue configured: {bool(config.get('lighting', {}).get('philips_hue', {}).get('bridge_ip'))}")
        logger.info(f"Tapo plugs configured: {len(config.get('energy', {}).get('tapo_p115', {}).get('devices', []))}")
        logger.info(f"Netatmo enabled: {config.get('weather', {}).get('integrations', {}).get('netatmo', {}).get('enabled', False)}")
        logger.info(f"Ring enabled: {config.get('ring', {}).get('enabled', False)}")
        
        # Initialize all hardware in parallel for speed
        results = await asyncio.gather(
            self._init_cameras(),
            self._init_hue_bridge(),
            self._init_tapo_plugs(),
            self._init_netatmo(),
            self._init_ring(),
            return_exceptions=True
        )
        
        # Store results
        self.initialization_results = {
            "cameras": results[0] if not isinstance(results[0], Exception) else {"success": False, "error": str(results[0])},
            "hue_bridge": results[1] if not isinstance(results[1], Exception) else {"success": False, "error": str(results[1])},
            "tapo_plugs": results[2] if not isinstance(results[2], Exception) else {"success": False, "error": str(results[2])},
            "netatmo": results[3] if not isinstance(results[3], Exception) else {"success": False, "error": str(results[3])},
            "ring": results[4] if not isinstance(results[4], Exception) else {"success": False, "error": str(results[4])},
        }
        
        # Summary
        successful = sum(1 for r in self.initialization_results.values() if r.get("success", False))
        total = len(self.initialization_results)
        
        logger.info("=" * 60)
        logger.info(f"HARDWARE INITIALIZATION COMPLETE: {successful}/{total} components initialized")
        logger.info("=" * 60)
        
        for component, result in self.initialization_results.items():
            status = "[OK]" if result.get("success") else "[FAIL]"
            logger.info(f"  {status} {component}: {result.get('message', result.get('error', 'Unknown'))}")
        
        self._initialized = True
        return self.initialization_results
    
    async def _init_cameras(self) -> Dict:
        """Initialize and test all cameras."""
        try:
            from ..camera.manager import CameraManager
            from ..core.server import TapoCameraServer
            from ..config import get_config
            
            logger.info("[CAMERA] Initializing cameras...")
            
            server = await TapoCameraServer.get_instance()
            camera_manager = server.camera_manager
            
            config = get_config()
            camera_configs = config.get("cameras", {})
            
            if not camera_configs:
                return {"success": True, "message": "No cameras configured", "count": 0}
            
            connected_count = 0
            failed_cameras = []
            
            # Test each camera connection
            cameras = await camera_manager.list_cameras()
            in_use_cameras = []
            
            for cam in cameras:
                cam_name = cam.get("name")
                status = cam.get("status", {})
                connected = status.get("connected", False) if isinstance(status, dict) else False
                in_use = status.get("in_use_by_another_app", False) if isinstance(status, dict) else False
                
                if in_use:
                    in_use_cameras.append(cam_name)
                    in_use_msg = status.get("in_use_error") or status.get("warning") or "Camera in use by another application"
                    logger.warning(f"  [WARN] Camera '{cam_name}': {in_use_msg}")
                elif connected:
                    connected_count += 1
                    logger.info(f"  [OK] Camera '{cam_name}': Connected")
                else:
                    failed_cameras.append(cam_name)
                    logger.warning(f"  [FAIL] Camera '{cam_name}': Not connected")
            
            # Build result message
            if in_use_cameras:
                message_parts = []
                if connected_count > 0:
                    message_parts.append(f"{connected_count} connected")
                if in_use_cameras:
                    message_parts.append(f"{len(in_use_cameras)} in use by other apps")
                if failed_cameras:
                    message_parts.append(f"{len(failed_cameras)} failed")
                message = f"{connected_count}/{len(cameras)} cameras ready ({', '.join(message_parts)})"
            elif connected_count == len(cameras):
                message = f"All {connected_count} cameras connected"
            else:
                message = f"{connected_count}/{len(cameras)} cameras connected"
            
            return {
                "success": connected_count > 0,
                "message": message,
                "count": connected_count,
                "failed": failed_cameras,
                "in_use": in_use_cameras,
                "cameras": [c.get("name") for c in cameras]
            }
                
        except Exception as e:
            logger.exception("Failed to initialize cameras")
            return {"success": False, "error": str(e)}
    
    async def _init_hue_bridge(self) -> Dict:
        """Initialize and test Hue Bridge connection."""
        try:
            from ..tools.lighting.hue_tools import hue_manager
            from ..config import get_config
            
            logger.info("[LIGHTING] Initializing Philips Hue Bridge...")
            
            config = get_config()
            hue_cfg = config.get("lighting", {}).get("philips_hue", {})
            
            if not hue_cfg.get("bridge_ip"):
                return {"success": False, "message": "Hue Bridge not configured"}
            
            # Initialize Hue manager
            if not hue_manager._initialized:
                success = await hue_manager.initialize()
                if not success:
                    return {
                        "success": False,
                        "error": hue_manager._connection_error or "Initialization failed"
                    }
            
            # Test connection by getting lights
            lights = hue_manager.lights
            groups = hue_manager.groups
            scenes = hue_manager.scenes
            
            logger.info(f"  [OK] Hue Bridge: {len(lights)} lights, {len(groups)} groups, {len(scenes)} scenes")
            
            return {
                "success": True,
                "message": f"Connected - {len(lights)} lights, {len(groups)} groups, {len(scenes)} scenes",
                "lights_count": len(lights),
                "groups_count": len(groups),
                "scenes_count": len(scenes),
                "bridge_ip": hue_manager._bridge_ip
            }
            
        except Exception as e:
            logger.exception("Failed to initialize Hue Bridge")
            return {"success": False, "error": str(e)}
    
    async def _init_tapo_plugs(self) -> Dict:
        """Initialize and test Tapo P115 smart plugs."""
        try:
            from ..tools.energy.tapo_plug_tools import tapo_plug_manager
            from ..config import get_config
            
            logger.info("[ENERGY] Initializing Tapo P115 smart plugs...")
            
            config = get_config()
            energy_cfg = config.get("energy", {}).get("tapo_p115", {})
            plugs_config = energy_cfg.get("devices", [])
            
            if not plugs_config:
                return {"success": True, "message": "No Tapo plugs configured", "count": 0}
            
            # Check if tapo library available
            try:
                import tapo
            except ImportError:
                return {"success": False, "error": "tapo library not installed"}
            
            # Initialize plug manager
            account = energy_cfg.get("account", {})
            if not account.get("email") or not account.get("password"):
                return {"success": False, "error": "Tapo account credentials not configured"}
            
            # Initialize the manager
            if not tapo_plug_manager._initialized:
                await tapo_plug_manager.initialize(account)
            
            # Test each plug connection directly
            connected_count = 0
            failed_plugs = []
            
            for plug_cfg in plugs_config:
                device_id = plug_cfg.get("device_id", "unknown")
                name = plug_cfg.get("name", device_id)
                host = plug_cfg.get("host")
                
                if not host:
                    failed_plugs.append(name)
                    logger.warning(f"  [FAIL] Plug '{name}': No host configured")
                    continue
                
                try:
                    # Test connection directly
                    api_client = tapo.ApiClient(account["email"], account["password"])
                    device = await api_client.p115(host)
                    info = await device.get_device_info()
                    energy = await device.get_energy_usage()
                    
                    connected_count += 1
                    power = energy.current_power if energy and hasattr(energy, 'current_power') else 0
                    logger.info(f"  [OK] Plug '{name}' ({host}): Connected - {power}W")
                except Exception as e:
                    failed_plugs.append(name)
                    error_msg = str(e)
                    logger.warning(f"  [FAIL] Plug '{name}' ({host}): {error_msg}")
            
            if connected_count == len(plugs_config):
                return {
                    "success": True,
                    "message": f"All {connected_count} plugs connected",
                    "count": connected_count
                }
            else:
                return {
                    "success": connected_count > 0,
                    "message": f"{connected_count}/{len(plugs_config)} plugs connected",
                    "count": connected_count,
                    "failed": failed_plugs
                }
                
        except Exception as e:
            logger.exception("Failed to initialize Tapo plugs")
            return {"success": False, "error": str(e)}
    
    async def _init_netatmo(self) -> Dict:
        """Initialize and test Netatmo weather station."""
        try:
            from ..integrations.netatmo_client import NetatmoService
            from ..config import get_config
            
            logger.info("[WEATHER] Initializing Netatmo weather station...")
            
            config = get_config()
            weather_cfg = config.get("weather", {}).get("integrations", {}).get("netatmo", {})
            
            if not weather_cfg.get("enabled"):
                return {"success": True, "message": "Netatmo not enabled in config"}
            
            # Check if pyatmo available
            try:
                import pyatmo
            except ImportError:
                return {"success": False, "error": "pyatmo library not installed"}
            
            service = None
            try:
                service = NetatmoService()
                await service.initialize()
                
                if not service._use_real_api:
                    return {"success": False, "error": "Netatmo initialization failed - using simulated data"}
                
                # Test connection by getting stations
                stations = await service.list_stations()
                station_count = len(stations)
                module_count = sum(len(s.get("modules", [])) for s in stations)
                
                logger.info(f"  [OK] Netatmo: {station_count} stations, {module_count} modules")
                
                return {
                    "success": True,
                    "message": f"Connected - {station_count} stations, {module_count} modules",
                    "stations_count": station_count,
                    "modules_count": module_count
                }
            except Exception as e:
                error_msg = str(e)
                error_type = type(e).__name__
                logger.error(f"  [ERROR] Netatmo initialization failed: {error_type}: {error_msg}")
                # Don't mask DNS errors - let them propagate so they can be fixed
                return {"success": False, "error": f"{error_type}: {error_msg}"}
            finally:
                if service:
                    try:
                        await service.close()
                    except Exception:
                        pass
                        
        except Exception as e:
            logger.exception("Failed to initialize Netatmo")
            return {"success": False, "error": str(e)}
    
    async def _init_ring(self) -> Dict:
        """Initialize and test Ring doorbell."""
        try:
            from ..integrations.ring_client import get_ring_client
            from ..config import get_config
            
            logger.info("[SECURITY] Initializing Ring doorbell...")
            
            config = get_config()
            ring_cfg = config.get("ring", {})
            
            if not ring_cfg.get("enabled"):
                return {"success": True, "message": "Ring not enabled in config"}
            
            # Test Ring connection
            ring_client = get_ring_client()
            if not ring_client:
                return {"success": False, "error": "Ring client not available"}
            
            # Try to get devices
            try:
                devices = await ring_client.get_devices()
                device_count = len(devices) if devices else 0
                
                logger.info(f"  [OK] Ring: {device_count} devices")
                
                return {
                    "success": True,
                    "message": f"Connected - {device_count} devices",
                    "devices_count": device_count
                }
            except Exception as e:
                logger.warning(f"  [FAIL] Ring: {str(e)}")
                return {"success": False, "error": str(e)}
                
        except Exception as e:
            logger.exception("Failed to initialize Ring")
            return {"success": False, "error": str(e)}


# Global instance
_hardware_initializer: Optional[HardwareInitializer] = None


async def initialize_all_hardware() -> Dict[str, Dict]:
    """Initialize all hardware components at startup."""
    global _hardware_initializer
    if _hardware_initializer is None:
        _hardware_initializer = HardwareInitializer()
    return await _hardware_initializer.initialize_all()


def get_initialization_results() -> Dict[str, Dict]:
    """Get hardware initialization results."""
    if _hardware_initializer:
        return _hardware_initializer.initialization_results
    return {}

