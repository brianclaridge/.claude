# DIRECTIVE: 070 backward-compat

**CRITICAL** Do NOT consider backward compatibility unless explicitly requested. Assume breaking changes are acceptable.

## DEFAULT: Use modern approaches

- Latest dependency versions
- Current best practices only
- Remove deprecated code
- Single clean implementation path

## AVOID unless user explicitly asks:

- Compatibility layers or adapters
- Multiple code paths for versions
- Feature flags for old behavior
- Migration guides or deprecation warnings
- Legacy parameter support

## User must say things like:

- "maintain backward compatibility"
- "works with existing system"
- "support version X.Y"
- "don't break existing"

## Example:

```python
# ❌ WRONG - Unnecessary compatibility
def process(data, legacy=False):
    return old_process(data) if legacy else new_process(data)

# ✓ CORRECT - Clean modern code
def process(data):
    return process_data(data)
```
