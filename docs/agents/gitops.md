# gitops Agent

> Git commit workflow with branch management and push confirmation.

## Overview

Orchestrates the git commit workflow by invoking the git-manager skill. Handles identity configuration, commit message generation, and optional push.

## Invocation

```
/gitops
```

Or triggered by:
- "commit changes"
- "commit my work"
- "save to git"
- All TODOs marked complete (Rule 040)

## Workflow

1. Git identity configuration
2. Change detection
3. Mode selection (auto/interactive)
4. Branch selection
5. Commit message generation
6. Push confirmation
7. Next action selection

## Skills Used

- `git-manager` - Complete git workflow

## Configuration

| Setting | Value |
|---------|-------|
| Allowed Tools | Bash, Read, Glob, Grep, AskUserQuestion, EnterPlanMode |

## Source

[agents/gitops.md](../../agents/gitops.md)
