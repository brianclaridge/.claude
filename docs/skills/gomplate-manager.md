# gomplate-manager Skill

> Validate gomplate templates against best practices (Rule 095).

## Overview

Validates gomplate template configuration against established best practices.

## Activation Triggers

- "/gomplate"
- "validate templates"
- "check gomplate"
- "template best practices"

## Validation Checks

| Category | Check |
|----------|-------|
| Syntax | Valid Go template syntax |
| Env Access | `.Env.VAR` for required vars |
| Paths | Absolute output paths |
| Config | gomplate.yaml structure |

## Related

- [Rule 095](../rules/095-gomplate-usage.md)
- [gomplate-manager Agent](../agents/gomplate-manager.md)

## Source

[skills/gomplate-manager/README.md](../../skills/gomplate-manager/README.md)
