#!/usr/bin/env pwsh
Set-Location "/workspace/${env:CLAUDE_PROJECT_SLUG}"
claude update
claude --continue 2>$null || claude
