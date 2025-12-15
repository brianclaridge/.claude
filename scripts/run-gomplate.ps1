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
  # Run gomplate, capture all output to log file only
  gomplate --config $configPath --verbose *> $logPath

  if ($LASTEXITCODE -ne 0) {
    throw "Exit code: $LASTEXITCODE - see $logPath"
  }
}
catch {
  # Append error to log
  $_.Exception.Message | Out-File -FilePath $logPath -Append -Encoding utf8
  throw "Template rendering failed - see $logPath"
}
