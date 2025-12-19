# Rule 050: python

> Python standards using uv and structured logging.

## Priority

Domain-specific (050-099)

## Directive

Python projects should:
1. Use `uv run` syntax
2. Have structured/organized code (no large monolithic files)
3. Include logging (loguru or structlog)

## Examples

**Correct:**
```bash
uv run pytest tests/
uv run python -m myapp
```

**Incorrect:**
```bash
python myapp.py
pytest tests/
```

## Logging

Use either:
- `loguru` - Simple, batteries-included
- `structlog` - Structured JSON logging

## Source

[rules/050-python.md](../../rules/050-python.md)
