"""Simplified scanner API endpoints for basic camera control."""

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ...mcp_client import call_mcp_tool

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/scanner", tags=["scanner"])


class CameraRequest(BaseModel):
    """Base request model for camera operations."""

    camera_name: str


class ScanRequest(CameraRequest):
    """Request model for scanning documents."""

    filename: Optional[str] = None


@router.get("/info/{camera_name}", response_model=Dict[str, Any])
async def get_scanner_info(camera_name: str) -> Dict[str, Any]:
    """Get basic information about a scanner camera via MCP."""
    try:
        result = await call_mcp_tool(
            "medical_management",
            {"action": "get_device_status", "device_id": camera_name, "device_type": "scanner"},
        )
        if result.get("success"):
            return result.get("data", result)
        raise HTTPException(status_code=404, detail=f"Scanner {camera_name} not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to get scanner info via MCP")
        raise HTTPException(status_code=500, detail=f"Failed to get scanner info: {e!s}")


@router.post("/scan", response_model=Dict[str, Any])
async def scan_document(request: ScanRequest) -> Dict[str, Any]:
    """Scan a document using the camera via MCP."""
    try:
        result = await call_mcp_tool(
            "medical_management",
            {
                "action": "scan_document",
                "device_id": request.camera_name,
                "filename": request.filename,
            },
        )
        if result.get("success"):
            return result.get("data", result)
        raise HTTPException(status_code=500, detail="Failed to scan document")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to scan document via MCP")
        raise HTTPException(status_code=500, detail=f"Failed to scan document: {e!s}")
