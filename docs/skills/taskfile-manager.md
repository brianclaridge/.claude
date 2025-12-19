# taskfile-manager Skill

> Validate Taskfile.yml against best practices (Rule 090).

## Overview

Validates Taskfile.yml configuration against established best practices.

## Activation Triggers

- "/taskfile"
- "validate taskfile"
- "check tasks"
- "taskfile best practices"

## Validation Checks

| Category | Check |
|----------|-------|
| Variables | UPPERCASE naming |
| Templates | No whitespace in `{{.VAR}}` |
| Tasks | kebab-case, colon namespaces |
| Structure | desc, silent, aliases |
| Platform | Cross-platform commands |

## Related

- [Rule 090](../rules/090-taskfile-usage.md)
- [taskfile-manager Agent](../agents/taskfile-manager.md)

## Source

[skills/taskfile-manager/README.md](../../skills/taskfile-manager/README.md)
