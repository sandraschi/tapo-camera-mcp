"""
Tapo Camera MCP API Package

This package contains all the API endpoints and related functionality
for the Tapo Camera MCP server.
"""

from typing import List
from fastapi import APIRouter, FastAPI
from ..config import ServerConfig

# Import all API versions
from .v1 import router as v1_router

__all__ = ["setup_api"]


def setup_api(app: FastAPI, config: ServerConfig) -> None:
    """Set up the API routes and middleware.

    Args:
        app: The FastAPI application instance
        config: The server configuration
    """
    # Include API routers
    app.include_router(v1_router, prefix="/api/v1", tags=["v1"])

    # Add CORS middleware if needed
    if config.cors_origins:
        from fastapi.middleware.cors import CORSMiddleware

        app.add_middleware(
            CORSMiddleware,
            allow_origins=config.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
