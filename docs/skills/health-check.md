# health-check Skill

> Validate .claude environment integrity.

## Overview

Performs comprehensive validation of the .claude environment configuration and dependencies.

## Activation Triggers

- "/health"
- "check setup"
- "validate environment"
- "run diagnostics"
- "is my setup correct"

## Validation Checks

| Category | Checks |
|----------|--------|
| Config | config.yml, settings.json |
| Environment | .env variables |
| Docker | Container, socket access |
| MCP | Server connectivity |
| Dependencies | Tool availability |

## Output

Reports with severity levels:
- **Error** - Blocking issues
- **Warning** - Non-critical issues
- **Info** - Informational

## Related

- [health-check Agent](../agents/health-check.md)
- [Troubleshooting](../TROUBLESHOOTING.md)

## Source

[skills/health-check/README.md](../../skills/health-check/README.md)
