# Plan: Update DIRECTIVE 040 for Submodule Plan Handling

## Summary

Update DIRECTIVE 040 (plans) to specify that when working on features/bugs in the `.claude/` submodule, plans should be stored in `.claude/plans/` and committed to the `.claude` repo (not left as untracked files in the main project).

## File to Modify

| File | Changes |
|------|---------|
| `${CLAUDE_PATH}/directives/040-plans.md` | Add submodule-specific plan handling section |

## TODO List

- [x] Add new section to DIRECTIVE 040 for submodule plan handling
- [x] Specify `.claude/plans/` as target directory when working on `.claude/` submodule
- [x] Require plans to be committed and pushed to `.claude` repo
- [x] Test directive by verifying current plan gets committed

---

## Changes to DIRECTIVE 040

Add new section after the `{CWD}` explanation:

```markdown
**SUBMODULE EXCEPTION:** When working on features, bugs, or improvements within the `.claude/` submodule itself:

1. Plans go to `.claude/plans/` (within the submodule), NOT `{CWD}/plans/`
2. Plans MUST be committed and pushed to the `.claude` repo
3. This ensures plan history is preserved with the submodule's version control

Detection: If the primary files being modified are within `.claude/` (agents, skills, hooks, directives, etc.), use `.claude/plans/` as the target directory.
```

## Rationale

- The `.claude/` directory is a separate git submodule with its own version history
- Plans for submodule work should be tracked alongside the code changes
- Prevents plans from accumulating as untracked files in the main project
- Maintains complete development history within the submodule
