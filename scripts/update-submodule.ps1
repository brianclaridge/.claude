#!/usr/bin/env pwsh
# Commit and sync .claude submodule changes
param(
    [string]$Message = "chore: update .claude",
    [string]$Branch = "main"
)

$ErrorActionPreference = "Stop"

# Determine submodule path based on execution context
$SubmodulePath = if (Test-Path ".claude") { ".claude" } else { "." }

# Validate it's a git repository
if (-not (Test-Path (Join-Path $SubmodulePath ".git"))) {
    Write-Error "ERROR: $SubmodulePath is not a git repository. Run: git submodule init && git submodule update"
    exit 1
}

# Check if there are changes or we're behind
Write-Host "Checking for changes..."
git -C $SubmodulePath fetch --all -q

$status = git -C $SubmodulePath status
$isBehind = $status -match "Your branch is behind"
$hasChanges = (git -C $SubmodulePath status --porcelain) -ne ""

if (-not $isBehind -and -not $hasChanges) {
    Write-Host "Submodule is already up to date and has no local changes"
    exit 0
}

# Stage all changes
Write-Host "Staging changes..."
git -C $SubmodulePath add --all

# Commit if there are staged changes
$hasStagedChanges = -not (git -C $SubmodulePath diff --cached --quiet; $LASTEXITCODE -eq 0)
if ($hasStagedChanges) {
    Write-Host "Committing: $Message"
    git -C $SubmodulePath commit -m $Message
}

# Push changes
Write-Host "Pushing to origin..."
git -C $SubmodulePath push

# Pull latest
Write-Host "Pulling from origin/$Branch..."
git -C $SubmodulePath pull origin $Branch

Write-Host "Done. Current HEAD:"
git -C $SubmodulePath log -1 --oneline
