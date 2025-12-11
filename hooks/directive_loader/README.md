# directive_loader

A Claude Code hook that loads markdown directive files and injects them as additional context into sessions.

## Hook Type

- **UserPromptSubmit** - Triggers on every user message submission
- **SessionStart** - Triggers when a new session begins

## Purpose

Scans the `/workspace/.claude/directives/` directory for markdown files (`.md`) and combines their content into a single context injection. This allows you to define persistent instructions, guidelines, or context that Claude should follow throughout a session.

## Directory Structure

```
directive_loader/
├── config.json          # Configuration settings
├── pyproject.toml       # Python project metadata
├── uv.lock              # Dependency lock file
├── README.md            # This file
├── .venv/               # Virtual environment (auto-created by uv)
└── src/
    ├── __init__.py
    ├── __main__.py      # Entry point
    ├── cli.py           # Command-line argument parsing
    ├── formatter.py     # JSON output formatting
    ├── loader.py        # Core directive loading logic
    ├── logger.py        # Structured event logging
    ├── paths.py         # Path configuration
    └── reader.py        # Stdin JSON parsing
```

## Configuration

Edit `config.json` to customize behavior:

```json
{
  "log_base_path": "/workspace/.claude/.data/logs/directive_loader",
  "directives_path": "/workspace/.claude/directives",
  "log_enabled": true,
  "log_level": "INFO"
}
```

| Setting | Description |
|---------|-------------|
| `log_base_path` | Directory for log output |
| `directives_path` | Directory containing `.md` directive files |
| `log_enabled` | Enable/disable logging |
| `log_level` | Log verbosity: DEBUG, INFO, WARNING, ERROR |

## How It Works

1. **Receive Event**: Hook receives JSON event data from Claude Code via stdin
2. **Scan Directives**: Reads all `.md` files from the configured directives path
3. **Combine Content**: Concatenates all directive content with `\n\n` separators
4. **Log Event**: Records directive loading metadata (count, filenames, load time)
5. **Return Context**: Outputs JSON with combined directives as `additionalContext`

## Input Format

The hook receives JSON via stdin:

```json
{
  "hook_event_name": "UserPromptSubmit",
  "session_id": "abc123",
  "...other fields..."
}
```

## Output Format

The hook outputs JSON to stdout:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "UserPromptSubmit",
    "additionalContext": "# DIRECTIVE: 010\n\nContent of first directive...\n\n# DIRECTIVE: 020\n\nContent of second directive..."
  }
}
```

## Log Output

Logs are written to:
```
/workspace/.claude/.data/logs/directive_loader/{session_id}/{hook_event_name}/{timestamp}.json
```

Log entries include:
- Directive count
- Filenames loaded
- Load time (ms)
- Combined content length

## Dependencies

- Python >= 3.12
- structlog >= 24.0.0

## Usage

### Automatic (via Claude Code hooks)

The hook runs automatically when configured in `.claude/settings.json`:

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "command": "uv run --directory /workspace/.claude/hooks/directive_loader python -m src"
      }
    ],
    "SessionStart": [
      {
        "command": "uv run --directory /workspace/.claude/hooks/directive_loader python -m src"
      }
    ]
  }
}
```

### Manual Testing

```bash
# Test with sample input
echo '{"hook_event_name": "UserPromptSubmit", "session_id": "test123"}' | \
  uv run --directory /workspace/.claude/hooks/directive_loader python -m src

# With debug logging
echo '{"hook_event_name": "UserPromptSubmit", "session_id": "test123"}' | \
  uv run --directory /workspace/.claude/hooks/directive_loader python -m src --debug
```

## Creating Directives

Add markdown files to `/workspace/.claude/directives/`:

```markdown
# DIRECTIVE: 010 example

**CRITICAL** This is an example directive.

## Rules

- Rule 1
- Rule 2
```

Files are loaded in alphabetical order. Use numeric prefixes (010, 020, etc.) to control ordering.
