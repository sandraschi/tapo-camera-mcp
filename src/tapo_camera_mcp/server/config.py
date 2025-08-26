"""Server configuration module."""
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List

@dataclass
class ServerConfig:
    """Server configuration class."""
    # Network settings
    host: str = "0.0.0.0"
    port: int = 8080
    
    # Camera settings
    default_camera: Optional[Dict[str, Any]] = None
    
    # Web interface settings
    web_enabled: bool = True
    web_host: str = "0.0.0.0"
    web_port: int = 7777
    
    # Performance settings
    request_timeout: int = 30
    max_retries: int = 3
    
    # Camera groups
    groups: Dict[str, List[str]] = field(default_factory=dict)
    
    # Additional configuration
    extra: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'ServerConfig':
        """Create config from dictionary."""
        return cls(**config_dict)
