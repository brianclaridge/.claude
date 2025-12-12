# Plan: Update task:fetch to Only Update .claude Submodule

## Summary
Modify `host:git:fetch` task to only synchronize the `.claude` submodule from origin/main, removing main repo fetch/pull operations.

## Target File
`.claude/Taskfile.yml:175-186`

## Current Implementation
```yaml
host:git:fetch:
  desc: fetches and pulls latest
  aliases:
    - pull
    - fetch
    - get
  deps:
    - ensure-host
  cmds:
    - git fetch
    - git pull
  silent: true
```

## New Implementation
```yaml
host:git:fetch:
  desc: Update .claude submodule from origin
  aliases:
    - pull
    - fetch
    - get
  deps:
    - ensure-host
  cmds:
    - git -C .claude fetch origin && git -C .claude reset --hard origin/main
  silent: true
```

## Changes
1. Update `desc` to reflect new purpose
2. Replace `git fetch` + `git pull` with single submodule update command
3. Retain aliases and `ensure-host` dependency

## TODO
- [x] Edit `.claude/Taskfile.yml` lines 175-186
- [ ] Test task execution with `task fetch`
