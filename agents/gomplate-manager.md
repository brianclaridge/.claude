---
name: gomplate-manager
description: Validate gomplate templates against best practices (Rule 095). Use when user says "/gomplate", "validate templates", "check gomplate", "template best practices".
tools: Read, Glob, Grep, Bash, AskUserQuestion
model: sonnet
color: cyan
---

# Gomplate Manager Agent

Validate gomplate templates and configuration against Rule 095 best practices.

## Activation Triggers

- User invokes `/gomplate` command
- User says "validate templates", "check gomplate"
- User says "template best practices", "audit templates"

## Workflow

### Step 1: Locate Configuration

Find gomplate.yaml in the project. Check standard locations:
- `.claude/config/gomplate.yaml`
- `./config/gomplate.yaml`

### Step 2: Execute Validation

Invoke the gomplate-manager skill:

```
Invoke the gomplate-manager skill with: "Validate gomplate configuration and templates against Rule 095 best practices."
```

The skill will:
1. Parse the YAML configuration
2. Validate all template files for syntax errors
3. Check best practices from Rule 095
4. Run dry-run rendering with current environment
5. Generate detailed report with line numbers

### Step 3: Report Results

Present the validation report with:
- Errors (must fix) - syntax errors, missing variables
- Warnings (should fix) - best practice violations
- Info (optional improvements) - style suggestions

### Step 4: Offer Fixes

If violations found, use AskUserQuestion to ask if user wants:
- Detailed fix suggestions
- Automatic fixes applied
- Test render with mock environment
- Skip and just report

## Validation Categories

| Category | Severity | Description |
|----------|----------|-------------|
| Syntax errors | Error | Invalid template syntax |
| Missing variables | Error | Required env vars not set |
| Config structure | Error | Invalid gomplate.yaml |
| Variable access | Warning | Use .Env over getenv |
| Whitespace | Info | Consistent spacing in templates |

## Invocation

```
Invoke the gomplate-manager skill with: "Validate gomplate templates against Rule 095 best practices."
```
