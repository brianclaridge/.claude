# agent-builder Agent

> Create new Claude Code agents.

## Overview

Scaffolds new agents with proper configuration and optional slash command.

## Invocation

```
/build-agent
```

Or triggered by:
- "create an agent"
- "build an agent for..."
- "I want to create a new agent"

## Workflow

1. Gather agent requirements
2. Determine capabilities and tools
3. Create agent markdown file
4. Create slash command (optional)
5. Update registrations

## Generated Files

```
agents/my-agent.md      # Agent definition
commands/my-agent.md    # Slash command (optional)
```

## Configuration Options

| Option | Description |
|--------|-------------|
| name | Agent identifier |
| description | When to invoke |
| model | sonnet, opus, haiku |
| tools | Allowed tools or * |
| color | Terminal color |

## Source

[agents/agent-builder.md](../../agents/agent-builder.md)

## See Also

- [Development Guide](../DEVELOPMENT.md#creating-agents)
