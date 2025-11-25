#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Automated repository backup using Windows native compression
    
.DESCRIPTION
    Creates a compressed ZIP backup of the repository and saves to:
    1. Desktop\repo backup\
    2. N:\backup\dev\repos\
    
    Excludes:
    - .venv/ (virtual environments)
    - __pycache__/ (Python cache)
    - .ruff_cache/, .mypy_cache/, .pytest_cache/
    - node_modules/ (if any)
    - dist/, build/ (build artifacts)
    - VirtualBox files (*.vdi, *.vmdk, *.vbox)
    - Test artifacts (MagicMock/, sandboxes/, quarantine/)
    - Logs (*.log)
    
.PARAMETER IncludeBuild
    Include dist/ and build/ folders (default: false)
    
.PARAMETER Verbose
    Show detailed progress and timing information
    
.PARAMETER WhatIf
    Preview what would be backed up without creating files
    
.PARAMETER List
    List backup history and statistics
    
.PARAMETER OutputFormat
    Output format: 'text' (default) or 'json' for programmatic use
    
.EXAMPLE
    .\scripts\backup-repo.ps1
    # Creates backup in Desktop\repo backup, N:\backup\dev\repos, and OneDrive
    
.EXAMPLE
    .\scripts\backup-repo.ps1 -IncludeBuild -Verbose
    # Creates backup including build artifacts with detailed progress
    
.EXAMPLE
    .\scripts\backup-repo.ps1 -WhatIf
    # Preview what would be backed up
    
.EXAMPLE
    .\scripts\backup-repo.ps1 -List
    # Show backup history and statistics
    
.EXAMPLE
    .\scripts\backup-repo.ps1 -OutputFormat JSON > backup-result.json
    # Output machine-readable JSON
#>

[CmdletBinding(SupportsShouldProcess)]
param(
    [switch]$IncludeBuild = $false,
    [switch]$List = $false,
    [ValidateSet('text', 'json')]
    [string]$OutputFormat = 'text'
)

# Verbose and WhatIf are available via CmdletBinding/SupportsShouldProcess
$Verbose = $VerbosePreference -eq 'Continue'
$WhatIf = $WhatIfPreference

# Start timing
$scriptStartTime = Get-Date

# Get repo name early (needed for -List and -WhatIf)
if ((Test-Path "pyproject.toml") -or (Test-Path ".git") -or (Test-Path "package.json")) {
    $repoName = (Get-Item .).Name
} else {
    $repoName = "unknown"
}

# Function to show backup history
function Show-BackupHistory {
    param(
        [string]$RepoName,
        [string[]]$BackupDirs
    )
    
    Write-Host "`n╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║        📊 Backup History: $RepoName 📊         ║" -ForegroundColor Cyan
    Write-Host "╚═══════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan
    
    foreach ($backupDir in $BackupDirs) {
        if (-not (Test-Path $backupDir)) {
            Write-Host "⚠️  Location: $backupDir (not found)`n" -ForegroundColor Yellow
            continue
        }
        
        $backups = Get-ChildItem -Path $backupDir -Filter "*.zip" -File | Sort-Object LastWriteTime -Descending
        $locationName = Split-Path $backupDir -Leaf
        $parentDir = Split-Path $backupDir -Parent | Split-Path -Leaf
        
        Write-Host "📍 $parentDir\$locationName" -ForegroundColor White
        Write-Host "   Total backups: $($backups.Count)" -ForegroundColor Gray
        
        if ($backups.Count -gt 0) {
            $oldest = $backups[-1]
            $newest = $backups[0]
            $totalSize = ($backups | Measure-Object -Property Length -Sum).Sum / 1MB
            
            Write-Host "   Oldest:       $($oldest.LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss'))" -ForegroundColor Gray
            Write-Host "   Newest:       $($newest.LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss'))" -ForegroundColor Gray
            Write-Host "   Total size:   $([math]::Round($totalSize, 2)) MB" -ForegroundColor Cyan
            Write-Host "   Avg size:     $([math]::Round($totalSize / $backups.Count, 2)) MB" -ForegroundColor Gray
        } else {
            Write-Host "   (no backups yet)" -ForegroundColor DarkGray
        }
        Write-Host ""
    }
    
    exit 0
}

# Handle -List flag
if ($List) {
    if ($repoName -eq "unknown") {
        Write-Host "❌ Error: Must run from repository root (need pyproject.toml, .git, or package.json)" -ForegroundColor Red
        exit 1
    }
    $desktopBackup = Join-Path (Join-Path ([Environment]::GetFolderPath("Desktop")) "repo backup") $repoName
    $nDriveBackup = Join-Path "N:\backup\dev\repos2" $repoName
    $oneDriveBackup = Join-Path (Join-Path $env:OneDrive "repo-backups") $repoName
    
    Show-BackupHistory -RepoName $repoName -BackupDirs @($desktopBackup, $nDriveBackup, $oneDriveBackup)
}

Write-Host "`n╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Magenta
Write-Host "║       📦 Repository Backup (Windows Native ZIP) 📦      ║" -ForegroundColor Magenta
Write-Host "╚═══════════════════════════════════════════════════════════╝`n" -ForegroundColor Magenta

# Check if we're in a repo (unless -List already handled it)
if ($repoName -eq "unknown") {
    Write-Host "❌ Error: Must run from repository root (need pyproject.toml, .git, or package.json)" -ForegroundColor Red
    exit 1
}

# Get timestamp
$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$backupName = "${repoName}_backup_${timestamp}.zip"

# Define backup destinations with subdirectories per repo
$desktopBackup = Join-Path (Join-Path ([Environment]::GetFolderPath("Desktop")) "repo backup") $repoName
$nDriveBackup = Join-Path "N:\backup\dev\repos2" $repoName
$oneDriveRoot = Join-Path $env:OneDrive "repo-backups"
$oneDriveBackup = Join-Path $oneDriveRoot $repoName

# Ensure backup directories exist
if (-not (Test-Path $desktopBackup)) {
    New-Item -ItemType Directory -Path $desktopBackup -Force | Out-Null
    Write-Host "✅ Created: $desktopBackup" -ForegroundColor Green
}

if (-not (Test-Path $nDriveBackup)) {
    New-Item -ItemType Directory -Path $nDriveBackup -Force | Out-Null
    Write-Host "✅ Created: $nDriveBackup" -ForegroundColor Green
}

if (-not (Test-Path $oneDriveBackup)) {
    New-Item -ItemType Directory -Path $oneDriveBackup -Force | Out-Null
    Write-Host "✅ Created: $oneDriveBackup" -ForegroundColor Green
}

$backupPath1 = Join-Path $desktopBackup $backupName
$backupPath2 = Join-Path $nDriveBackup $backupName
$backupPath3 = Join-Path $oneDriveBackup $backupName

Write-Host "📋 Backup Configuration:" -ForegroundColor Cyan
Write-Host "  Repository:    $repoName" -ForegroundColor White
Write-Host "  Timestamp:     $timestamp" -ForegroundColor White
Write-Host "  Destination 1: $backupPath1" -ForegroundColor White
Write-Host "  Destination 2: $backupPath2" -ForegroundColor White
Write-Host "  Destination 3: $backupPath3" -ForegroundColor Cyan
Write-Host "  Include build: $(if($IncludeBuild){'Yes'}else{'No'})" -ForegroundColor White
Write-Host "  Method:        .NET ZIP API (folder structure preserved)" -ForegroundColor Green
Write-Host ""

# Define exclusions
$exclusions = @(
    ".venv",
    "venv",
    "env",
    ".env",
    "__pycache__",
    ".mypy_cache",
    ".ruff_cache",
    ".pytest_cache",
    "htmlcov",
    "node_modules",
    # ".git",  # INCLUDE .git - contains unpushed commits, local branches, history
    "*.pyc",
    "*.pyo",
    "*.pyd",
    ".DS_Store",
    "Thumbs.db",
    ".windsurf",
    ".cursor",
    "*.log",
    ".vbox",
    "*.vdi",
    "*.vmdk",
    "*.vhd",
    "*.vbox",
    "*.vbox-prev",
    "MagicMock",
    "sandboxes",
    "quarantine",
    "analysis",
    "backups",
    "*.dxt",        # Old DXT package format
    "deploy/gitlab/data",  # GitLab data (locked by container)
    "deploy/gitlab/logs",  # GitLab logs
    "deploy/gitlab/config/*.json",  # GitLab dynamic config
    "deploy/gitlab/config/*.key",   # GitLab keys
    "deploy/gitlab/config/*.pub",   # GitLab public keys
    "deploy/gitlab/config/initial_root_password"  # GitLab password
)

# Large test files that should be excluded (can be regenerated)
# Note: Use forward slashes or double backslashes for regex compatibility
$excludeLargeTestFiles = @(
    "samples/metadata.db",      # Large Calibre test database (3.9 MB)
    "samples/test_library.db",  # Large test libraries  
    "test_data/*.db"            # Test data in any test_data directory
)

# Combine exclusions
$exclusions += $excludeLargeTestFiles

if (-not $IncludeBuild) {
    $exclusions += @("dist", "build", "*.whl", "*.tar.gz")
}

Write-Host "🚫 Excluding:" -ForegroundColor Yellow
foreach ($excl in $exclusions) {
    Write-Host "  - $excl" -ForegroundColor Gray
}
Write-Host ""

# Calculate sizes
Write-Host "📊 Analyzing repository size..." -ForegroundColor Cyan

$allFiles = Get-ChildItem -Recurse -File -ErrorAction SilentlyContinue
$totalSize = ($allFiles | Measure-Object -Property Length -Sum).Sum / 1MB

# Filter files to backup
$repoRoot = (Get-Item .).FullName
$backupFiles = $allFiles | Where-Object {
    $file = $_
    $shouldExclude = $false
    
    # Skip symlinks/ReparsePoints (cause access denied errors)
    if ($file.Attributes -band [System.IO.FileAttributes]::ReparsePoint) {
        return $false
    }
    
    # Get relative path from repo root for matching
    $relativePath = $file.FullName.Substring($repoRoot.Length + 1) -replace '\\', '/'
    
    foreach ($excl in $exclusions) {
        # Convert exclusion pattern to regex
        $exclNormalized = $excl -replace '\\', '/'
        $pattern = $exclNormalized -replace '\*', '.*' -replace '\.', '\.'
        
        # Check if relative path matches exclusion pattern
        if ($relativePath -match "^$pattern" -or $relativePath -match "/$pattern" -or $relativePath -eq $exclNormalized) {
            $shouldExclude = $true
            break
        }
    }
    
    -not $shouldExclude
}

$backupSize = ($backupFiles | Measure-Object -Property Length -Sum).Sum / 1MB
$excludedSize = $totalSize - $backupSize

Write-Host "  Total size:    $([math]::Round($totalSize, 2)) MB" -ForegroundColor White
Write-Host "  Excluded:      $([math]::Round($excludedSize, 2)) MB" -ForegroundColor Red
Write-Host "  Backup size:   $([math]::Round($backupSize, 2)) MB" -ForegroundColor Green
Write-Host "  Reduction:     $([math]::Round(($excludedSize / $totalSize) * 100, 1))%`n" -ForegroundColor Cyan

# Exit early if WhatIf (after file analysis)
if ($WhatIf) {
    Write-Host "`n⚠️  DRY-RUN MODE: No files will be created`n" -ForegroundColor Yellow
    Write-Host "📋 Files that would be backed up: $($backupFiles.Count) files ($([math]::Round($backupSize, 2)) MB)" -ForegroundColor Cyan
    Write-Host "📦 Backup locations:" -ForegroundColor Cyan
    Write-Host "  1. Desktop:     $desktopBackup" -ForegroundColor White
    Write-Host "  2. N: drive:    $nDriveBackup" -ForegroundColor White
    Write-Host "  3. OneDrive:    $oneDriveBackup" -ForegroundColor White
    Write-Host "`n✅ Dry-run complete - no files created`n" -ForegroundColor Green
    exit 0
}

# Function to get file hash for comparison with progress
function Get-FileHashSHA256 {
    param(
        [string]$FilePath,
        [switch]$ShowProgress
    )
    $hash = [System.Security.Cryptography.SHA256]::Create()
    $fileStream = [System.IO.File]::OpenRead($FilePath)
    
    if ($ShowProgress) {
        $fileName = Split-Path $FilePath -Leaf
        Write-Host "  🔐 Computing hash: $fileName..." -NoNewline -ForegroundColor DarkGray
    }
    
    $hashBytes = $hash.ComputeHash($fileStream)
    $fileStream.Close()
    $hash.Dispose()
    
    if ($ShowProgress) {
        Write-Host " ✓" -ForegroundColor Green
    }
    
    return [System.BitConverter]::ToString($hashBytes) -replace '-', ''
}

# Function to show progress bar
function Write-ProgressBar {
    param(
        [int]$Current,
        [int]$Total,
        [string]$Activity
    )
    if ($Total -eq 0) { return }
    $percent = [math]::Min(100, [math]::Round(($Current / $Total) * 100))
    $filled = [math]::Floor($percent / 2)
    $empty = 50 - $filled
    $bar = "█" * $filled + "░" * $empty
    Write-Host "`r[$bar] $percent% ($Current/$Total) - $Activity" -NoNewline
}

# Function to check if backup is duplicate of previous
function Test-BackupDuplicate {
    param(
        [string]$NewBackupPath,
        [string]$BackupDir,
        [switch]$Verbose
    )
    
    if (-not (Test-Path $NewBackupPath)) {
        return $false
    }
    
    # Get all previous backups, sorted by creation time (newest first)
    $previousBackups = Get-ChildItem -Path $BackupDir -Filter "*.zip" -File | 
        Where-Object { $_.FullName -ne $NewBackupPath } | 
        Sort-Object LastWriteTime -Descending
    
    if ($previousBackups.Count -eq 0) {
        if ($Verbose) {
            Write-Host "  ℹ️  No previous backup found for comparison" -ForegroundColor DarkGray
        }
        return $false
    }
    
    # Compare with most recent backup
    $previousBackup = $previousBackups[0]
    if ($Verbose) {
        Write-Host "  🔍 Comparing with previous backup: $(Split-Path $previousBackup.Name -Leaf)" -ForegroundColor DarkGray
    }
    
    $newHash = Get-FileHashSHA256 -FilePath $NewBackupPath -ShowProgress:$Verbose
    $previousHash = Get-FileHashSHA256 -FilePath $previousBackup.FullName -ShowProgress:$Verbose
    
    $isDuplicate = ($newHash -eq $previousHash)
    if ($Verbose -and $isDuplicate) {
        Write-Host "  ✓ Hashes match - duplicate detected" -ForegroundColor Yellow
    } elseif ($Verbose) {
        Write-Host "  ✓ Hashes differ - backup is new" -ForegroundColor Green
    }
    
    return $isDuplicate
}


# Create backup
Write-Host "🔄 Creating backups..." -ForegroundColor Cyan

$backupStartTime = Get-Date

# Initialize summary variables
$created = @()
$skipped = @()

# Helper function to create ZIP with progress
function New-BackupZip {
    param(
        [string]$ZipPath,
        [array]$Files,
        [string]$LocationName,
        [switch]$Verbose,
        [string]$RepoRoot
    )
    
    $zipStart = Get-Date
    $zip = [System.IO.Compression.ZipFile]::Open($ZipPath, [System.IO.Compression.ZipArchiveMode]::Create)
    $fileCount = 0
    
    foreach ($file in $Files) {
        # Calculate relative path from repo root
        $relativePath = $file.FullName.Substring($RepoRoot.Length + 1)
        # Normalize to forward slashes for ZIP standard (preserves folder structure)
        $zipEntryPath = $relativePath -replace '\\', '/'
        # Create entry with full relative path - this preserves folder structure
        [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile($zip, $file.FullName, $zipEntryPath, [System.IO.Compression.CompressionLevel]::Optimal) | Out-Null
        $fileCount++
        
        if ($Verbose -and ($fileCount % 100 -eq 0)) {
            Write-ProgressBar -Current $fileCount -Total $Files.Count -Activity "Adding files to $LocationName"
        }
    }
    
    $zip.Dispose()
    
    if ($Verbose) {
        Write-Host "`r" -NoNewline  # Clear progress bar
        $zipDuration = (Get-Date) - $zipStart
        Write-Host "  ⏱️  ZIP created in $([math]::Round($zipDuration.TotalSeconds, 1))s" -ForegroundColor DarkGray
    }
}

try {
    # CRITICAL FIX: Use .NET ZIP to preserve folder structure
    # Compress-Archive flattens structure when given file list
    
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    Add-Type -AssemblyName System.Security.Cryptography
    
    $repoRoot = (Get-Item .).FullName
    
    # Create backup 1 (Desktop)
    Write-Host "  → Desktop\repo backup..." -ForegroundColor Gray
    if (Test-Path $backupPath1) {
        Remove-Item $backupPath1 -Force
    }
    
    New-BackupZip -ZipPath $backupPath1 -Files $backupFiles -LocationName "Desktop" -Verbose:$Verbose -RepoRoot $repoRoot
    
    # Check if duplicate of previous backup
    if (Test-BackupDuplicate -NewBackupPath $backupPath1 -BackupDir $desktopBackup -Verbose:$Verbose) {
        Write-Host "  ⏭️  Desktop backup identical to previous - removing duplicate" -ForegroundColor Yellow
        Remove-Item $backupPath1 -Force
        $backupPath1 = $null  # Mark as skipped
    } else {
        Write-Host "  ✅ Desktop backup complete (folder structure preserved)" -ForegroundColor Green
    }
    
    # Create backup 2 (N: drive)
    Write-Host "  → N:\backup\dev\repos2..." -ForegroundColor Gray
    if (Test-Path $backupPath2) {
        Remove-Item $backupPath2 -Force
    }
    
    New-BackupZip -ZipPath $backupPath2 -Files $backupFiles -LocationName "N: drive" -Verbose:$Verbose -RepoRoot $repoRoot
    
    # Check if duplicate of previous backup
    if (Test-BackupDuplicate -NewBackupPath $backupPath2 -BackupDir $nDriveBackup -Verbose:$Verbose) {
        Write-Host "  ⏭️  N: drive backup identical to previous - removing duplicate" -ForegroundColor Yellow
        Remove-Item $backupPath2 -Force
        $backupPath2 = $null  # Mark as skipped
    } else {
        Write-Host "  ✅ N: drive backup complete (folder structure preserved)" -ForegroundColor Green
    }
    
    # Create backup 3 (OneDrive)
    Write-Host "  → OneDrive\repo-backups..." -ForegroundColor Gray
    if (Test-Path $backupPath3) {
        Remove-Item $backupPath3 -Force
    }
    
    New-BackupZip -ZipPath $backupPath3 -Files $backupFiles -LocationName "OneDrive" -Verbose:$Verbose -RepoRoot $repoRoot
    
    # Check if duplicate of previous backup
    if (Test-BackupDuplicate -NewBackupPath $backupPath3 -BackupDir $oneDriveBackup -Verbose:$Verbose) {
        Write-Host "  ⏭️  OneDrive backup identical to previous - removing duplicate" -ForegroundColor Yellow
        Remove-Item $backupPath3 -Force
        $backupPath3 = $null  # Mark as skipped
    } else {
        Write-Host "  ✅ OneDrive backup complete (folder structure preserved)" -ForegroundColor Green
    }
    
    $backupDuration = (Get-Date) - $backupStartTime
    if ($Verbose) {
        Write-Host "`n⏱️  Total backup time: $([math]::Round($backupDuration.TotalSeconds, 1))s" -ForegroundColor DarkGray
    }
    
    # Summary (update global variables)
    if ($backupPath1 -and (Test-Path $backupPath1)) { $created += "Desktop" } elseif ($backupPath1 -eq $null) { $skipped += "Desktop" }
    if ($backupPath2 -and (Test-Path $backupPath2)) { $created += "N: drive" } elseif ($backupPath2 -eq $null) { $skipped += "N: drive" }
    if ($backupPath3 -and (Test-Path $backupPath3)) { $created += "OneDrive" } elseif ($backupPath3 -eq $null) { $skipped += "OneDrive" }
    
    if ($created.Count -gt 0) {
        Write-Host "`n✅ Backups created: $($created -join ', ')" -ForegroundColor Green
    }
    if ($skipped.Count -gt 0) {
        Write-Host "⏭️  Backups skipped (unchanged): $($skipped -join ', ')`n" -ForegroundColor Yellow
    }
    
    if ($created.Count -eq 0) {
        Write-Host "`n📌 No new backups created - repository unchanged since last backup`n" -ForegroundColor Cyan
    } else {
        Write-Host "✅ Backup process complete with folder structure preserved!`n" -ForegroundColor Green
    }
    
} catch {
    Write-Host "❌ Error creating backup: $_" -ForegroundColor Red
    exit 1
}

# Get final backup file info
$backupsCreated = 0
if ($backupPath1 -and (Test-Path $backupPath1)) { $backupsCreated++ }
if ($backupPath2 -and (Test-Path $backupPath2)) { $backupsCreated++ }
if ($backupPath3 -and (Test-Path $backupPath3)) { $backupsCreated++ }

if ($backupsCreated -gt 0) {
    # Use first available backup for statistics
    $statsBackup = $null
    if ($backupPath1 -and (Test-Path $backupPath1)) { $statsBackup = $backupPath1 }
    elseif ($backupPath2 -and (Test-Path $backupPath2)) { $statsBackup = $backupPath2 }
    elseif ($backupPath3 -and (Test-Path $backupPath3)) { $statsBackup = $backupPath3 }
    
    if ($statsBackup) {
        $finalSize = (Get-Item $statsBackup).Length / 1MB
        $compressionRatio = ($finalSize / $backupSize) * 100
        
        Write-Host ""
        Write-Host "╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Green
        Write-Host "║              📦 Backup Complete! 📦                     ║" -ForegroundColor Green
        Write-Host "╚═══════════════════════════════════════════════════════════╝" -ForegroundColor Green
        Write-Host ""
        Write-Host "📊 Backup Statistics:" -ForegroundColor Cyan
        Write-Host "  Created:        $backupsCreated of 3 locations" -ForegroundColor White
        Write-Host "  File:           $backupName" -ForegroundColor White
        Write-Host "  Location 1:     $desktopBackup $(if($backupPath1 -and (Test-Path $backupPath1)){'✅'}else{'⏭️ skipped'})" -ForegroundColor White
        Write-Host "  Location 2:     $nDriveBackup $(if($backupPath2 -and (Test-Path $backupPath2)){'✅'}else{'⏭️ skipped'})" -ForegroundColor White
        Write-Host "  Location 3:     $oneDriveBackup $(if($backupPath3 -and (Test-Path $backupPath3)){'✅'}else{'⏭️ skipped'})" -ForegroundColor Cyan
        Write-Host "  Size:           $([math]::Round($finalSize, 2)) MB" -ForegroundColor Cyan
        Write-Host "  Original:       $([math]::Round($backupSize, 2)) MB" -ForegroundColor Gray
        Write-Host "  Compression:    $([math]::Round($compressionRatio, 1))%" -ForegroundColor Green
        Write-Host "  Space saved:    $([math]::Round($totalSize - $finalSize, 2)) MB" -ForegroundColor Green
        Write-Host "  Method:         .NET ZIP API (folder structure preserved)" -ForegroundColor Green
        Write-Host "  Duplicate check: Enabled (skips unchanged backups)" -ForegroundColor Cyan
        Write-Host ""
        
        # Restore instructions
        $restorePath = $statsBackup
        Write-Host "💡 To restore:" -ForegroundColor Cyan
        Write-Host "  Expand-Archive -Path `"$restorePath`" -DestinationPath `"destination-folder`"" -ForegroundColor Gray
        Write-Host ""
    }
    
} else {
    Write-Host "`n✅ All backups skipped - repository unchanged since last backup`n" -ForegroundColor Cyan
}

$scriptDuration = (Get-Date) - $scriptStartTime

# Export metrics
$metricsDir = Join-Path $env:APPDATA "backup-metrics"
if (-not (Test-Path $metricsDir)) {
    New-Item -ItemType Directory -Path $metricsDir -Force | Out-Null
}

$metricsFile = Join-Path $metricsDir "backup-$repoName.jsonl"
$metrics = @{
    timestamp = (Get-Date).ToUniversalTime().ToString("o")
    repo = $repoName
    status = if ($backupsCreated -gt 0) { "success" } elseif ($skipped.Count -eq 3) { "skipped" } else { "partial" }
    locations_created = $created.Count
    locations_skipped = $skipped.Count
    size_mb = if ($statsBackup) { [math]::Round($finalSize, 2) } else { $null }
    duration_seconds = [math]::Round($scriptDuration.TotalSeconds, 2)
    file_count = $backupFiles.Count
    duplicate_detected = ($skipped.Count -gt 0)
} | ConvertTo-Json -Compress

Add-Content -Path $metricsFile -Value $metrics
if ($Verbose) {
    Write-Host "📊 Metrics exported to: $metricsFile" -ForegroundColor DarkGray
}

# JSON output format
if ($OutputFormat -eq "json") {
    $jsonOutput = @{
        repo = $repoName
        timestamp = $timestamp
        status = if ($backupsCreated -gt 0) { "success" } elseif ($skipped.Count -eq 3) { "skipped" } else { "partial" }
        created = @($created)
        skipped = @($skipped)
        size_mb = if ($statsBackup) { [math]::Round($finalSize, 2) } else { $null }
        duration_seconds = [math]::Round($scriptDuration.TotalSeconds, 2)
        file_count = $backupFiles.Count
        locations = @(
            @{ name = "Desktop"; path = $desktopBackup; created = ($backupPath1 -and (Test-Path $backupPath1)) }
            @{ name = "N: drive"; path = $nDriveBackup; created = ($backupPath2 -and (Test-Path $backupPath2)) }
            @{ name = "OneDrive"; path = $oneDriveBackup; created = ($backupPath3 -and (Test-Path $backupPath3)) }
        )
    } | ConvertTo-Json -Depth 3
    
    Write-Host $jsonOutput
    exit 0
}

Write-Host "✅ Done!`n" -ForegroundColor Green
