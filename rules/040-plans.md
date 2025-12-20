# RULE: 040 plans

## Quick Reference

| Question | Answer |
|----------|--------|
| When to plan? | Any task with 3+ steps, features, debugging, refactoring |
| Where to save? | `${CLAUDE_PLANS_PATH}` (always) |
| Filename format? | `YYYYMMDD_HHMMSS_plan-topic.md` |
| After completion? | Invoke `git-manager` skill |
| Skip planning? | Session-starter (Rule 010), single-step tasks |

---

**CRITICAL** For ANY non-trivial task, multi-step operation, or complex request, ALWAYS create and save a plan to `${CLAUDE_PLANS_PATH}` BEFORE starting work.

## Plan Location

**ALL plans go to `${CLAUDE_PLANS_PATH}`** regardless of what code is being modified. This provides:
- Single source of truth for all plans
- Consistent commit workflow via the `.claude` submodule
- Simplified plan discovery and management

The `plan_distributor` hook automatically copies plans from Claude Code's internal location to `${CLAUDE_PLANS_PATH}` with proper naming.

## Plan Header Format

Every plan MUST begin with an "Affects" header listing absolute paths:

```markdown
# Plan: <Title>

**Affects:** `<absolute-path-1>`, `<absolute-path-2>`

---
```

Example:
```markdown
# Plan: Add User Authentication

**Affects:** `/workspace/src/auth/`, `/workspace/api/routes/`

---
```

This header enables:
- Quick identification of impacted code areas
- Better plan organization and searchability
- Automated tooling to correlate plans with code changes

## Plan Mode Integration

When ExitPlanMode is invoked:

1. Claude Code saves the plan to its internal location with a random name
2. The `plan_distributor` hook copies it to `${CLAUDE_PLANS_PATH}` with proper naming
3. You should verify the plan was distributed correctly
4. If distribution fails, manually create the plan file

**Filename format**: `YYYYMMDD_HHMMSS_plan-topic.md`
- Use `date '+%Y%m%d_%H%M%S'` to generate timestamp
- topic is kebab-case (e.g., `user-authentication`, `api-refactor`)
- Example: `20250829_151052_vm-restart-on-start.md`

**CRITICAL**: This applies whether or not the user explicitly asks for a plan. The plan should be created BEFORE the work. Once the plan is written, ask the user permission to proceed.

**EXCEPTION:** Do not create a plan when executing Rule 010 (session-starter agent initialization).

## Triggers for Planning

- Any task requiring 3+ steps
- Feature implementations
- Debugging complex issues
- Code refactoring
- System configurations
- Research and analysis tasks
- Any task where a TODO list would be beneficial

## Post-Implementation Workflow

**CRITICAL** After all plan TODOs are marked complete:

1. Verify all tasks show `completed` status
2. Invoke the `git-manager` skill to commit implementation
3. Do NOT proceed to git operations without invoking the skill

### NON-NEGOTIABLE

Post-implementation prompts (plan update, git-manager invocation) are **MANDATORY WORKFLOW PROMPTS** that cannot be bypassed, even when:

- User says "continue without questions"
- Session is being resumed from context loss
- User says "just do it" or similar
- Time pressure is implied

### Skip Conditions

Do NOT invoke git-manager when:

- Working directory is not a git repository
- User explicitly declines ("don't commit", "skip commit")
- Task was read-only analysis or planning only
- No file changes were made during implementation

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
