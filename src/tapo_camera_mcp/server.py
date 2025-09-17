"""
Tapo Camera MCP Server - Legacy import for backward compatibility.

This module provides backward compatibility by importing from core.server.
"""
from .core.server import TapoCameraServer

# For backward compatibility
TapoCameraMCP = TapoCameraServer
