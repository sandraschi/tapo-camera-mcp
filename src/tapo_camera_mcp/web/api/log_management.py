"""
Log management API endpoints for manual log operations.
"""

import logging
from typing import TYPE_CHECKING, Any, Dict

from fastapi import APIRouter, BackgroundTasks, HTTPException

from ...mcp_client import call_mcp_tool
from ...utils.log_manager import sanitize_logs_now

if TYPE_CHECKING:
    from ...utils.log_manager import LogManager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/logs", tags=["log-management"])


@router.post("/sanitize", summary="Sanitize log files")
async def sanitize_logs(
    background_tasks: BackgroundTasks, log_files: list[str] = None
) -> Dict[str, Any]:
    """
    Manually trigger log sanitization (rotation, compression, cleanup) via MCP.

    Args:
        log_files: Optional list of specific log files to sanitize.
                  If not provided, all log files will be processed.

    Returns:
        Dict containing the results of sanitization operations.
    """
    try:
        # Note: Log sanitization is currently done via direct calls since
        # system_management tool doesn't have this action yet.
        # TODO: Add sanitize action to system_management tool

        # Run sanitization in background to avoid blocking
        background_tasks.add_task(_sanitize_logs_background, log_files)
        return {
            "message": "Log sanitization started in background",
            "status": "running",
            "note": "Using direct log manager calls - consider adding to system_management MCP tool",
        }
    except Exception as e:
        logger.exception(f"Failed to start log sanitization: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start log sanitization: {e!s}")


@router.get("/stats", summary="Get log statistics")
async def get_logs_stats() -> Dict[str, Any]:
    """
    Get statistics about log files via MCP.

    Returns:
        Dict containing log statistics and configuration info.
    """
    try:
        # Try to get log stats via system management tool
        result = await call_mcp_tool("system_management", {"action": "logs", "lines": 1})
        if result.get("success"):
            # Extract stats from the log data
            log_data = result.get("data", {})
            return {
                "log_files": log_data.get("log_files", []),
                "total_size": log_data.get("total_size", 0),
                "oldest_entry": log_data.get("oldest_entry"),
                "newest_entry": log_data.get("newest_entry"),
                "entry_count": log_data.get("entry_count", 0),
            }
        # Fallback: since system_management might not have stats, return basic info
        return {
            "message": "Log statistics not available via MCP. Use direct log management.",
            "available_via_mcp": False,
        }
    except Exception as e:
        logger.exception(f"Failed to get log stats via MCP: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get log stats: {e!s}")


@router.post("/rotate/{log_file}", summary="Rotate specific log file")
async def rotate_log_file(log_file: str, background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """
    Manually rotate a specific log file via MCP.

    Args:
        log_file: Name of the log file to rotate (without path).

    Returns:
        Dict indicating rotation status.
    """
    try:
        # Note: Log rotation is currently done via direct calls since
        # system_management tool doesn't have this action yet.
        # TODO: Add rotate action to system_management tool

        from ...utils.log_manager import LogManager

        log_manager = LogManager()

        # Run rotation in background
        background_tasks.add_task(_rotate_log_background, log_manager, log_file)
        return {
            "message": f"Log rotation started for {log_file}",
            "status": "running",
            "note": "Using direct log manager calls - consider adding to system_management MCP tool",
        }
    except Exception as e:
        logger.exception(f"Failed to start log rotation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start log rotation: {e!s}")


async def _sanitize_logs_background(log_files: list[str] = None):
    """Background task for log sanitization"""
    try:
        results = sanitize_logs_now(log_files)
        logger.info(f"Background log sanitization completed: {results}")
    except Exception as e:
        logger.exception(f"Background log sanitization failed: {e}")


async def _rotate_log_background(log_manager: "LogManager", log_file: str):
    """Background task for log rotation"""
    try:
        success = log_manager.rotate_log(log_file, force=True)
        if success:
            logger.info(f"Background log rotation completed for {log_file}")
        else:
            logger.warning(f"Background log rotation failed or not needed for {log_file}")
    except Exception as e:
        logger.exception(f"Background log rotation failed for {log_file}: {e}")
