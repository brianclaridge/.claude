# Plan: Remove .claude Submodule Script

## Summary

Create a PowerShell script and Taskfile task to completely remove the `.claude` submodule from a parent repository.

## Target Behavior

```
$ task claude:remove-submodule   # From parent directory

Removing .claude submodule...
Deinitializing submodule...
Removing .git/modules/.claude...
Removing .claude from index...
Committing removal...

Done. .claude submodule has been removed.
```

## Implementation

### Script: `scripts/remove-submodule.ps1`

PowerShell equivalent of:
```bash
git submodule deinit -f .claude
rm -rf .git/modules/.claude
git rm -f .claude
git commit -m "Remove .claude submodule"
```

Features:
- Must run from parent directory (not from within `.claude/`)
- Validate `.claude` exists as a submodule before proceeding
- Clear status messages for each step
- Confirmation handled by Taskfile `prompt:` directive

### Taskfile Task

```yaml
claude:remove-submodule:
  aliases:
    - remove-submodule
  desc: Completely remove .claude submodule from parent repository
  prompt: This will permanently remove the .claude submodule. Continue?
  dir: "{{.TASKFILE_DIR}}/.."
  cmds:
    - pwsh -NoProfile -File .claude/scripts/remove-submodule.ps1
```

Note: `dir` is set to parent directory. Taskfile's `prompt:` handles confirmation.

## Files to Create

| File | Purpose |
|------|---------|
| `scripts/remove-submodule.ps1` | PowerShell script for submodule removal |

## Files to Modify

| File | Change |
|------|--------|
| `Taskfile.yml` | Add `claude:remove-submodule` task |

## TODO

- [x] Create `scripts/remove-submodule.ps1`
- [x] Add task to `Taskfile.yml`
