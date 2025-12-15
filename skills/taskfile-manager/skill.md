---
name: taskfile-manager
description: Validate Taskfile.yml against best practices (Rule 090). Use when user says "/taskfile", "validate taskfile", "check tasks", "taskfile best practices".
tools: Read, Glob, Grep
---

# Taskfile Manager Skill

Validate Taskfile.yml against official best practices from taskfile.dev and Rule 090.

## Activation Triggers

- User invokes `/taskfile` command
- User says "validate taskfile", "check tasks"
- User says "taskfile best practices", "audit taskfile"

## Workflow

### Step 1: Locate Taskfile

Find Taskfile.yml in the project:

```bash
# Check common locations
- ./Taskfile.yml
- ./Taskfile.yaml
- ./.claude/Taskfile.yml
```

### Step 2: Parse and Validate

Read the Taskfile and check each rule from Rule 090:

| Check | Rule | Severity |
|-------|------|----------|
| Variable naming | UPPERCASE only | Error |
| Template syntax | No whitespace in `{{.VAR}}` | Error |
| Task naming | kebab-case | Warning |
| Namespace format | Colon-separated | Warning |
| Task descriptions | `desc:` present | Warning |
| Aliases | `aliases:` for common tasks | Info |
| Silent mode | `silent: true` | Info |
| Platform directive | `platforms:` for OS-specific | Warning |
| Cross-platform | pwsh compatibility | Warning |
| Script preference | External scripts for complex | Info |

### Step 3: Generate Report

Output validation report with line numbers:

```
Taskfile Validation Report
==========================
File: ./Taskfile.yml

ERRORS (must fix):
  Line 12: Variable 'binary_name' should be UPPERCASE → 'BINARY_NAME'
  Line 45: Template '{{ .VAR }}' has whitespace → '{{.VAR}}'

WARNINGS (should fix):
  Line 23: Task 'buildApp' should be kebab-case → 'build-app'
  Line 34: Missing 'desc:' for public task 'deploy'
  Line 56: Command 'rm -rf' may fail on Windows
           Suggestion: Add 'platforms: [linux, darwin]' or use pwsh

INFO (optional):
  Line 67: Consider adding 'aliases:' for task 'docker:build'
  Line 89: Consider 'silent: true' for cleaner output

Summary: 2 errors, 3 warnings, 2 info
```

### Step 4: Suggest Fixes

For each violation, provide the corrected YAML:

```yaml
# Before (Line 12)
vars:
  binary_name: myapp

# After
vars:
  BINARY_NAME: myapp
```

## Validation Rules Detail

### Variable Naming (Error)

Pattern: `/^[A-Z][A-Z0-9_]*$/`

```yaml
# Scan vars: section for lowercase
vars:
  VALID_VAR: ok
  invalid_var: error  # Flag this
```

### Template Whitespace (Error)

Pattern: `/\{\{\s+\./` or `/\.\s+\}\}/`

```yaml
# Flag any template with internal whitespace
cmd: echo {{ .VAR }}  # Error
cmd: echo {{.VAR}}    # OK
```

### Task Naming (Warning)

Pattern: Task names should be `/^[a-z][a-z0-9-]*$/` or namespace format `/^[a-z][a-z0-9-]*:[a-z][a-z0-9-]*$/`

```yaml
tasks:
  build-app:     # OK
  docker:build:  # OK
  buildApp:      # Warning
  Build_App:     # Warning
```

### Platform Detection (Warning)

Flag OS-specific commands without `platforms:`:

```yaml
# Unix-only commands that need platforms:
rm -rf, chmod, chown, ln -s, grep, sed, awk

# Windows-only commands that need platforms:
del, rmdir, copy, move, icacls
```

### Cross-Platform Suggestion

When detecting OS-specific commands, suggest pwsh alternative:

```yaml
# Instead of:
cmd: rm -rf ./dist

# Suggest:
cmd: pwsh -c "Remove-Item -Recurse -Force ./dist -ErrorAction SilentlyContinue"
```

## Output Format

Always output a structured report. Use checkmarks for passed items:

```
✓ Variable naming: PASSED (12/12 uppercase)
✗ Template whitespace: FAILED (2 violations)
✓ Task descriptions: PASSED (8/8 have desc:)
⚠ Platform directive: WARNING (1 issue)
✓ Silent mode: PASSED
✓ Namespace consistency: PASSED

Overall: 1 error, 1 warning
Status: NEEDS FIXES
```

## Python Validator Script

For automated validation, use the Python validator script:

```bash
# Run validation (text output)
uv run --directory ${CLAUDE_SKILLS_PATH}/taskfile-manager python -m scripts ./Taskfile.yml

# Run validation (JSON output for programmatic use)
uv run --directory ${CLAUDE_SKILLS_PATH}/taskfile-manager python -m scripts ./Taskfile.yml --format json

# Strict mode (treat warnings as errors)
uv run --directory ${CLAUDE_SKILLS_PATH}/taskfile-manager python -m scripts ./Taskfile.yml --strict
```

The Python script provides:
- Line number tracking via ruamel.yaml
- JSON output for CI integration
- Exit codes for automation (0=pass, 1=fail)

## Integration

This skill is invoked by:
- `/taskfile` command
- `taskfile-manager` agent
- Direct skill invocation
- Python script for automation
