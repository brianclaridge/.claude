#!/usr/bin/env pwsh
<#
.SYNOPSIS
    GCP authentication wrapper.

.DESCRIPTION
    Authenticates to Google Cloud Platform using gcloud auth login.
    Wraps the gcp-login skill's Python library.

.PARAMETER Force
    Force re-login even if already authenticated.

.EXAMPLE
    ./gcp-auth.ps1
    # Authenticate to GCP

.EXAMPLE
    ./gcp-auth.ps1 -Force
    # Force re-authentication
#>

param(
    [switch]$Force
)

$ErrorActionPreference = "Stop"

$skillPath = "${env:CLAUDE_SKILLS_PATH}/gcp-login"

if (-Not (Test-Path -Path $skillPath)) {
    throw "GCP login skill not found: $skillPath"
}

$args = @()

if ($Force) {
    $args += "--force"
}

try {
    Push-Location $skillPath

    if ($args.Count -gt 0) {
        uv run python -m lib @args
    }
    else {
        uv run python -m lib
    }

    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}
finally {
    Pop-Location
}
