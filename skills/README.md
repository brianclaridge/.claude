# Claude Code Skills

Skills are model-invoked capability packages that extend Claude's abilities for specialized tasks. Unlike slash commands (user-invoked), Claude autonomously activates skills when your request matches the skill's description.

## Quick Start

```bash
# Create a skill
mkdir -p /workspace/${CLAUDE_PROJECT_SLUG}/.claude/skills/my-skill
cat > /workspace/${CLAUDE_PROJECT_SLUG}/.claude/skills/my-skill/SKILL.md << 'EOF'
---
name: my-skill
description: What this does AND when Claude should use it
---

# Instructions
Your skill instructions here.
EOF
```

## How Skills Work

### Invocation Flow

```text
User request → Claude matches skill description → tool_use call →
SKILL.md content loads → Claude executes instructions
```

Skills are **model-invoked** - Claude decides when to activate based on matching your request to skill descriptions. Manual triggers:

- "Use the [skill-name] skill for this task"
- "What skills are available?"

### Progressive Disclosure

1. **Startup**: Only metadata (name/description) loads into context
2. **Activation**: Full SKILL.md content expands when skill triggers
3. **As-needed**: Supporting files load only when referenced

This keeps the base prompt lean while allowing unbounded skill complexity.

## SKILL.md Structure

```yaml
---
name: lowercase-with-hyphens      # Required: max 64 chars, [a-z0-9-] only
description: Brief description... # Required: max 1024 chars
allowed-tools: Read, Grep, Glob   # Optional: restrict tool access
---

# Skill Name

## Instructions
Step-by-step guidance for Claude.

## Examples
Concrete usage examples.

## References
- See `reference.md` for API details
- Run `scripts/helper.py` for X
```

### Field Requirements

| Field | Constraint | Notes |
|-------|------------|-------|
| `name` | `[a-z0-9-]`, max 64 chars | Must be unique across all skill sources |
| `description` | max 1024 chars | Include WHAT it does AND WHEN to use it |
| `allowed-tools` | Comma-separated | Optional - restricts available tools |

## Storage Locations

| Location | Path | Scope |
|----------|------|-------|
| Personal | `/workspace/${CLAUDE_PROJECT_SLUG}/.claude/skills/skill-name/SKILL.md` | Your projects only |
| Project | `.claude/skills/skill-name/SKILL.md` | Team via git |
| Plugin | Bundled with installed plugins | Plugin-specific |

### Directory Structure

```text
my-skill/
├── SKILL.md           # Required - core instructions
├── reference.md       # Optional - detailed documentation
├── examples.md        # Optional - usage examples
├── templates/         # Optional - file templates
│   └── component.tsx
└── scripts/           # Optional - executable utilities
    └── helper.py
```

## Writing Effective Descriptions

Activation reliability depends on description quality.

```yaml
# Poor - vague, low activation rate (~50%)
description: Helps with data

# Good - specific triggers, high activation rate (~84%)
description: Analyze Excel spreadsheets, generate pivot tables, create charts. Use when working with .xlsx files or when user asks about data analysis.
```

**Best practices:**

- Include specific file types, operations, or keywords users would mention
- State both capability AND trigger conditions
- Be explicit about when the skill applies

## Tool Restrictions

Use `allowed-tools` to create read-only or limited skills:

```yaml
---
name: code-auditor
description: Security audit for code. Use when reviewing for vulnerabilities.
allowed-tools: Read, Grep, Glob
---
```

Claude cannot use Edit, Write, or Bash when this skill is active.

## Example: Code Review Skill

```yaml
---
name: code-reviewer
description: Review code for bugs, security issues, and best practices. Use when asked to review, audit, or check code quality.
allowed-tools: Read, Grep, Glob
---

# Code Reviewer

## Process
1. Read specified files using the Read tool
2. Analyze for:
   - Security vulnerabilities (OWASP Top 10)
   - Performance anti-patterns
   - Code style violations
3. Provide actionable feedback with line references

## Output Format
### Summary
Brief overview of findings.

### Issues
| Severity | File:Line | Issue | Fix |
|----------|-----------|-------|-----|
| HIGH | auth.py:42 | SQL injection | Use parameterized queries |

### Recommendations
Prioritized list of improvements.
```

## Debugging

```bash
# View skill loading and errors
claude --debug

# Common issues:
# - Skill not activating: Description too vague
# - YAML errors: Check --- markers and indentation (no tabs)
# - Path issues: Use forward slashes (scripts/helper.py)
```

## Skills vs Agents

| Aspect | Skills | Agents |
|--------|--------|--------|
| Location | `/workspace/${CLAUDE_PROJECT_SLUG}/.claude/skills/` | `/workspace/${CLAUDE_PROJECT_SLUG}/.claude/agents/` |
| Invocation | Model-invoked (automatic) | Task tool (explicit) |
| Context | Same conversation | Separate subprocess |
| Output | Progressive file loading | Final report only |
| Use case | Specialized capabilities | Complex delegated tasks |

## Resources

### Official Documentation

- [Claude Code Skills](https://code.claude.com/docs/en/skills)
- [How to Create Custom Skills](https://support.claude.com/en/articles/12512198-how-to-create-custom-skills)
- [Introducing Agent Skills](https://www.anthropic.com/news/skills)

### Engineering Deep-Dives

- [Equipping Agents for the Real World](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills) - Anthropic engineering blog on skill architecture
- [Inside Claude Code Skills](https://mikhail.io/2025/10/claude-code-skills/) - Structure, prompts, and invocation internals
- [How to Make Skills Activate Reliably](https://scottspence.com/posts/how-to-make-claude-code-skills-activate-reliably) - Improving activation rates with hooks
