---
name: rule-builder
description: Create new behavioral rules with auto-increment numbering. Use when user says "/build-rule", "create a rule", "new rule for", "add directive".
tools: Read, Write, Glob, Grep, Bash
---

# Rule Builder Skill

Scaffold new behavioral rules following the established 0XX pattern with auto-increment.

## Activation Triggers

- User invokes `/build-rule` command
- User says "create a rule", "new rule for", "add directive"
- User asks "add rule about", "I need a rule for"

## Workflow

### Step 1: Find Next Rule Number

Scan existing rules to determine next number:

```bash
# Find highest existing rule number
ls ${CLAUDE_PATH}/rules/*.md | grep -oP '\d{3}' | sort -n | tail -1
```

Increment by 10:
- If highest is 090, next is 100
- If highest is 100, next is 110

### Step 2: Gather Requirements

Use AskUserQuestion to collect:

1. **Topic**: What behavior does this rule govern?
   - Examples: "git usage", "docker best practices", "API design"

2. **Constraint Type**: What is the primary directive?
   - CRITICAL (must follow)
   - IMPORTANT (should follow)
   - RECOMMENDED (consider following)

3. **Key Constraints**: What must/must not happen?
   - "Always use X"
   - "Never do Y"
   - "Prefer Z over W"

4. **Examples Needed**: Should we include code examples?
   - Yes with correct/incorrect patterns
   - No, just prose

### Step 3: Generate Rule Template

Create rule file at `${CLAUDE_PATH}/rules/{NNN}-{topic}.md`:

```markdown
# RULE: {NNN} {topic}

**{CONSTRAINT_TYPE}** {main constraint summary}

## {Section 1}

{content}

## {Section 2 - if applicable}

{content}

## Example

```yaml
# ✓ CORRECT
{good example}

# ✗ WRONG
{bad example}
```
```

### Step 4: Update README.md

Add rule to README.md rules section if it exists:
- Update the rules comment in Structure section

## Rule Numbering Convention

| Range | Category |
|-------|----------|
| 000-009 | Core directives (meta-rules) |
| 010-019 | Session management |
| 020-029 | Persona and behavior |
| 030-039 | Agent usage |
| 040-049 | Planning and workflow |
| 050-059 | Language-specific (Python, etc.) |
| 060-069 | External tools (context7, etc.) |
| 070-079 | Code quality |
| 080-089 | User interaction |
| 090-099 | Tooling (Taskfile, etc.) |
| 100+ | Extended rules |

## Template Patterns

### CRITICAL Rule

```markdown
# RULE: 100 example-topic

**CRITICAL** Always do X when Y. This is non-negotiable.

## When This Applies

- Condition A
- Condition B

## Required Pattern

```code
# The correct approach
example code
```

## Common Mistakes

```code
# ✗ WRONG - Why this is wrong
bad example
```
```

### IMPORTANT Rule

```markdown
# RULE: 110 example-topic

**IMPORTANT** Prefer X over Y for better outcomes.

## Rationale

Explanation of why this matters.

## Preferred Approach

Description with examples.

## Acceptable Alternatives

When exceptions are allowed.
```

### RECOMMENDED Rule

```markdown
# RULE: 120 example-topic

**RECOMMENDED** Consider using X for improved results.

## Benefits

- Benefit 1
- Benefit 2

## Implementation

How to apply this recommendation.
```

## File Naming Convention

- Format: `{NNN}-{kebab-case-topic}.md`
- Examples:
  - `100-api-design.md`
  - `110-docker-usage.md`
  - `120-logging-standards.md`

## Integration

This skill is invoked by:
- `/build-rule` command
- `rule-builder` agent
- Direct skill invocation
