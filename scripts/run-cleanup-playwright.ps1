#!/usr/bin/env pwsh

$ErrorActionPreference = "Stop"

$maxAgeMinutes = 30
$now = Get-Date

$paths = @(
  @{ Path = "/usr/local/share/playwright"; Pattern = "mcp-*" },
  @{ Path = "/tmp"; Pattern = "*playwright*" }
)

$cleaned = 0

foreach ($item in $paths) {
  if (-Not (Test-Path -Path $item.Path)) {
    continue
  }

  Get-ChildItem -Path $item.Path -Directory -Filter $item.Pattern -ErrorAction SilentlyContinue |
  Where-Object { ($now - $_.LastWriteTime).TotalMinutes -gt $maxAgeMinutes } |
  ForEach-Object {
    try {
      _rmrf $_.FullName
      $cleaned++
    }
    catch {
      # Ignore removal failures (may be in use)
    }
  }
}

# Return count for optional logging
$cleaned
