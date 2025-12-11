# DIRECTIVE: 040 plans

**CRITICAL** For ANY non-trivial task, multi-step operation, or complex request, ALWAYS create and save a plan to `{CWD}/plans/` BEFORE starting work.

**IMPORTANT:** `{CWD}` refers to Claude Code's current working directory (the directory where the session was started), NOT the directory of the project being edited. For example, if Claude Code was started in `/workspace/projects/` but you are editing files in `/workspace/.claude/hooks/logger/`, plans go in `/workspace/projects/plans/`.

This applies whether or not the user explicitly asks for a plan. The plan should be created BEFORE the work. Once the plan is written, ask the user permission to proceed. The plan should include the contents of your TODO list. Ensure the user knows you're doing this.

**PLAN MODE INTEGRATION:** When ExitPlanMode is invoked during plan mode:

1. IMMEDIATELY after ExitPlanMode approval, create the physical plan file in `{CWD}/plans/`
2. Use the same plan content that was presented via ExitPlanMode
3. Inform the user that the plan has been saved to the file
4. Then proceed with implementation
5. The plan file MUST be created even if ExitPlanMode was used

**EXCEPTION:** Do not create a plan when executing DIRECTIVE 010 (project-manager agent initialization), as this is an analysis task that doesn't require planning.

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

### Skip Conditions

Do NOT invoke git-manager when:

- Working directory is not a git repository
- User explicitly declines ("don't commit", "skip commit")
- Task was read-only analysis or planning only
- No file changes were made during implementation
