#!/usr/bin/env pwsh

param(
  [switch]$Debug
)

Set-Location "${env:CLAUDE_WORKSPACE_PATH}"

_run "Claude cache cleanup" {
  Remove-Item -Recurse -Force "${HOME}/.claude/cache" -ErrorAction SilentlyContinue
  Remove-Item -Recurse -Force "${HOME}/.claude/logs" -ErrorAction SilentlyContinue
}

_run "Claude npm update" {
  npm update -g @anthropic-ai/claude-code *> $null
  if ($LASTEXITCODE -ne 0) { throw "npm update failed" }
}

_run "Claude update" {
  claude update *> $null
  if ($LASTEXITCODE -ne 0) { throw "claude update failed" }
}

Write-Host ""
_attn "Starting Claude in '${env:CLAUDE_WORKSPACE_PATH}'..."
Write-Host ""

$debugLog = "/root/.claude/debug/latest"
$logFile = "${env:CLAUDE_LOGS_PATH}/claude.log"

# Start background tail to stream debug log to mounted path
$tailJob = Start-Job -ScriptBlock {
  param($src, $dst)
  # Wait for log file to exist
  while (-Not (Test-Path $src)) { Start-Sleep -Milliseconds 500 }
  & tail -f $src >> $dst
} -ArgumentList $debugLog, $logFile

if ($Debug) {
  & claude --continue --debug
}
else {
  & claude --continue
}

$exitCode = $LASTEXITCODE

# Stop the tail job
Stop-Job -Job $tailJob -ErrorAction SilentlyContinue
Remove-Job -Job $tailJob -ErrorAction SilentlyContinue

exit $exitCode
