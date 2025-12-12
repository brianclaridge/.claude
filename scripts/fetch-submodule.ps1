#!/usr/bin/env pwsh
# Fetch and reset .claude submodule to origin/main

$ErrorActionPreference = "Stop"

# Determine submodule path based on execution context
$SubmodulePath = if (Test-Path ".claude") { ".claude" } else { "." }

# Validate it's a git repository
if (-not (Test-Path (Join-Path $SubmodulePath ".git"))) {
    Write-Error "ERROR: $SubmodulePath is not a git repository. Run: git submodule init && git submodule update"
    exit 1
}

# Validate remote exists
$remotes = git -C $SubmodulePath remote
if ($remotes -notcontains "origin") {
    Write-Error "ERROR: No 'origin' remote configured in $SubmodulePath"
    exit 1
}

# Fetch and reset
Write-Host "Fetching from origin..."
git -C $SubmodulePath fetch origin

Write-Host "Resetting to origin/main..."
git -C $SubmodulePath reset --hard origin/main

Write-Host "Cleaning untracked files..."
git -C $SubmodulePath clean -fd

Write-Host "Done. Current HEAD:"
git -C $SubmodulePath log -1 --oneline
