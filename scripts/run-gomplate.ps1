#!/usr/bin/env pwsh

$ErrorActionPreference = "Stop"

$configPath = "${env:CLAUDE_PATH}/config/gomplate.yaml"
$logPath = "${env:CLAUDE_LOGS_PATH}/gomplate.log"

if (-Not (Test-Path -Path $configPath -PathType Leaf)) {
  throw "Config not found: $configPath"
}

# Ensure log directory exists
$logDir = Split-Path -Parent $logPath
if (-Not (Test-Path -Path $logDir)) {
  New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

try {
  $output = gomplate --config $configPath 2>&1
  $output | Out-File -FilePath $logPath -Encoding utf8

  if ($LASTEXITCODE -ne 0) {
    throw ($output | Out-String)
  }
}
catch {
  # Append error to log
  $_ | Out-File -FilePath $logPath -Append -Encoding utf8
  throw "Template rendering failed - see $logPath"
}
