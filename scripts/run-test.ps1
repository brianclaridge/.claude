#!/usr/bin/env pwsh

param(
  [Parameter(ValueFromRemainingArguments)]
  [string[]]
  $remaining_args
)

claude --version 2>&1 | Write-Host

Write-Host ("${PWD}") -ForegroundColor Yellow
Write-Host ("{0,-30} {1,-10} {2,-20} {3,10}" -f "Name", "Type", "LastWriteTime", "Size") -ForegroundColor Cyan
Write-Host ("{0,-30} {1,-10} {2,-20} {3,10}" -f "----", "----", "-------------", "----") -ForegroundColor Cyan

Get-ChildItem -Force | ForEach-Object {
  $type, $color = switch -Regex ($_) {
    { $_.PSIsContainer } { "dir", "Blue"; break }
    { $_.Extension -match '\.(exe|sh|ps1)$' } { "exec", "Green"; break }
    { $_.Extension -match '\.(zip|tar|gz)$' } { "archive", "Red"; break }
    { $_.Extension -match '\.(jpg|png|gif)$' } { "image", "Magenta"; break }
    { $_.Name -match '^\.' } { "hidden", "DarkGray"; break }
    default { "file", "White" }
  }

  $size = if ($_.PSIsContainer) {
    "-"
  }
  elseif ($_.Length -ge 1GB) {
    "{0:N2} GB" -f ($_.Length / 1GB)
  }
  elseif ($_.Length -ge 1MB) {
    "{0:N2} MB" -f ($_.Length / 1MB)
  }
  elseif ($_.Length -ge 1KB) {
    "{0:N2} KB" -f ($_.Length / 1KB)
  }
  else {
    "{0} B" -f $_.Length
  }

  Write-Host ("{0,-30} {1,-10} {2,-20} {3,10}" -f $_.Name, $type, $_.LastWriteTime.ToString("yyyy-MM-dd HH:mm"), $size) -ForegroundColor $color
}
