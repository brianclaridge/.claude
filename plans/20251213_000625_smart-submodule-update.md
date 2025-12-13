# Plan: Smart Submodule Update Task

## Summary

Replace the `claude:update` task with an intelligent version that:
1. Detects changes in `.claude/` directory
2. Auto-generates commit messages based on changed files
3. Commits and pushes `.claude` submodule changes
4. Updates the parent repo's submodule reference

## Current State

**`scripts/update-submodule.ps1`** (current):
- Takes static `-Message` parameter
- Stages all changes, commits with provided message
- Pushes to origin
- Does NOT auto-generate messages based on changes
- Does NOT update parent repo's submodule reference

**`Taskfile.yml` task**:
```yaml
claude:update:
  cmds:
    - pwsh -NoProfile -File scripts/update-submodule.ps1 -Message "{{.MSG}}" -Branch "{{.BRANCH}}"
```

## Target Behavior

```
$ task update               # From either .claude/ or parent directory

Checking .claude for changes...
Changes detected:
  A agents/new-agent.md
  M hooks/logger/src/__main__.py
  D old-file.py

Committing .claude: chore(.claude): add agents/new-agent.md, update hooks/logger
Pushed to origin/main

Updating parent submodule reference...
Committing parent: chore: update .claude submodule
Pushed to origin/main

Done.
```

## Implementation

### Approach: Rewrite PowerShell Script

Rewrite `scripts/update-submodule.ps1` to:

1. **Detect execution context**:
   - If CWD is `.claude/` → work in place
   - If CWD has `.claude/` subdirectory → work in `.claude/`

2. **Check for `.claude` changes**:
   - Run `git status --porcelain` in `.claude/`
   - Parse output to categorize: Added (A), Modified (M), Deleted (D)

3. **Generate commit message**:
   - Extract file/directory names from changes
   - Format: `chore(.claude): add X, update Y, remove Z`
   - Truncate if too long (max ~72 chars for subject line)

4. **Commit and push `.claude`**:
   - `git add -A`
   - `git commit -m "<generated message>"`
   - `git push origin main`

5. **Update parent repo (if applicable)**:
   - Detect if parent uses `.claude` as submodule (check `../.gitmodules`)
   - If yes:
     - `cd ..`
     - `git add .claude`
     - `git commit -m "chore: update .claude submodule"`
     - `git push origin main`

### Parameters

Keep `-Message` as optional override:
- If provided: use as-is (current behavior)
- If not provided: auto-generate from changes

### Message Generation Logic

**Format**: `chore(.claude): <action> <items>`

```
Changes:
  A agents/foo.md        → "add agents/foo.md"
  M hooks/bar/x.py       → "update hooks/bar"
  D old.txt              → "remove old.txt"

Combined (max 3 items):
  "chore(.claude): add agents/foo.md, update hooks/bar, remove old.txt"

If >3 items:
  "chore(.claude): add agents/foo.md, update hooks/bar (+2 more)"
```

## Files to Modify

| File | Change |
|------|--------|
| `scripts/update-submodule.ps1` | Rewrite with smart detection and two-stage commit |
| `Taskfile.yml` | Update task description (optional) |

## TODO

- [x] Rewrite `scripts/update-submodule.ps1` with change detection
- [x] Implement commit message generation
- [x] Add parent submodule update logic
- [x] Test from both `.claude/` and parent directory
- [x] Update task description in Taskfile.yml
# test
