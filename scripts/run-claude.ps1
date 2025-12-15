#!/usr/bin/env pwsh

param(
  [switch]$Debug
)

$ErrorActionPreference = "Stop"

Set-Location "${env:CLAUDE_WORKSPACE_PATH}"

# Clean up cache and logs
Remove-Item -Recurse -Force "${HOME}/.claude/cache" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "${HOME}/.claude/logs" -ErrorAction SilentlyContinue

# Update claude via npm
npm update -g @anthropic-ai/claude-code 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
  throw "npm update @anthropic-ai/claude-code failed"
}

# Update claude internal
$updateOutput = claude update 2>&1
if ($LASTEXITCODE -ne 0) {
  throw "Claude update failed: $updateOutput"
}

# Start claude
if ($Debug) {
  claude --continue --debug 2>$null || claude --debug
} else {
  claude --continue 2>$null || claude
}

exit $LASTEXITCODE
