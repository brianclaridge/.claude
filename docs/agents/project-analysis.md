# project-analysis Agent

> Comprehensive codebase analysis and exploration.

## Overview

Performs deep analysis of project structure, functionality, and architecture. Automatically invoked on session start per Rule 010.

## Invocation

```
/analyze
```

Or automatically on session start.

## Capabilities

- Project structure visualization (`tree` command)
- Functional analysis (what the code does)
- Technology detection
- Architecture identification
- Git context integration

## Analysis Modes

| Mode | Trigger | Focus |
|------|---------|-------|
| Full | startup, clear | Comprehensive all-sections analysis |
| Abbreviated | resume, compact | Recent changes and pending work |

## Workflow

1. Invoke `session-context` skill for context gathering
2. Analyze project structure
3. Identify key components and patterns
4. Detect technologies and frameworks
5. Summarize pending work (if any)
6. Invoke `project-metadata-builder` skill

## Skills Used

- `session-context` - Git status, recent commits
- `project-metadata-builder` - Project registry update

## Configuration

| Setting | Value |
|---------|-------|
| Model | sonnet |
| Tools | All |
| Color | pink |

## Source

[agents/project-analysis.md](../../agents/project-analysis.md)
