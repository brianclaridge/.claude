# Plan: Add -debug_claude Parameter to run-claude.ps1

## Summary

Update `run-claude.ps1` to accept a `-debug_claude` switch parameter so that `claude:debug` task can pass it when running outside Docker.

## Implementation

### 1. Update `scripts/run-claude.ps1`

Add `-debug_claude` switch parameter:

```powershell
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
```

### 2. Update `claude:debug` task

Pass `-debug_claude` when calling run-claude outside Docker:

```yaml
docker compose run --remove-orphans claude pwsh -NoProfile -File ${CLAUDE_PATH}/scripts/run-claude.ps1 -debug_claude
```

## Files Modified

| File | Change |
|------|--------|
| `.claude/scripts/run-claude.ps1` | Add `-debug_claude` parameter |
| `.claude/Taskfile.yml` | Update `claude:debug` to pass `-debug_claude` |

## TODO

- [x] Add `-debug_claude` switch parameter to `run-claude.ps1`
- [x] Update `claude:debug` task to pass `-debug_claude` flag
