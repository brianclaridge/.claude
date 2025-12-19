# rule-builder Agent

> Create new behavioral rules with auto-increment numbering.

## Overview

Scaffolds new behavioral rules following the established pattern and numbering convention.

## Invocation

```
/build-rule
```

Or triggered by:
- "create a rule"
- "new rule for..."
- "add directive"

## Workflow

1. Determine rule category and purpose
2. Find next available number in range
3. Create rule markdown file
4. Configure reinforcement (optional)

## Rule Categories

| Range | Category |
|-------|----------|
| 000-009 | Core directives |
| 010-019 | Session management |
| 020-029 | Persona |
| 030-049 | Workflow |
| 050-099 | Domain-specific |

## Skills Used

- `rule-builder` - Rule scaffolding

## Generated Files

```
rules/XXX-rule-name.md  # Rule definition
```

## Source

[agents/rule-builder.md](../../agents/rule-builder.md)

## See Also

- [Rules Documentation](../rules/README.md)
- [Development Guide](../DEVELOPMENT.md#creating-rules)
