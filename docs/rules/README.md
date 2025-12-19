# Rules

Behavioral directives that govern Claude's behavior in the .claude environment.

## Overview

Rules are markdown files in `rules/` numbered 000-095. They define:
- Required behaviors
- Workflow patterns
- Best practices
- Constraints

Rules are loaded at session start by Claude Code and enforced throughout the session.

## Rule Index

| Rule | Name | Description |
|------|------|-------------|
| [000](000-rule-follower.md) | rule-follower | Always evaluate adherence to directives |
| [010](010-session-starter.md) | session-starter | Auto-analyze on session start |
| [020](020-persona.md) | persona | Maintain Spock-like logical persona |
| [030](030-agents.md) | agents | Consider agents for every request |
| [040](040-plans.md) | plans | Create plans for non-trivial tasks |
| [050](050-python.md) | python | Python standards (uv, logging) |
| [060](060-context7.md) | context7 | Use Context7 for library documentation |
| [070](070-backward-compat.md) | backward-compat | No backward compatibility unless requested |
| [080](080-ask-user-questions.md) | ask-user-questions | Use AskUserQuestion tool for clarification |
| [090](090-taskfile-usage.md) | taskfile-usage | Taskfile.yml best practices |
| [095](095-gomplate-usage.md) | gomplate-usage | gomplate template best practices |

## Rule Categories

### Core Directives (000-009)

| Rule | Purpose |
|------|---------|
| 000 | Ensures all rules are evaluated before responding |

### Session Management (010-019)

| Rule | Purpose |
|------|---------|
| 010 | Triggers project-analysis on session start |

### Persona (020-029)

| Rule | Purpose |
|------|---------|
| 020 | Maintains logical, unemotional Spock persona |

### Workflow (030-049)

| Rule | Purpose |
|------|---------|
| 030 | Agent consideration for every request |
| 040 | Plan creation and git-manager invocation |

### Domain-Specific (050-099)

| Rule | Purpose |
|------|---------|
| 050 | Python standards (uv, structlog) |
| 060 | Context7 MCP for library docs |
| 070 | Modern code, no backward compatibility |
| 080 | Interactive questions via AskUserQuestion |
| 090 | Taskfile.yml best practices |
| 095 | gomplate template best practices |

## Rule Priority

Rules are processed in numerical order. Lower numbers have higher priority:
- 000 (highest) - Core compliance
- 010-019 - Session behavior
- 020-029 - Communication style
- 030-049 - Workflow patterns
- 050-099 - Domain standards

## Rule Reinforcement

Some rules can be reinforced on every message via `config.yml`:

```yaml
hooks:
  rules_loader:
    reinforcement_enabled: false
    rules:
      000-rule-follower:
        reinforce: true
      040-plans:
        reinforce: true
```

## Creating New Rules

### Numbering Guidelines

1. Check existing rules for gaps
2. Choose category-appropriate number
3. Avoid collisions with future rules

### Rule Template

```markdown
# RULE: XXX rule-name

**CRITICAL** One-line summary.

## Description

Detailed explanation.

## Examples

Correct and incorrect behavior.

## Exceptions

When rule doesn't apply.
```

See [Development Guide](../DEVELOPMENT.md#creating-rules).

## See Also

- [Agents](../agents/README.md) - Specialized sub-agents
- [Skills](../skills/README.md) - Model-invoked capabilities
- [Development](../DEVELOPMENT.md) - Extension guide
