"""
Security System Integrations

Provides unified integration with various home security MCP servers
for comprehensive dashboard monitoring and control.
"""

from .integrations import (
    NestProtectClient,
    RingMCPClient,
    SecurityAlert,
    SecurityDevice,
    SecurityIntegrationManager,
    security_manager,
)

__all__ = [
    "SecurityDevice",
    "SecurityAlert",
    "NestProtectClient",
    "RingMCPClient",
    "SecurityIntegrationManager",
    "security_manager",
]
