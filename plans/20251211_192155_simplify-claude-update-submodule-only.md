# Plan: Simplify claude:update to Submodule-Only Operations

## Summary
Modify `claude:update` to only commit/push/pull the .claude submodule without touching the parent repo. Task must work from both parent directory and within .claude itself.

## Target File
`.claude/includes/Taskfile.yml:29-48`

## Current Implementation (to remove)
```yaml
claude:update:
  desc: Update .claude submodule and commit the change
  vars:
    MSG: '{{.MSG | default "Update .claude submodule"}}'
  preconditions:
    - sh: |
        git -C .claude fetch --all -q
        git -C .claude status | grep -q "Your branch is behind" || [ -n "$(git -C .claude status --porcelain)" ]
      msg: ".claude submodule is already up to date and has no local changes"
  cmds:
    - git -C .claude add --all
    - git -C .claude diff --cached --quiet || git -C .claude commit -m "{{.MSG}}"
    - git -C .claude push
    - git -C .claude pull origin {{.BRANCH | default "main"}}
    - git add .claude                    # REMOVE
    - git diff --cached --quiet .claude || git commit -m "{{.MSG}}"  # REMOVE
    - git push                           # REMOVE
  silent: true
```

## New Implementation
```yaml
claude:update:
  desc: Commit and sync .claude submodule changes
  vars:
    MSG: '{{.MSG | default "chore: update .claude"}}'
    BRANCH: '{{.BRANCH | default "main"}}'
    GIT_DIR:
      sh: '[ -d .claude ] && echo ".claude" || echo "."'
  preconditions:
    - sh: |
        git -C {{.GIT_DIR}} fetch --all -q
        git -C {{.GIT_DIR}} status | grep -q "Your branch is behind" || [ -n "$(git -C {{.GIT_DIR}} status --porcelain)" ]
      msg: "Submodule is already up to date and has no local changes"
  cmds:
    - git -C {{.GIT_DIR}} add --all
    - git -C {{.GIT_DIR}} diff --cached --quiet || git -C {{.GIT_DIR}} commit -m "{{.MSG}}"
    - git -C {{.GIT_DIR}} push
    - git -C {{.GIT_DIR}} pull origin {{.BRANCH}}
  silent: true
```

## Key Changes
1. **Remove parent repo operations** (lines 45-47)
2. **Add GIT_DIR variable** - detects context:
   - If `.claude/` exists → running from parent → `GIT_DIR=".claude"`
   - If no `.claude/` → running inside submodule → `GIT_DIR="."`
3. **Update description** - reflects submodule-only scope
4. **Update default MSG** - use conventional commit format

## Context Detection Logic
```bash
[ -d .claude ] && echo ".claude" || echo "."
```
- From parent: `.claude` directory exists → returns `.claude`
- From .claude: no `.claude` subdirectory → returns `.`

## TODO
- [x] Edit `.claude/includes/Taskfile.yml` to update `claude:update` task
- [ ] Verify task works from parent directory
- [ ] Verify task works from .claude directory
