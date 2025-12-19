# git-manager Skill

> Interactive git commit workflow with safety checks and user confirmation.

## Overview

Handles the complete git commit workflow including identity configuration, change detection, commit message generation, and push confirmation.

## Activation Triggers

- All plan TODOs marked complete (Rule 040)
- User says "commit changes", "commit my work", "save to git"
- Explicit invocation via gitops agent

## Workflow

### Modes

| Mode | Description |
|------|-------------|
| Commit & Plan | Commit, skip push, enter plan mode |
| Auto | Generate message, commit, push immediately |
| Interactive | Full control over all steps |

### Steps

1. Git identity configuration (from .env or SSH detection)
2. Status check and change detection
3. Mode selection
4. Sensitive file scan
5. Commit message generation (conventional commits)
6. Lock cleanup
7. Stage and commit
8. Push confirmation (optional)
9. Next action selection

## Safety Rules

**Never**:
- Force push
- Skip hooks
- Commit .env files
- Amend pushed commits
- Change remote URLs

## Configuration

Environment variables in `.env`:
```bash
GIT_USER_NAME="Your Name"
GIT_USER_EMAIL="your.email@example.com"
```

## Source

[skills/git-manager/README.md](../../skills/git-manager/README.md)
