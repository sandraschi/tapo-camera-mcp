"""
Configuration module for Tapo Camera MCP.

This module provides configuration models and utilities for the Tapo Camera MCP server.
"""
import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, TypeVar, Type, Union

from .models import ServerConfig, CameraConfig, WebUISettings, SecuritySettings, LoggingSettings, StorageSettings

T = TypeVar('T')

class ConfigManager:
    """Manages configuration loading and saving."""
    
    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        """Initialize the config manager.
        
        Args:
            config_path: Path to the configuration file. If None, looks for config in default locations.
        """
        self.config_path = self._find_config_file(config_path)
        self._config_cache: Dict[str, Any] = {}
    
    def _find_config_file(self, config_path: Optional[Union[str, Path]] = None) -> Path:
        """Find the configuration file.
        
        Args:
            config_path: Explicit config file path. If None, searches in default locations.
            
        Returns:
            Path to the configuration file.
            
        Raises:
            FileNotFoundError: If no configuration file is found.
        """
        if config_path and Path(config_path).exists():
            return Path(config_path)
            
        # Default config locations
        search_paths = [
            Path("config.yaml"),
            Path("config.yml"),
            Path("~/.config/tapo-camera-mcp/config.yaml").expanduser(),
            Path("/etc/tapo-camera-mcp/config.yaml"),
        ]
        
        for path in search_paths:
            if path.exists():
                return path
                
        # If no config found, create a default one in the current directory
        default_config = Path("config.yaml")
        self.save_default_config(default_config)
        return default_config
    
    def save_default_config(self, path: Union[str, Path]) -> None:
        """Save a default configuration file.
        
        Args:
            path: Path where to save the default configuration.
        """
        default_config = {
            "host": "0.0.0.0",
            "port": 8080,
            "debug": False,
            "web": {
                "enabled": True,
                "host": "0.0.0.0",
                "port": 7777,
                "title": "Tapo Camera MCP",
                "theme": "dark",
                "enable_swagger": True,
                "enable_redoc": False,
                "enable_cors": True,
                "cors_origins": ["*"],
                "session_secret": "change-this-in-production",
                "session_lifetime": 86400
            },
            "security": {
                "secret_key": "change-this-in-production",
                "algorithm": "HS256",
                "access_token_expire_minutes": 1440,
                "password_min_length": 8,
                "password_require_digit": True,
                "password_require_uppercase": True,
                "password_require_special_char": True,
                "rate_limit": "100/minute",
                "enable_rate_limiting": True
            },
            "logging": {
                "level": "INFO",
                "file": "tapo-camera-mcp.log",
                "max_size_mb": 10,
                "backup_count": 5,
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "date_format": "%Y-%m-%d %H:%M:%S"
            },
            "storage": {
                "recordings_dir": "recordings",
                "snapshots_dir": "snapshots",
                "temp_dir": "temp",
                "max_storage_gb": 100,
                "retention_days": 30
            },
            "camera_scan_interval": 300,
            "max_workers": 4,
            "request_timeout": 30,
            "log_level": "INFO"
        }
        
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w') as f:
            yaml.safe_dump(default_config, f, default_flow_style=False, sort_keys=False)
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file.
        
        Returns:
            Dictionary containing the configuration.
            
        Raises:
            ValueError: If the configuration file has an unsupported format.
        """
        if self._config_cache:
            return self._config_cache
            
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        with open(self.config_path, 'r') as f:
            if self.config_path.suffix.lower() in ('.yaml', '.yml'):
                config = yaml.safe_load(f)
            elif self.config_path.suffix.lower() == '.json':
                config = json.load(f)
            else:
                raise ValueError(f"Unsupported config file format: {self.config_path.suffix}")
        
        self._config_cache = config
        return config
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by dot notation key.
        
        Args:
            key: Dot notation key (e.g., 'web.port').
            default: Default value if key is not found.
            
        Returns:
            The configuration value or default if not found.
        """
        config = self.load_config()
        keys = key.split('.')
        value = config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def get_model(self, model_class: Type[T]) -> T:
        """Get a configuration model instance.
        
        Args:
            model_class: The configuration model class.
            
        Returns:
            An instance of the model class populated with configuration values.
        """
        config = self.load_config()
        model_name = model_class.__name__.lower()
        
        if model_name == 'serverconfig':
            # Special handling for ServerConfig since it contains nested models
            return ServerConfig(
                host=config.get('host', '0.0.0.0'),
                port=config.get('port', 8080),
                debug=config.get('debug', False),
                web=WebUISettings(**config.get('web', {})),
                security=SecuritySettings(**config.get('security', {})),
                logging=LoggingSettings(**config.get('logging', {})),
                storage=StorageSettings(**config.get('storage', {})),
                camera_scan_interval=config.get('camera_scan_interval', 300),
                max_workers=config.get('max_workers', 4),
                request_timeout=config.get('request_timeout', 30),
                log_level=config.get('log_level', 'INFO'),
                default_camera=config.get('default_camera'),
                cors_origins=config.get('cors_origins', ['*']),
                data_dir=Path(config.get('data_dir', 'data')),
                cache_dir=Path(config.get('cache_dir', 'cache')),
                api_key=config.get('api_key')
            )
        elif hasattr(model_class, 'parse_obj'):
            # Handle Pydantic models
            model_config = config.get(model_name, {})
            return model_class.parse_obj(model_config)
        else:
            # Handle dataclasses
            model_config = config.get(model_name, {})
            return model_class(**model_config)

# Global configuration instance
config_manager = ConfigManager()

# Shortcut functions
get_config = config_manager.load_config
get_setting = config_manager.get
get_model = config_manager.get_model

# Export models and utilities
__all__ = [
    'ServerConfig',
    'CameraConfig',
    'WebUISettings',
    'SecuritySettings',
    'LoggingSettings',
    'StorageSettings',
    'ConfigManager',
    'config_manager',
    'get_config',
    'get_setting',
    'get_model'
]
