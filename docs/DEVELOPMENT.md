# Development Guide

> How to extend the .claude environment with custom agents, skills, hooks, and rules.

## Creating Agents

Agents are specialized sub-agents invoked via the Task tool. They're defined as markdown files in `agents/`.

### Agent Structure

```markdown
# Agent Name

Brief description of what this agent does.

## Capabilities

- Capability 1
- Capability 2

## When to Use

Describe when Claude should invoke this agent.

## Workflow

1. Step 1
2. Step 2
3. ...

## Tools Available

List the tools this agent can access.

## Example

Show example usage or output.
```

### Creating a New Agent

1. Create `agents/my-agent.md`
2. Add entry to `settings.json` under `agents`
3. Optionally create a slash command in `commands/`

See [Agents Documentation](agents/README.md) for examples.

## Creating Skills

Skills are model-invoked capabilities that Claude activates when triggers match.

### Skill Structure

```
skills/my-skill/
├── README.md      # Skill definition and triggers
├── lib/           # Python implementation (optional)
└── scripts/       # Helper scripts (optional)
```

### Skill README Template

```markdown
# My Skill

Description of what this skill does.

## Activation Triggers

- "trigger phrase 1"
- "trigger phrase 2"
- User says "/command"

## Workflow

### Step 1: Initialization
...

### Step 2: Main Logic
...

## Configuration

Settings from config.yml or .env.

## Error Handling

How errors are handled.
```

### Creating a New Skill

1. Create `skills/my-skill/README.md`
2. Add Python implementation in `lib/` if needed
3. Register in `commands/*.md` for slash command access
4. Update `settings.json` if tool permissions needed

See [Skills Documentation](skills/README.md) for examples.

## Creating Hooks

Hooks are Python scripts that execute on Claude Code events.

### Hook Events

| Event | Description |
|-------|-------------|
| `Stop` | After Claude completes a turn |
| `UserPromptSubmit` | Before user message is sent |
| `SessionStart` | When session begins/resumes |

### Hook Structure

```
hooks/my-hook/
├── __init__.py
├── run.py          # Main handler
└── pyproject.toml  # Dependencies
```

### Hook Implementation

```python
# hooks/my-hook/run.py
import sys
import json

def main():
    # Read event data from stdin
    event_data = json.loads(sys.stdin.read())

    hook_type = event_data.get("hook_type")
    payload = event_data.get("payload", {})

    # Process event
    result = {
        "success": True,
        "message": "Hook executed"
    }

    # Output result
    print(json.dumps(result))

if __name__ == "__main__":
    main()
```

### Registering a Hook

Add to `settings.json`:

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {"type": "command", "command": "uv run --directory hooks/my-hook python -m run"}
    ]
  }
}
```

## Creating Rules

Rules are behavioral directives that govern Claude's behavior.

### Rule Numbering

| Range | Category |
|-------|----------|
| 000-009 | Core directives |
| 010-019 | Session management |
| 020-029 | Persona |
| 030-049 | Workflow |
| 050-099 | Domain-specific |

### Rule Template

```markdown
# RULE: XXX rule-name

**CRITICAL** One-line summary of the rule.

## Description

Detailed explanation of what this rule enforces.

## Examples

Show examples of correct and incorrect behavior.

## Exceptions

When this rule does not apply.
```

### Creating a New Rule

1. Find appropriate number (check `rules/` for gaps)
2. Create `rules/XXX-rule-name.md`
3. Optionally enable reinforcement in `config.yml`

See [Rules Documentation](rules/README.md) for all rules.

## Creating Stacks

Stacks are application templates for the stack-manager.

### Stack Template

```markdown
# Stack Name

> One-line description

## Technology Stack

| Component | Technology |
|-----------|------------|
| Frontend | ... |
| Backend | ... |
| Database | ... |

## Use Cases

- Use case 1
- Use case 2

## Project Structure

```text
project/
├── ...
```

## Getting Started

```bash
# Setup commands
```

## Configuration

Required environment variables and settings.
```

### Creating a New Stack

1. Create `stacks/my-stack.md`
2. Update stack-manager skill to include it
3. Test with `/stack-manager`

See [Stacks Documentation](stacks/README.md) for examples.

## Testing Changes

### Testing Agents

```bash
# Start session and invoke
/my-agent
```

### Testing Skills

Skills are invoked automatically by Claude when triggers match.

### Testing Hooks

```bash
# Test hook directly
echo '{"hook_type": "UserPromptSubmit", "payload": {}}' | \
  uv run --directory hooks/my-hook python -m run
```

### Testing Rules

Rules are loaded at session start. Verify behavior in conversation.

## Best Practices

1. **Keep agents focused** - One responsibility per agent
2. **Document triggers** - Clear activation conditions for skills
3. **Log in hooks** - Use structured logging for debugging
4. **Number rules carefully** - Consider priority and category
5. **Test incrementally** - Verify each component works alone

## See Also

- [Architecture](ARCHITECTURE.md) - System design
- [Troubleshooting](TROUBLESHOOTING.md) - Common issues
