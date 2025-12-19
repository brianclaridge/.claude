---
# REQUIRED FIELDS
name: agent-name
description: Brief description of when to use this agent. Include trigger phrases.
tools: Read, Write, Edit, Glob, Grep, Bash

# OPTIONAL FIELDS
model: sonnet          # Options: sonnet (default), opus, haiku
color: blue            # Unique color for terminal display (see color guide below)
---

# Agent Name

Detailed description of the agent's purpose and capabilities.

## When to Use

- Trigger condition 1
- Trigger condition 2
- User says "keyword" or "phrase"

## Workflow

### Step 1: Initial Action

Description of what the agent does first.

### Step 2: Processing

Description of main processing steps.

### Step 3: Output

Description of what the agent returns.

## Example

```
User: example input
Agent: example output
```

---

## Field Reference

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Kebab-case identifier (e.g., `my-agent`) |
| `description` | string | When/why to invoke this agent |
| `tools` | string | Comma-separated tool names or `*` for all |

### Optional Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `model` | enum | sonnet | Model to use: `haiku`, `sonnet`, `opus` |
| `color` | string | auto | Terminal display color |

### Model Selection Guide

| Model | Use Case | Cost |
|-------|----------|------|
| `haiku` | Simple tasks, fast responses | $ |
| `sonnet` | Balanced capability/cost | $$ |
| `opus` | Complex reasoning, planning | $$$$ |

### Available Colors

Use unique colors to distinguish agents in terminal output:

| Color | Current Usage |
|-------|---------------|
| `blue` | project-analysis |
| `green` | gitops |
| `yellow` | plan |
| `cyan` | gomplate-manager |
| `magenta` | stack-manager |
| `purple` | rule-builder |
| `teal` | skill-builder |
| `white` | hello-world |
| `orange` | browser-automation |
| `red` | (reserved for errors) |

### Tools Reference

Common tool combinations:

- **Read-only**: `Read, Glob, Grep`
- **Read-write**: `Read, Write, Edit, Glob, Grep`
- **Full access**: `*` (all tools)
- **With user interaction**: `Read, Write, Edit, Glob, Grep, Bash, AskUserQuestion`
