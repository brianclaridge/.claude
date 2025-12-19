# RULE: 040 plans

## Quick Reference

| Question | Answer |
|----------|--------|
| When to plan? | Any task with 3+ steps, features, debugging, refactoring |
| Where to save? | `{CWD}/plans/` (or `.claude/plans/` if editing submodule) |
| Filename format? | `YYYYMMDD_HHMMSS_plan-topic.md` |
| After completion? | Invoke `git-manager` skill |
| Skip planning? | Session-starter (Rule 010), single-step tasks |

---

**CRITICAL** For ANY non-trivial task, multi-step operation, or complex request, ALWAYS create and save a plan to `{CWD}/plans/` BEFORE starting work.

**IMPORTANT:** `{CWD}` refers to Claude Code's current working directory (the directory where the session was started), NOT the directory of the project being edited.

**SUBMODULE EXCEPTION:** When working on features, bugs, or improvements within the `.claude/` submodule itself:

For example, if Claude Code was started in `/workspace` but you are editing files in `${CLAUDE_PATH}/**`, plans go in `${CLAUDE_PATH}/plans/`.

1. Plans go to `.claude/plans/` (within the submodule), NOT `{CWD}/plans/`
2. Plans MUST be committed and pushed to the `.claude` repo
3. This ensures plan history is preserved with the submodule's version control

Detection: If the primary files being modified are within `.claude/` (agents, skills, hooks, directives, etc.), use `.claude/plans/` as the target directory.

**CRITICAL**: This applies whether or not the user explicitly asks for a plan. The plan should be created BEFORE the work. Once the plan is written, ask the user permission to proceed. The plan should include the contents of your TODO list. Ensure the user knows you're doing this.

**PLAN MODE INTEGRATION:** When ExitPlanMode is invoked during plan mode:

1. IMMEDIATELY after ExitPlanMode approval, create the physical plan file in `{CWD}/plans/`
2. Use the same plan content that was presented via ExitPlanMode
3. Inform the user that the plan has been saved to the file
4. Then proceed with implementation
5. The plan file MUST be created even if ExitPlanMode was used

**EXCEPTION:** Do not create a plan when executing DIRECTIVE 010 (session-starter agent initialization), as this is an analysis task that doesn't require planning.

Triggers for automatic planning include:

- Any task requiring 3+ steps
- Feature implementations
- Debugging complex issues
- Code refactoring
- System configurations
- Research and analysis tasks
- Any task where a TODO list would be beneficial

The filename format MUST be: YYYYMMDD_HHMMSS_plan-topic.md where:

- Create the plan BEFORE executing the plan (or immediately after ExitPlanMode approval)
- Ask the user for permission to proceed with the plan
- `{CWD}/plans/` is the directory for all plans (see note above about CWD)
- ALWAYS use the Linux `date` command to generate the timestamp: `date '+%Y%m%d_%H%M%S'`
- YYYYMMDD is the date (e.g., 20250829)
- HHMMSS is the time in 24-hour format (e.g., 151052)
- plan-topic is a kebab-case description (e.g., vm-restart-on-start)
- Example: 20250829_151052_vm-restart-on-start.md
- DO NOT include square brackets [] in the actual filename

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

These prompts are distinct from **clarifying questions** (which gather missing information). Workflow prompts enforce process integrity and user control over commits.

**If in doubt:** A prompt required by a rule is mandatory. Only skip if the rule's own skip conditions are met.

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
