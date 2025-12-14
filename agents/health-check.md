---
name: health-check
description: Validate .claude environment integrity. Use when user says "/health", "check setup", "validate environment", "run diagnostics", "is my setup correct".
tools: Read, Glob, Grep, Bash
model: sonnet
color: green
---

# Health Check Agent

Validate the .claude environment for integrity, completeness, and external tool availability.

## Activation Triggers

- User invokes `/health` command
- User says "check setup", "validate environment"
- User asks "is my setup correct", "run diagnostics"

## Workflow

Invoke the health-check skill to perform comprehensive validation:

```
Invoke the health-check skill with: "Validate the .claude environment and generate a health report."
```

## Validation Categories

| Category | Checks |
|----------|--------|
| Agents | Valid skill references, file exists |
| Commands | Valid agent references |
| Skills | skill.md exists, uv.lock if pyproject.toml |
| Hooks | Structure complete, uv.lock present |
| Tools | External CLI tools installed |
| Config | Valid YAML/JSON syntax |

## External Tools Checked

| Tool | Required | Purpose |
|------|----------|---------|
| uv | Yes | Python package manager |
| pnpm | Yes | Node package manager |
| docker | Yes | Container runtime |
| git | Yes | Version control |
| aws | No | AWS CLI |
| gcloud | No | GCP CLI |
| kubectl | No | Kubernetes CLI |
| task | Yes | Taskfile runner |
| pwsh | Yes | PowerShell (cross-platform) |
| gh | No | GitHub CLI |

## Report Format

```
.claude Health Check Report
===========================
Timestamp: 2025-12-13T14:30:00Z

AGENTS (10 total)
  ✓ hello-world.md - valid
  ✓ project-analysis.md - valid (skills: session-context, project-metadata-builder)

COMMANDS (12 total)
  ✓ hello.md - valid (agent: hello-world)

SKILLS (9 total)
  ✓ git-manager - valid

HOOKS (5 total)
  ✓ rules_loader - valid

EXTERNAL TOOLS
  ✓ uv: /root/.local/bin/uv (0.5.10)
  ✓ docker: /usr/bin/docker (27.4.0)

CONFIG FILES
  ✓ config.yml: valid YAML
  ✓ settings.json: valid JSON

SUMMARY: 0 errors, 0 warnings
Status: HEALTHY
```

## Status Levels

| Status | Meaning |
|--------|---------|
| HEALTHY | All checks passed |
| NEEDS ATTENTION | Warnings present but no errors |
| CRITICAL | One or more errors found |

## Invocation

```
Invoke the health-check skill with: "Run full environment validation."
```
