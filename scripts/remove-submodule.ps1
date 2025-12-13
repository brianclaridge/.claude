#!/usr/bin/env pwsh
# Remove .claude submodule from parent repository
# Must be run from parent directory (not from within .claude/)

$ErrorActionPreference = "Stop"

Write-Host "Removing .claude submodule..." -ForegroundColor Cyan

# Validate we're in parent directory (not inside .claude)
if (-not (Test-Path ".gitmodules")) {
    Write-Error "ERROR: .gitmodules not found. Run this from the parent repository."
    exit 1
}

$gitmodulesContent = Get-Content ".gitmodules" -Raw
if ($gitmodulesContent -notmatch '\.claude') {
    Write-Error "ERROR: .claude is not configured as a submodule in this repository."
    exit 1
}

if (-not (Test-Path ".claude")) {
    Write-Error "ERROR: .claude directory not found."
    exit 1
}

# Step 1: Deinitialize submodule
Write-Host "Deinitializing submodule..." -ForegroundColor Yellow
git submodule deinit -f .claude

# Step 2: Remove .git/modules/.claude
Write-Host "Removing .git/modules/.claude..." -ForegroundColor Yellow
$modulesPath = ".git/modules/.claude"
if (Test-Path $modulesPath) {
    Remove-Item -Recurse -Force $modulesPath
}

# Step 3: Remove .claude from git index
Write-Host "Removing .claude from index..." -ForegroundColor Yellow
git rm -f .claude

# Step 4: Commit the removal
Write-Host "Committing removal..." -ForegroundColor Yellow
git commit -m "chore: remove .claude submodule"

Write-Host "`nDone. .claude submodule has been removed." -ForegroundColor Green
