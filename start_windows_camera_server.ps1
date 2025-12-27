# Start Windows Camera Server for USB cameras
# This server provides HTTP access to USB cameras for the Docker container

Write-Host "Starting Windows Camera Server..." -ForegroundColor Green

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "Python not found. Please install Python 3.8+." -ForegroundColor Red
    exit 1
}

# Change to script directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

# Start the Windows camera server
Write-Host "Starting camera server on http://localhost:7778..." -ForegroundColor Yellow
python windows_camera_server.py



