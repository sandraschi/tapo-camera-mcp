"""
Configuration module for Tapo Camera MCP.

This module provides configuration models and utilities for the Tapo Camera MCP server.
"""
import os
import sys
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
        """
        if config_path and Path(config_path).exists():
            return Path(config_path)
            
        # Get the module directory to find the repo root config
        module_dir = Path(__file__).parent.parent.parent.parent  # Go up to repo root
        repo_config = module_dir / "config.yaml"
        
        # User-writable config directory
        user_config_dir = Path("~/.config/tapo-camera-mcp").expanduser()
        user_config_file = user_config_dir / "config.yaml"
        
        # Search paths in order of preference
        search_paths = [
            user_config_file,  # User config directory (highest priority)
            repo_config,       # Repo root config file
            Path("config.yaml"),  # Current directory
            Path("config.yml"),
            Path("/etc/tapo-camera-mcp/config.yaml"),  # System config (Linux)
        ]
        
        for path in search_paths:
            if path.exists():
                return path
                
        # If no config found, try to create one from the repo template
        if repo_config.exists():
            # Copy repo config to user directory
            user_config_dir.mkdir(parents=True, exist_ok=True)
            try:
                import shutil
                shutil.copy2(repo_config, user_config_file)
                return user_config_file
            except Exception:
                # If copying fails, just use the repo config
                return repo_config
        
        # Last resort: create a minimal default config in user directory
        user_config_dir.mkdir(parents=True, exist_ok=True)
        self.save_default_config(user_config_file)
        return user_config_file
    
    def save_default_config(self, path: Union[str, Path]) -> None:
        """Save a default configuration file.
        
        Args:
            path: Path where to save the default configuration.
        """
        # Get user-writable directories
        user_data_dir = Path("~/.local/share/tapo-camera-mcp").expanduser()
        user_data_dir.mkdir(parents=True, exist_ok=True)
        
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
                "file": str(user_data_dir / "tapo-camera-mcp.log"),
                "max_size_mb": 10,
                "backup_count": 5,
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "date_format": "%Y-%m-%d %H:%M:%S"
            },
            "storage": {
                "recordings_dir": str(user_data_dir / "recordings"),
                "snapshots_dir": str(user_data_dir / "snapshots"),
                "temp_dir": str(user_data_dir / "temp"),
                "max_storage_gb": 100,
                "retention_days": 30
            },
            "camera_scan_interval": 300,
            "max_workers": 4,
            "request_timeout": 30,
            "log_level": "INFO",
            "cameras": []  # Empty cameras list for initial setup
        }
        
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(path, 'w') as f:
                yaml.safe_dump(default_config, f, default_flow_style=False, sort_keys=False)
        except PermissionError:
            # If we can't write to the specified path, create a warning but don't crash
            print(f"Warning: Cannot write config to {path}. Using read-only mode.", file=sys.stderr)
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file.
        
        Returns:
            Dictionary containing the configuration.
        """
        if self._config_cache:
            return self._config_cache
            
        if not self.config_path.exists():
            # Create a minimal in-memory config
            return {
                "host": "0.0.0.0",
                "port": 8080,
                "debug": False,
                "cameras": [],
                "log_level": "INFO"
            }
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                if self.config_path.suffix.lower() in ('.yaml', '.yml'):
                    config = yaml.safe_load(f)
                elif self.config_path.suffix.lower() == '.json':
                    config = json.load(f)
                else:
                    raise ValueError(f"Unsupported config file format: {self.config_path.suffix}")
            
            # Ensure config is a dictionary
            if not isinstance(config, dict):
                config = {}
                
            self._config_cache = config
            return config
            
        except Exception as e:
            print(f"Warning: Error loading config from {self.config_path}: {e}", file=sys.stderr)
            # Return minimal config on error
            return {
                "host": "0.0.0.0",
                "port": 8080,
                "debug": False,
                "cameras": [],
                "log_level": "INFO"
            }
    
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
            web_config = config.get('web', {})
            security_config = config.get('security', {})
            security_integrations = config.get('security_integrations', {})

            # Merge security_integrations into security_config
            if security_config and security_integrations:
                security_config = dict(security_config)
                security_config['integrations'] = security_integrations
            elif security_integrations:
                security_config = {'integrations': security_integrations}

            logging_config = config.get('logging', {})
            storage_config = config.get('storage', {})

            return ServerConfig(
                host=config.get('host', '0.0.0.0'),
                port=config.get('port', 8080),
                debug=config.get('debug', False),
                web=WebUISettings(**web_config) if web_config else WebUISettings(),
                security=SecuritySettings(**security_config) if security_config else SecuritySettings(),
                logging=LoggingSettings(**logging_config) if logging_config else LoggingSettings(),
                storage=StorageSettings(**storage_config) if storage_config else StorageSettings(),
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
        elif hasattr(model_class, 'model_validate'):
            # Handle Pydantic v2 models
            model_config = config.get(model_name, {})
            return model_class.model_validate(model_config)
        elif hasattr(model_class, 'parse_obj'):
            # Handle Pydantic v1 models
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
