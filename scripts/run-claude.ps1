#!/usr/bin/env pwsh
param(
    [switch]$debug_claude
)

Set-Location "/workspace/${env:CLAUDE_PROJECT_SLUG}"
claude update

if ($debug_claude) {
    claude --continue --debug 2>$null || claude --debug
} else {
    claude --continue 2>$null || claude
}
