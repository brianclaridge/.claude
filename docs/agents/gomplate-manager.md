# gomplate-manager Agent

> Validate gomplate templates against best practices (Rule 095).

## Overview

Validates gomplate template configuration against Rule 095 best practices. Checks syntax, environment variable access, and output paths.

## Invocation

```
/gomplate
```

Or triggered by:
- "validate templates"
- "check gomplate"
- "template best practices"

## Validation Checks

| Category | Checks |
|----------|--------|
| Syntax | Valid Go template syntax |
| Env Access | `.Env.VAR` for required variables |
| Paths | Absolute output paths |
| Structure | gomplate.yaml configuration |

## Skills Used

- `gomplate-manager` - Validation logic

## Related Rule

[Rule 095: gomplate-usage](../rules/095-gomplate-usage.md)

## Source

[agents/gomplate-manager.md](../../agents/gomplate-manager.md)
