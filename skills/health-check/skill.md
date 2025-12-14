---
name: health-check
description: Validate .claude environment integrity. Use when user says "/health", "check setup", "validate environment", "run diagnostics".
tools: Read, Glob, Grep, Bash
---

# Health Check Skill

Validate the .claude environment for integrity, completeness, and external tool availability.

## Activation Triggers

- User invokes `/health` command
- User says "check setup", "validate environment", "run diagnostics"
- User asks "is my setup correct", "are my agents working"

## Workflow

### Step 1: Discover Components

```bash
# Find all components
AGENTS=$(ls /workspace/${CLAUDE_PROJECT_SLUG}/.claude/agents/*.md 2>/dev/null)
COMMANDS=$(ls /workspace/${CLAUDE_PROJECT_SLUG}/.claude/commands/*.md 2>/dev/null)
SKILLS=$(ls -d /workspace/${CLAUDE_PROJECT_SLUG}/.claude/skills/*/ 2>/dev/null)
HOOKS=$(ls -d /workspace/${CLAUDE_PROJECT_SLUG}/.claude/hooks/*/ 2>/dev/null)
```

### Step 2: Validate Agent-Skill References

For each agent in `agents/*.md`:
1. Read YAML frontmatter
2. Extract skill references from description text
3. Check if referenced skill exists in `skills/*/skill.md`

Pattern to detect skill references:
- "Skills Used: skill-name"
- "Invokes: skill-name skill"
- Text containing skill directory names

### Step 3: Validate Command-Agent References

For each command in `commands/*.md`:
1. Read content
2. Extract agent references (pattern: "the X agent", "X-agent")
3. Check if referenced agent exists in `agents/*.md`

### Step 4: Validate Skill Completeness

For each skill directory in `skills/*/`:
1. Verify `skill.md` or `SKILL.md` exists
2. If `pyproject.toml` exists, verify `uv.lock` present
3. If `src/` exists, verify `__main__.py` present

### Step 5: Check External Tools

Required tools to verify:

| Tool | Command | Purpose |
|------|---------|---------|
| uv | `uv --version` | Python package manager |
| pnpm | `pnpm --version` | Node package manager |
| docker | `docker --version` | Container runtime |
| aws | `aws --version` | AWS CLI |
| gcloud | `gcloud --version` | GCP CLI |
| kubectl | `kubectl version --client` | Kubernetes CLI |
| task | `task --version` | Taskfile runner |
| pwsh | `pwsh --version` | PowerShell |
| gh | `gh --version` | GitHub CLI |
| git | `git --version` | Version control |

### Step 6: Validate Configuration Files

Check config files are valid:

```bash
# Validate YAML
python3 -c "import yaml; yaml.safe_load(open('/workspace/${CLAUDE_PROJECT_SLUG}/.claude/config.yml'))"

# Validate JSON
python3 -c "import json; json.load(open('/workspace/${CLAUDE_PROJECT_SLUG}/.claude/settings.json'))"
```

### Step 7: Generate Report

Output structured report:

```
.claude Health Check Report
===========================
Timestamp: {ISO timestamp}

AGENTS ({count} total)
  ✓ agent-name.md - valid
  ✓ agent-name.md - valid (skills: skill1, skill2)
  ✗ agent-name.md - ERROR: references non-existent skill 'missing-skill'

COMMANDS ({count} total)
  ✓ command.md - valid (agent: agent-name)
  ✗ command.md - ERROR: references non-existent agent 'missing-agent'

SKILLS ({count} total)
  ✓ skill-name - valid
  ⚠ skill-name - WARNING: missing uv.lock (pyproject.toml present)
  ✗ skill-name - ERROR: missing skill.md

HOOKS ({count} total)
  ✓ hook-name - valid
  ⚠ hook-name - WARNING: missing uv.lock

EXTERNAL TOOLS
  ✓ uv: {path} ({version})
  ✓ docker: {path} ({version})
  ✗ kubectl: NOT FOUND
  ⚠ aws: {path} (credentials not configured)

CONFIG FILES
  ✓ config.yml: valid YAML
  ✓ settings.json: valid JSON
  ✗ settings.json: ERROR: invalid JSON at line 45

SUMMARY: {errors} errors, {warnings} warnings
Status: {HEALTHY | NEEDS ATTENTION | CRITICAL}
```

## Severity Levels

| Level | Symbol | Meaning |
|-------|--------|---------|
| Error | ✗ | Must fix - broken reference or missing required file |
| Warning | ⚠ | Should fix - incomplete setup or missing optional |
| Pass | ✓ | All checks passed |

## Status Determination

| Errors | Warnings | Status |
|--------|----------|--------|
| 0 | 0 | HEALTHY |
| 0 | 1+ | NEEDS ATTENTION |
| 1+ | any | CRITICAL |

## Example Validation Logic

### Agent Skill Reference Check

```python
import re
import yaml
from pathlib import Path

def check_agent_skills(agent_path: Path, skills_dir: Path) -> list[str]:
    """Check if agent references valid skills."""
    errors = []
    content = agent_path.read_text()

    # Parse frontmatter
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            frontmatter = yaml.safe_load(parts[1])
            description = frontmatter.get("description", "")

    # Find skill references in tables or descriptions
    # Pattern: "Skills Used" row or "skill-name skill"
    skill_names = [d.name for d in skills_dir.iterdir() if d.is_dir()]

    for skill in skill_names:
        if skill in content:
            skill_path = skills_dir / skill / "skill.md"
            if not skill_path.exists():
                skill_path = skills_dir / skill / "SKILL.md"
            if not skill_path.exists():
                errors.append(f"References skill '{skill}' but skill.md not found")

    return errors
```

## Integration

This skill is invoked by:
- `/health` command
- `health-check` agent
- Direct skill invocation
