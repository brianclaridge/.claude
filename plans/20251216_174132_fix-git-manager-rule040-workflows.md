# Plan: Fix git-manager and Rule 040 Plan Workflows

## Issue 1: git-manager "Commit & Plan" Mode

### Problem

After selecting "Commit & Plan" mode, I incorrectly asked a follow-up question. The user expected a silent handoff to plan mode.

### Fix

Update `skills/git-manager/SKILL.md` "Commit & Plan Mode" section (lines 181-194):

**Add step 9 and clarifying note:**
```markdown
8. Invoke `EnterPlanMode` immediately
9. **STOP** - Do NOT ask follow-up questions. Wait silently for user input.

This is the recommended workflow for iterative development - commit your work and immediately enter plan mode. The user will provide the next task when ready.

**CRITICAL**: Unlike Auto and Interactive modes, Commit & Plan does NOT proceed to Step 7 (What's next?). The workflow ends after invoking EnterPlanMode.
```

---

## Issue 2: Rule 040 Plan File Lifecycle

### Problem

1. Plans aren't consistently copied to `{CWD}/plans/` after ExitPlanMode approval
2. No provision for updating plans if implementation deviates from original plan

### Fix

Update `rules/040-plans.md` to add "Post-Execution Plan Update" section:

**Add after "Post-Implementation Workflow" section:**
```markdown
## Post-Execution Plan Update

Before invoking git-manager, offer to update the plan file if any of these occurred:

- Scope changed during implementation
- Unexpected issues discovered
- Approach modified from original plan
- User provided mid-execution feedback

### Update Format

Append an "Execution Notes" section to the plan file:

```markdown
---

## Execution Notes

**Deviations from original plan:**
- {bullet points of changes}

**Issues discovered:**
- {any problems encountered}

**Additional work completed:**
- {unplanned items that were done}
```

### Update Trigger

Use AskUserQuestion before git-manager:

```json
{
  "question": "The plan may have changed during execution. Update the plan file?",
  "header": "Plan Update",
  "options": [
    {"label": "Yes, append notes", "description": "Add execution notes to plan file"},
    {"label": "No, keep original", "description": "Plan file remains unchanged"}
  ],
  "multiSelect": false
}
```

**Skip this prompt if:**
- No deviations from plan occurred
- Plan was trivial (single-file change)
- User selected "Commit & Plan" mode (silent workflow)
```

---

## Issue 3: Duplicate "Discovering organization hierarchy..." Log

### Problem

During `aws-auth --rebuild`, the message appears twice:
```
Discovering organization hierarchy...
Discovering organization hierarchy...
```

### Likely Cause

Both files log this message:
- `skills/aws-login/lib/discovery.py` - `discover_organization()` function
- `lib/aws_inspector/aws_inspector/services/organizations.py` - `discover_organization()` function

### Fix

Remove the log from `skills/aws-login/lib/discovery.py` since it's just a thin wrapper. The aws_inspector library should own the logging.

---

## Files to Modify

| File | Change |
|------|--------|
| `.claude/skills/git-manager/SKILL.md` | Add step 9 and clarifying note to Commit & Plan Mode section |
| `.claude/rules/040-plans.md` | Add "Post-Execution Plan Update" section with execution notes format |
| `.claude/skills/aws-login/lib/discovery.py` | Remove duplicate "Discovering organization hierarchy..." log |
