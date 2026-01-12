@echo off
REM Windows batch file for Tapo LLMs CLI
REM This provides cross-platform executable access

REM Try to find Python in virtual environment first
if exist "%VIRTUAL_ENV%\Scripts\python.exe" (
    "%VIRTUAL_ENV%\Scripts\python.exe" -m tapo_camera_mcp.cli %*
) else if exist "venv\Scripts\python.exe" (
    "venv\Scripts\python.exe" -m tapo_camera_mcp.cli %*
) else if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -m tapo_camera_mcp.cli %*
) else (
    REM Fall back to system Python
    python -m tapo_camera_mcp.cli %*
)