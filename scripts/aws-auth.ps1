#!/usr/bin/env pwsh
<#
.SYNOPSIS
    AWS SSO authentication wrapper.

.DESCRIPTION
    Authenticates to AWS using SSO. Wraps the aws-login skill's Python library.

    On first run (no .aws.yml config), performs setup:
    - Uses AWS_SSO_START_URL, AWS_ROOT_ACCOUNT_ID, AWS_ROOT_ACCOUNT_NAME from .env
    - Authenticates to root account
    - Discovers accounts from AWS Organizations
    - Saves discovered accounts to .aws.yml

.PARAMETER Account
    Account alias to authenticate to (e.g., 'root', 'sandbox').
    If omitted, shows interactive account selection menu.

.PARAMETER Force
    Force re-login even if credentials are still valid.

.PARAMETER Setup
    Force first-run setup (rediscover accounts).

.PARAMETER Rebuild
    Rebuild .aws.yml and profiles (re-auth only if needed).

.PARAMETER SkipVpc
    Skip ALL resource discovery (auth only, no inventory files).

.PARAMETER SkipResources
    Skip S3/SQS/SNS/SES discovery (VPCs still discovered).

.EXAMPLE
    ./aws-auth.ps1
    # Interactive account selection

.EXAMPLE
    ./aws-auth.ps1 root
    # Login to root account

.EXAMPLE
    ./aws-auth.ps1 sandbox -Force
    # Force re-login to sandbox

.EXAMPLE
    ./aws-auth.ps1 -Rebuild
    # Rebuild config (skip SSO if credentials valid)

.EXAMPLE
    ./aws-auth.ps1 -Rebuild -SkipVpc
    # Fast rebuild (auth only, no inventory)

.EXAMPLE
    ./aws-auth.ps1 -Rebuild -SkipResources
    # Rebuild with VPCs only (skip S3/SQS/SNS/SES)
#>

param(
    [Parameter(Position = 0)]
    [string]$Account,

    [switch]$Force,

    [switch]$Setup,

    [switch]$Rebuild,

    [switch]$SkipVpc,

    [switch]$SkipResources
)

$ErrorActionPreference = "Stop"

# Paths
$skillPath = "${env:CLAUDE_SKILLS_PATH}/aws-login"

if (-Not (Test-Path -Path $skillPath)) {
    throw "AWS login skill not found: $skillPath"
}

# Build arguments
$args = @()

if ($Account) {
    $args += $Account
}

if ($Force) {
    $args += "--force"
}

if ($Setup) {
    $args += "--setup"
}

if ($Rebuild) {
    $args += "--rebuild"
}

if ($SkipVpc) {
    $args += "--skip-vpc"
}

if ($SkipResources) {
    $args += "--skip-resources"
}

# Run via uv
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
