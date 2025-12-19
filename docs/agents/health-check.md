# health-check Agent

> Validate .claude environment integrity.

## Overview

Performs comprehensive validation of the .claude environment. Checks configuration, dependencies, and connectivity.

## Invocation

```
/health
```

Or triggered by:
- "check setup"
- "validate environment"
- "run diagnostics"
- "is my setup correct"

## Validation Checks

| Category | Checks |
|----------|--------|
| Configuration | config.yml, settings.json validity |
| Environment | Required env vars in .env |
| Docker | Container and socket access |
| MCP | Server connectivity |
| Dependencies | Tool availability |

## Skills Used

- `health-check` - Validation logic

## Output

Reports issues with severity levels:
- **Error**: Blocking issues requiring fix
- **Warning**: Non-critical issues
- **Info**: Informational findings

## Source

[agents/health-check.md](../../agents/health-check.md)
