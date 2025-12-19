# Rule 070: backward-compat

> No backward compatibility unless explicitly requested.

## Priority

Domain-specific (050-099)

## Directive

Do NOT consider backward compatibility unless explicitly requested. Assume breaking changes are acceptable.

## Default Behavior

- Use latest dependency versions
- Current best practices only
- Remove deprecated code
- Single clean implementation path

## Avoid Unless Requested

- Compatibility layers
- Multiple code paths for versions
- Feature flags for old behavior
- Migration guides
- Legacy parameter support

## User Must Say

- "maintain backward compatibility"
- "works with existing system"
- "support version X.Y"
- "don't break existing"

## Example

```python
# Wrong - Unnecessary compatibility
def process(data, legacy=False):
    return old_process(data) if legacy else new_process(data)

# Correct - Clean modern code
def process(data):
    return process_data(data)
```

## Source

[rules/070-backward-compat.md](../../rules/070-backward-compat.md)
