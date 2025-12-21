#!/usr/bin/env pwsh

param(
  [switch]
  $stream_claude,

  [switch]
  $debug_claude,

  [Parameter(ValueFromRemainingArguments)]
  [string[]]
  $remaining_args
)

_run "claude data cleanup" {
  _rmrf "${HOME}/.claude/debug"
  _rmrf "${HOME}/.claude/cache"
  _rmrf "${HOME}/.claude/logs"
}

_run "claude npm update" {
  npm update -g @anthropic-ai/claude-code *> $null
  if ($LASTEXITCODE -ne 0) { throw "npm update failed" }
}

_run "claude update" {
  claude update *> $null
  if ($LASTEXITCODE -ne 0) { throw "claude update failed" }
}

_attn "Starting Claude in '${env:WORKSPACE_PATH}'..."
Set-Location "${env:WORKSPACE_PATH}"

if ($debug_claude) {
  _warn "debug mode"
  & claude --continue --debug 2> $null || claude --debug
}
elseif ($stream) {
  _warn "strem mode"
  $msg = @{
    type               = "user"
    message            = @{
      role    = "user"
      content = ($remaining_args -join ' ')
    }
    session_id         = "default"
    parent_tool_use_id = $null
  } | ConvertTo-Json -Compress

  $msg | & claude --print --fork-session --input-format stream-json --output-format stream-json --verbose
}
else {
  & claude --continue 2> $null || claude
}

$exitCode = $LASTEXITCODE

exit $exitCode
