---
name: rule-builder
description: Create new behavioral rules with auto-increment numbering. Use when user says "/build-rule", "create a rule", "new rule for", "add directive".
tools: Read, Write, Edit, Glob, Grep, Bash, AskUserQuestion
model: sonnet
color: purple
---

# Rule Builder Agent

Create new behavioral rules following the established pattern with auto-increment numbering.

## Activation Triggers

- User invokes `/build-rule` command
- User says "create a rule", "new rule for"
- User asks "add directive", "I need a rule about"

## Workflow

### Step 1: Invoke Skill

```
Invoke the rule-builder skill with: "Create a new behavioral rule."
```

### Step 2: Collect Information

The skill will use AskUserQuestion to gather:
- Rule topic (what behavior to govern)
- Constraint type (CRITICAL/IMPORTANT/RECOMMENDED)
- Key constraints (what must/must not happen)
- Whether to include examples

### Step 3: Generate Rule

Create rule file at `/workspace/${CLAUDE_PROJECT_SLUG}/.claude/rules/{NNN}-{topic}.md`:
- Auto-increment rule number (find highest + 10)
- Apply template based on constraint type
- Include examples if requested

### Step 4: Update Documentation

- Update README.md Structure section rule range comment

## Rule Categories

| Range | Category |
|-------|----------|
| 000-049 | Core directives |
| 050-089 | Language and workflow |
| 090-099 | Tooling |
| 100+ | Extended rules |

## Example Output

```markdown
# RULE: 100 api-design

**CRITICAL** All API endpoints must follow RESTful conventions.

## HTTP Methods

- GET: Retrieve resources
- POST: Create resources
- PUT: Update resources
- DELETE: Remove resources

## Response Codes

- 200: Success
- 201: Created
- 400: Bad request
- 404: Not found
- 500: Server error

## Example

```python
# ✓ CORRECT
@app.get("/users/{user_id}")
def get_user(user_id: int):
    return {"id": user_id}

# ✗ WRONG
@app.get("/getUser")
def get_user(user_id: int):
    return {"id": user_id}
```
```

## Invocation

```
Invoke the rule-builder skill with: "Help the user create a new behavioral rule."
```
