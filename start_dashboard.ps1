# Start Tapo Camera MCP Dashboard
# Validates dependencies and fixes Unicode encoding issues on Windows

Write-Host "`n" -NoNewline
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "  Home Security MCP Dashboard - Starting..." -ForegroundColor White
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host ""

# Set UTF-8 encoding for console
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"

# Activate venv
& .\venv\Scripts\Activate.ps1

# Validate dependencies BEFORE starting
Write-Host "🔍 Validating dependencies..." -ForegroundColor Cyan
python validate_dependencies.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "`n❌ DEPENDENCY CHECK FAILED!" -ForegroundColor Red
    Write-Host "   Server cannot start with missing critical dependencies." -ForegroundColor Yellow
    Write-Host "   Install missing packages shown above and try again.`n" -ForegroundColor White
    exit 1
}

Write-Host "`n✅ Dependencies validated!" -ForegroundColor Green
Write-Host ""

# Check for port conflicts
$port = 7777
Write-Host "🔍 Checking port $port availability..." -ForegroundColor Cyan
$portInUse = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue

if ($portInUse) {
    $processId = $portInUse.OwningProcess
    $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
    $processName = if ($process) { $process.ProcessName } else { "Unknown" }
    $processPath = if ($process) { $process.Path } else { "N/A" }
    
    Write-Host "`n❌ PORT CONFLICT DETECTED!" -ForegroundColor Red
    Write-Host "   Port $port is already in use by:" -ForegroundColor Yellow
    Write-Host "   • Process: $processName (PID: $processId)" -ForegroundColor White
    Write-Host "   • Path: $processPath" -ForegroundColor Gray
    Write-Host ""
    Write-Host "💡 Solutions:" -ForegroundColor Cyan
    Write-Host "   1. Stop the conflicting process:" -ForegroundColor White
    Write-Host "      Stop-Process -Id $processId -Force" -ForegroundColor Gray
    Write-Host ""
    Write-Host "   2. Stop Docker container (if using Docker):" -ForegroundColor White
    Write-Host "      docker ps | findstr tapo" -ForegroundColor Gray
    Write-Host "      docker stop <container-id>" -ForegroundColor Gray
    Write-Host ""
    Write-Host "   3. Use a different port:" -ForegroundColor White
    Write-Host "      python -m tapo_camera_mcp.web --host 0.0.0.0 --port 7778" -ForegroundColor Gray
    Write-Host ""
    exit 1
}

Write-Host "✅ Port $port is available!" -ForegroundColor Green
Write-Host ""

# Start dashboard
Write-Host "🚀 Starting dashboard on http://localhost:$port..." -ForegroundColor Yellow
Write-Host "   Connection supervisor will monitor all devices" -ForegroundColor Gray
Write-Host "   Health dashboard: http://localhost:$port/health-dashboard" -ForegroundColor Gray
Write-Host "   Alerts dashboard: http://localhost:$port/alerts`n" -ForegroundColor Gray

python -m tapo_camera_mcp.web --host 0.0.0.0 --port $port

