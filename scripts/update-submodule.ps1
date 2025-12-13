#!/usr/bin/env pwsh
# Smart submodule update with auto-generated commit messages
# Commits .claude changes, then updates parent submodule reference
param(
    [string]$Message = "",  # Optional override - if empty, auto-generate
    [string]$Branch = "main"
)

$ErrorActionPreference = "Stop"

function Get-ChangeSummary {
    <#
    .SYNOPSIS
    Parse git status and generate commit message
    #>
    param([string]$Path)

    $changes = git -C $Path status --porcelain
    if (-not $changes) { return $null }

    $added = @()
    $modified = @()
    $deleted = @()

    foreach ($line in $changes -split "`n") {
        if (-not $line) { continue }

        $status = $line.Substring(0, 2).Trim()
        $file = $line.Substring(3).Trim()

        # Get the top-level directory or filename
        $parts = $file -split '/'
        $item = if ($parts.Count -gt 1) { $parts[0] } else { $file }

        switch -Regex ($status) {
            '^A|^\?\?' { if ($item -notin $added) { $added += $item } }
            '^M|^R'    { if ($item -notin $modified) { $modified += $item } }
            '^D'       { if ($item -notin $deleted) { $deleted += $item } }
        }
    }

    # Build message parts
    $parts = @()
    if ($added.Count -gt 0) {
        $items = ($added | Select-Object -First 2) -join ", "
        $suffix = if ($added.Count -gt 2) { " (+$($added.Count - 2))" } else { "" }
        $parts += "add $items$suffix"
    }
    if ($modified.Count -gt 0) {
        $items = ($modified | Select-Object -First 2) -join ", "
        $suffix = if ($modified.Count -gt 2) { " (+$($modified.Count - 2))" } else { "" }
        $parts += "update $items$suffix"
    }
    if ($deleted.Count -gt 0) {
        $items = ($deleted | Select-Object -First 2) -join ", "
        $suffix = if ($deleted.Count -gt 2) { " (+$($deleted.Count - 2))" } else { "" }
        $parts += "remove $items$suffix"
    }

    if ($parts.Count -eq 0) { return $null }

    $summary = $parts -join ", "

    # Truncate if too long (keep under 72 chars)
    $prefix = "chore(.claude): "
    $maxLen = 72 - $prefix.Length
    if ($summary.Length -gt $maxLen) {
        $summary = $summary.Substring(0, $maxLen - 3) + "..."
    }

    return "$prefix$summary"
}

function Test-IsSubmodule {
    <#
    .SYNOPSIS
    Check if parent directory uses .claude as a submodule
    #>
    param([string]$SubmodulePath)

    $parentPath = Split-Path -Parent (Resolve-Path $SubmodulePath)
    $gitmodulesPath = Join-Path $parentPath ".gitmodules"

    if (Test-Path $gitmodulesPath) {
        $content = Get-Content $gitmodulesPath -Raw
        return $content -match '\.claude'
    }
    return $false
}

# =============================================================================
# Main Script
# =============================================================================

# Determine submodule path based on execution context
$SubmodulePath = if (Test-Path ".claude") { ".claude" } else { "." }
$IsInSubmodule = $SubmodulePath -eq "."

Write-Host "Checking $SubmodulePath for changes..." -ForegroundColor Cyan

# Validate it's a git repository
if (-not (Test-Path (Join-Path $SubmodulePath ".git"))) {
    Write-Error "ERROR: $SubmodulePath is not a git repository"
    exit 1
}

# Fetch latest
git -C $SubmodulePath fetch --all -q 2>$null

# Check for changes
$hasChanges = (git -C $SubmodulePath status --porcelain) -ne ""
$status = git -C $SubmodulePath status
$isBehind = $status -match "Your branch is behind"

if (-not $hasChanges -and -not $isBehind) {
    Write-Host "No changes detected in $SubmodulePath" -ForegroundColor Green
    exit 0
}

# Show changes
if ($hasChanges) {
    Write-Host "`nChanges detected:" -ForegroundColor Yellow
    git -C $SubmodulePath status --porcelain | ForEach-Object { Write-Host "  $_" }
}

# Determine commit message
$CommitMessage = if ($Message) {
    $Message  # Use provided message
} else {
    Get-ChangeSummary -Path $SubmodulePath  # Auto-generate
}

if (-not $CommitMessage) {
    Write-Host "No changes to commit" -ForegroundColor Green
    exit 0
}

# Stage and commit .claude changes
Write-Host "`nStaging changes..." -ForegroundColor Cyan
git -C $SubmodulePath add --all

$hasStagedChanges = $false
git -C $SubmodulePath diff --cached --quiet 2>$null
if ($LASTEXITCODE -ne 0) { $hasStagedChanges = $true }

if ($hasStagedChanges) {
    Write-Host "Committing: $CommitMessage" -ForegroundColor Green
    git -C $SubmodulePath commit -m $CommitMessage

    Write-Host "Pushing to origin/$Branch..." -ForegroundColor Cyan
    git -C $SubmodulePath push origin $Branch
}

# Pull latest (in case remote has changes)
if ($isBehind) {
    Write-Host "Pulling from origin/$Branch..." -ForegroundColor Cyan
    git -C $SubmodulePath pull origin $Branch
}

Write-Host "`n.claude HEAD:" -ForegroundColor Green
git -C $SubmodulePath log -1 --oneline

# =============================================================================
# Update parent repo's submodule reference (if applicable)
# =============================================================================

$ParentPath = if ($IsInSubmodule) { ".." } else { "." }
$ParentHasSubmodule = Test-IsSubmodule -SubmodulePath $SubmodulePath

if ($ParentHasSubmodule -and -not $IsInSubmodule) {
    Write-Host "`nUpdating parent submodule reference..." -ForegroundColor Cyan

    # Check if submodule reference changed
    $parentChanges = git -C $ParentPath status --porcelain .claude

    if ($parentChanges) {
        git -C $ParentPath add .claude
        git -C $ParentPath commit -m "chore: update .claude submodule"

        Write-Host "Pushing parent to origin..." -ForegroundColor Cyan
        git -C $ParentPath push

        Write-Host "`nParent repo updated." -ForegroundColor Green
    } else {
        Write-Host "Parent submodule reference unchanged." -ForegroundColor Green
    }
}

Write-Host "`nDone." -ForegroundColor Green
