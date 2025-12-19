# session-context Skill

> Gather session context including git status and recent changes.

## Overview

Collects contextual information at session start for the project-analysis agent.

## Activation Triggers

- Session start (via project-analysis agent)
- Invoked by session_context_injector hook

## Data Gathered

- Git branch and status
- Recent commits
- Uncommitted changes
- Recent plans
- Pending work detection

## Usage

```bash
uv run --directory ${CLAUDE_SKILLS_PATH}/session-context \
  python -m src [session_type] --json
```

Session types: `startup`, `resume`, `clear`, `compact`

## Output

JSON with:
- `git_context` - Branch, commits, changes
- `plans` - Recent plan files
- `pending_work` - Detected incomplete tasks

## Source

[skills/session-context/README.md](../../skills/session-context/README.md)
