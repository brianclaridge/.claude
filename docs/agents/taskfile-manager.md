# taskfile-manager Agent

> Validate Taskfile.yml against best practices (Rule 090).

## Overview

Validates Taskfile.yml configuration against Rule 090 best practices. Checks naming conventions, cross-platform compatibility, and structure.

## Invocation

```
/taskfile
```

Or triggered by:
- "validate taskfile"
- "check tasks"
- "taskfile best practices"

## Validation Checks

| Category | Checks |
|----------|--------|
| Variables | UPPERCASE naming |
| Templates | No whitespace in `{{.VAR}}` |
| Tasks | kebab-case naming, colon namespacing |
| Structure | `desc:`, `silent:`, `aliases:` |
| Platform | Cross-platform commands |

## Skills Used

- `taskfile-manager` - Validation logic

## Related Rule

[Rule 090: taskfile-usage](../rules/090-taskfile-usage.md)

## Source

[agents/taskfile-manager.md](../../agents/taskfile-manager.md)
