# skill-builder Agent

> Create new Claude Code skills.

## Overview

Scaffolds new skills with proper structure, README, and optional Python implementation.

## Invocation

```
/build-skill
```

Or triggered by:
- "create a skill"
- "build a skill for..."
- "I want to create a new skill"

## Workflow

1. Gather skill requirements
2. Determine activation triggers
3. Create skill directory structure
4. Generate README.md with workflow
5. Create Python implementation (if needed)
6. Update registrations

## Generated Structure

```
skills/my-skill/
├── README.md           # Skill definition
├── lib/                # Python (optional)
│   ├── __init__.py
│   └── main.py
└── pyproject.toml      # Dependencies
```

## Source

[agents/skill-builder.md](../../agents/skill-builder.md)

## See Also

- [Development Guide](../DEVELOPMENT.md#creating-skills)
