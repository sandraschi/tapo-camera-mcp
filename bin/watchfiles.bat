@echo off
REM Windows batch file for watchfiles runner
REM This provides cross-platform executable access

REM Try to find Python in virtual environment first
if exist "%VIRTUAL_ENV%\Scripts\python.exe" (
    "%VIRTUAL_ENV%\Scripts\python.exe" "%~dp0..\watchfiles_runner.py" %*
) else if exist "venv\Scripts\python.exe" (
    "venv\Scripts\python.exe" "%~dp0..\watchfiles_runner.py" %*
) else if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" "%~dp0..\watchfiles_runner.py" %*
) else (
    REM Fall back to system Python
    python "%~dp0..\watchfiles_runner.py" %*
)