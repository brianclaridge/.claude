#!/usr/bin/env pwsh
param(
  [switch]$debug_claude,

  [Parameter(ValueFromRemainingArguments = $true)]
  [string[]]$RemainingArgs
)

Set-Location "/workspace${env:CLAUDE_PROJECT_SLUG}"

_attn "Checking for latest claude code version..."

claude update

_attn "Starting claude code in '/workspace${env:CLAUDE_PROJECT_SLUG}'..."

if ($debug_claude) {
  claude --continue --debug 2>$null || claude --debug
}
else {
  claude --continue 2>$null || claude
}
