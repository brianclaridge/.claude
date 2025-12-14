# Plan: Periodic .claude Submodule Auto-Updater

**Date:** 2025-12-14
**Objective:** Implement periodic auto-update (every 15 minutes) for .claude submodule from upstream with Claude notification

## Architecture (Hook-Based)

```
┌─────────────────────────────────────────────────────────────────┐
│  UserPromptSubmit Hook: submodule_auto_updater                  │
│                                                                 │
│  1. Read last_check_time from state file                        │
│  2. If (now - last_check) > 15 minutes:                         │
│     - git fetch origin (quiet)                                  │
│     - Compare HEAD vs origin/main                               │
│     - If updates available:                                     │
│       - Run: git reset --hard origin/main                       │
│       - Run: git clean -fd                                      │
│       - Record commits pulled                                   │
│     - Update last_check_time                                    │
│  3. If update_performed && not_recently_notified:               │
│     - Inject context to Claude (what was updated)               │
│     - Update last_notify_time                                   │
└─────────────────────────────────────────────────────────────────┘
```

**State Files (in .claude/.data/):**
- `submodule_check_state.json` - Tracks last check time and update history
- `submodule_notify_state.json` - Notification throttling

## Implementation Tasks

### Phase 1: Create Hook Structure
**Directory:** `.claude/hooks/submodule_auto_updater/` (CREATE)

```
submodule_auto_updater/
├── pyproject.toml
└── src/
    ├── __init__.py
    ├── __main__.py
    ├── updater.py        # Git fetch, compare, and update logic
    ├── state_manager.py  # State file read/write
    └── formatter.py      # Notification formatting
```

### Phase 2: Implement Core Logic

**pyproject.toml:**
- Python >=3.11
- Dependencies: structlog

**__main__.py:**
- Read hook event from stdin
- Only process UserPromptSubmit events
- Call updater if 15+ minutes since last check
- Inject notification if update performed and not recently notified
- Output JSON response

**updater.py:**
- `check_and_update()` function
- Runs `git fetch origin --quiet`
- Compares `git rev-parse HEAD` vs `git rev-parse origin/main`
- If different:
  - Get commit log: `git log --oneline HEAD..origin/main`
  - Run: `git reset --hard origin/main`
  - Run: `git clean -fd`
  - Return update summary (commits pulled, old/new hash)
- Returns result dict with `updated: bool`, `commits_pulled: list`, etc.

**state_manager.py:**
- `read_check_state()` - Get last check time
- `write_check_state()` - Update check time and last update info
- `should_notify()` - Check notification throttle (once per session)
- `mark_notified()` - Record notification sent

**formatter.py:**
- `format_update_notification()` - Create context for Claude about what was updated

### Phase 3: Register Hook
**File:** `.claude/config/templates/claude_settings.json`

Add to UserPromptSubmit hooks array:
```json
{
  "type": "command",
  "command": "uv run --directory /workspace/{{ .Env.CLAUDE_PROJECT_SLUG }}/.claude/hooks/submodule_auto_updater python -m src"
}
```

## Files Summary

| File | Action | Purpose |
|------|--------|---------|
| `.claude/hooks/submodule_auto_updater/pyproject.toml` | CREATE | Hook project config |
| `.claude/hooks/submodule_auto_updater/src/__init__.py` | CREATE | Package init |
| `.claude/hooks/submodule_auto_updater/src/__main__.py` | CREATE | Hook entry point |
| `.claude/hooks/submodule_auto_updater/src/updater.py` | CREATE | Git fetch/update logic |
| `.claude/hooks/submodule_auto_updater/src/state_manager.py` | CREATE | State file mgmt |
| `.claude/hooks/submodule_auto_updater/src/formatter.py` | CREATE | Notification text |
| `.claude/config/templates/claude_settings.json` | MODIFY | Register hook |

## State File Formats

**submodule_check_state.json:**
```json
{
  "last_check_time": 1702500000,
  "last_update_time": 1702500000,
  "last_update_result": {
    "updated": true,
    "old_commit": "abc123",
    "new_commit": "def456",
    "commits_pulled": [
      "def456 fix: something",
      "cde345 feat: new feature"
    ]
  }
}
```

**submodule_notify_state.json:**
```json
{
  "last_notified_session": "session-id-123",
  "last_notified_time": 1702500000
}
```

## Notification Content Example

When update is performed, Claude receives context like:
```
## .claude Submodule Updated

The .claude submodule was automatically updated from upstream.

**Previous commit:** abc123
**Current commit:** def456
**Commits pulled:** 2

Changes:
- def456 fix: something
- cde345 feat: new feature

Note: You may need to restart the session if hooks or settings changed significantly.
```

## Throttling Logic

1. **Check throttle:** Only check/update if 15+ minutes since last check
2. **Notify throttle:** Only notify once per session about updates

## Testing

1. Start session
2. Submit any prompt
3. View logs: `.claude/.data/logs/submodule_auto_updater/`
4. View state: `cat .claude/.data/submodule_check_state.json`
5. Manually reset local to older commit to test auto-update

## Advantages Over Cron

- No Dockerfile modifications required
- No entrypoint changes required
- No cron daemon to manage
- Updates only during active usage (not while idle)
- Fully integrated with existing hook architecture
- Simpler debugging via structlog

## Notes

- AUTO-UPDATES by running git reset --hard origin/main
- Informs Claude of what was updated
- Git operations run in .claude submodule directory
- Graceful degradation if .claude is not a git repo
- Uses git clean -fd to remove untracked files (matches task:fetch behavior)
