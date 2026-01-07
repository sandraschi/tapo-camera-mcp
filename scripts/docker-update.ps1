#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Quick container update: rebuild and restart

.DESCRIPTION
    Rebuilds containers with cache (fast) and restarts them.
    Perfect for incremental code changes during development.
    
    USAGE AFTER CODE CHANGES:
    - After AI makes code edits, run this script
    - Or tell AI: "rebuild containers" / "update containers" / "fast build"
    - This uses Docker layer caching (only rebuilds changed code, not dependencies)

.EXAMPLE
    .\scripts\docker-update.ps1
    # Fast rebuild and restart (uses cache)
#>

$composeFile = "deploy/myhomecontrol/docker-compose.yml"

if (-not (Test-Path $composeFile)) {
    Write-Host "[X] Docker Compose file not found: $composeFile" -ForegroundColor Red
    exit 1
}

Write-Host "`n[REBUILD] Quick container update (with cache)..." -ForegroundColor Cyan
Write-Host "   [INFO] Reuses cached layers - no unnecessary downloads!`n" -ForegroundColor Gray

# Change to compose file directory
Push-Location (Split-Path $composeFile -Parent)

try {
    $startTime = Get-Date
    
    # Build with cache (fast)
    Write-Host ">>> Building with cache..." -ForegroundColor Cyan
    docker compose -f (Split-Path $composeFile -Leaf) build
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "`n[X] Build failed!" -ForegroundColor Red
        exit $LASTEXITCODE
    }
    
    # Aggressively kill anything hogging port 7777
    Write-Host "`n[KILL] Killing any old containers hogging port 7777..." -ForegroundColor Yellow
    $conflictingContainers = docker ps -q --filter "publish=7777"
    if ($conflictingContainers) {
        Write-Host "   Stopping containers: $conflictingContainers" -ForegroundColor Gray
        docker stop $conflictingContainers
        docker rm -f $conflictingContainers
    }

    # Standard compose down as well
    Write-Host "[STOP] Normalizing environment with compose down..." -ForegroundColor Cyan
    docker compose -f (Split-Path $composeFile -Leaf) down --remove-orphans
    
    # Restart containers
    Write-Host "`n[UP] Starting containers..." -ForegroundColor Cyan
    docker compose -f (Split-Path $composeFile -Leaf) up -d
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "`n[X] Restart failed!" -ForegroundColor Red
        exit $LASTEXITCODE
    }
    
    $duration = (Get-Date) - $startTime
    
    Write-Host ""
    Write-Host "[OK] Update complete in $([math]::Round($duration.TotalSeconds, 1))s!" -ForegroundColor Green
    Write-Host ""
    
}
finally {
    Pop-Location
}
