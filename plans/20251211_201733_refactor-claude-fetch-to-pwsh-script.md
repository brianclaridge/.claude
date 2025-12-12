# Plan: Refactor claude:fetch to PowerShell Script

## Summary
Move fetch logic from Taskfile to a PowerShell script with robust validation and error handling.

## Target Files
- **New:** `.claude/scripts/fetch-submodule.ps1`
- **Modify:** `.claude/includes/Taskfile.yml` (lines 20-27)

## Requirements
1. Validate .claude submodule exists and is properly initialized
2. Ensure correct remote is configured
3. Fetch and reset to origin/main
4. Provide clear error messages if anything is misconfigured

## New Script: `.claude/scripts/fetch-submodule.ps1`

```powershell
#!/usr/bin/env pwsh
# Fetch and reset .claude submodule to origin/main

$ErrorActionPreference = "Stop"

# Determine submodule path based on execution context
$SubmodulePath = if (Test-Path ".claude") { ".claude" } else { "." }

# Validate it's a git repository
if (-not (Test-Path (Join-Path $SubmodulePath ".git"))) {
    Write-Error "ERROR: $SubmodulePath is not a git repository. Run: git submodule init && git submodule update"
    exit 1
}

# Validate remote exists
$remotes = git -C $SubmodulePath remote
if ($remotes -notcontains "origin") {
    Write-Error "ERROR: No 'origin' remote configured in $SubmodulePath"
    exit 1
}

# Fetch and reset
Write-Host "Fetching from origin..."
git -C $SubmodulePath fetch origin

Write-Host "Resetting to origin/main..."
git -C $SubmodulePath reset --hard origin/main

Write-Host "Cleaning untracked files..."
git -C $SubmodulePath clean -fd

Write-Host "Done. Current HEAD:"
git -C $SubmodulePath log -1 --oneline
```

## Updated Taskfile

```yaml
claude:fetch:
  desc: Fetch and reset .claude submodule to origin/main
  cmds:
    - pwsh -NoProfile -File .claude/scripts/fetch-submodule.ps1
  silent: true
```

## TODO
- [x] Create `.claude/scripts/` directory if needed
- [x] Create `fetch-submodule.ps1` script
- [x] Update `claude:fetch` task to call script
- [ ] Verify task syntax
