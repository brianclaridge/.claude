# logger

A Claude Code hook that logs all hook events to structured JSON files for auditing and debugging.

## Hook Type

- **Universal** - Can be attached to any hook event type
- Typically used with: UserPromptSubmit, SessionStart, PreToolUse, PostToolUse, etc.

## Purpose

Captures complete hook event data and writes it to timestamped JSON files. Useful for:
- Debugging hook behavior
- Auditing Claude Code sessions
- Analyzing tool usage patterns
- Building session history

## Directory Structure

```
logger/
├── config.json          # Configuration settings
├── pyproject.toml       # Python project metadata
├── uv.lock              # Dependency lock file
├── README.md            # This file
├── .venv/               # Virtual environment (auto-created by uv)
└── src/
    ├── __init__.py
    ├── __main__.py      # Entry point
    ├── cli.py           # Command-line argument parsing with help
    ├── paths.py         # Path configuration
    ├── reader.py        # Stdin JSON parsing
    └── writer.py        # JSON file writing with append
```

## Configuration

Edit `config.json` to customize behavior:

```json
{
  "log_base_path": "/workspace/${CLAUDE_PROJECT_SLUG}/.claude/.data/logs/claude_hooks"
}
```

| Setting | Description |
|---------|-------------|
| `log_base_path` | Base directory for all log output |

## How It Works

1. **Receive Event**: Hook receives JSON event data from Claude Code via stdin
2. **Parse Event**: Extracts `session_id` and `hook_event_name` from the data
3. **Create Path**: Builds directory structure: `{log_base_path}/{session_id}/{hook_event_name}/`
4. **Write Log**: Appends event data to a timestamped JSON array file
5. **Return Response**: Outputs JSON allowing execution to continue

## Input Format

The hook receives JSON via stdin (varies by event type):

```json
{
  "hook_event_name": "PostToolUse",
  "session_id": "abc123",
  "tool_name": "Bash",
  "tool_input": {...},
  "tool_output": {...},
  "...other fields..."
}
```

## Output Format

The hook outputs JSON to stdout:

```json
{
  "continue": true,
  "suppressOutput": false
}
```

| Field | Description |
|-------|-------------|
| `continue` | `true` allows execution to proceed |
| `suppressOutput` | `false` shows normal output to user |

## Log Output

Logs are written to:
```
/workspace/${CLAUDE_PROJECT_SLUG}/.claude/.data/logs/claude_hooks/{session_id}/{hook_event_name}/{timestamp}.json
```

Each log file contains a JSON array of events:
```json
[
  {
    "hook_event_name": "PostToolUse",
    "session_id": "abc123",
    "tool_name": "Bash",
    "timestamp": "2025-01-15T10:30:00Z",
    "...complete event data..."
  },
  {
    "...next event..."
  }
]
```

New events are appended to existing files, building a complete history.

## Dependencies

- Python >= 3.12
- No external dependencies (minimal implementation)

## Usage

### Automatic (via Claude Code hooks)

The hook runs automatically when configured in `.claude/settings.json`:

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "command": "uv run --directory /workspace/${CLAUDE_PROJECT_SLUG}/.claude/hooks/logger python -m src"
      }
    ],
    "PostToolUse": [
      {
        "command": "uv run --directory /workspace/${CLAUDE_PROJECT_SLUG}/.claude/hooks/logger python -m src"
      }
    ]
  }
}
```

### Manual Testing

```bash
# Test with sample input
echo '{"hook_event_name": "PostToolUse", "session_id": "test123", "tool_name": "Bash"}' | \
  uv run --directory /workspace/${CLAUDE_PROJECT_SLUG}/.claude/hooks/logger python -m src

# Verify log was created
cat /workspace/${CLAUDE_PROJECT_SLUG}/.claude/.data/logs/claude_hooks/test123/PostToolUse/*.json
```

## Log File Management

Log files accumulate over time. To manage disk space:

```bash
# View all session logs
ls -la /workspace/${CLAUDE_PROJECT_SLUG}/.claude/.data/logs/claude_hooks/

# Remove logs older than 7 days
find /workspace/${CLAUDE_PROJECT_SLUG}/.claude/.data/logs/claude_hooks -type f -mtime +7 -delete

# Remove empty directories
find /workspace/${CLAUDE_PROJECT_SLUG}/.claude/.data/logs/claude_hooks -type d -empty -delete
```

## Interaction with Other Hooks

The logger hook is designed to run alongside other hooks without interference:
- Returns `continue: true` to allow other hooks to execute
- Returns `suppressOutput: false` to preserve normal output
- Minimal processing time to avoid slowing down sessions
