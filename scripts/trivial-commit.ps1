#!/usr/bin/env pwsh
# Create a trivial commit with optional message
param(
    [string]$Message = "(chore) trivial update"
)

$ErrorActionPreference = "Stop"

# Check for changes
$changes = git status --porcelain
if (-not $changes) {
    Write-Host "No changes to commit"
    exit 0
}

Write-Host "Current status:"
git status

Write-Host "`nStaging all changes..."
git add --all

Write-Host "Committing: $Message"
git commit -m $Message

Write-Host "Pushing to origin..."
git push

Write-Host "`nFinal status:"
git status
