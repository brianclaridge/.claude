# Rule 040: plans

> Create plans for non-trivial tasks.

## Priority

Workflow (030-049)

## Directive

For ANY non-trivial task, multi-step operation, or complex request, ALWAYS create and save a plan to `{CWD}/plans/` BEFORE starting work.

## Plan Requirements

- Filename: `YYYYMMDD_HHMMSS_plan-topic.md`
- Created BEFORE work begins
- Ask user permission to proceed
- Include TODO list contents

## Triggers

- Any task requiring 3+ steps
- Feature implementations
- Debugging complex issues
- Code refactoring
- Research and analysis tasks

## Post-Implementation

1. Verify all TODOs complete
2. Offer to update plan with execution notes
3. Invoke `git-manager` skill

### NON-NEGOTIABLE

Post-implementation prompts are **MANDATORY WORKFLOW PROMPTS** that cannot be bypassed, even when:

- User says "continue without questions"
- Session resumes from context loss
- User says "just do it" or similar

These prompts enforce process integrity. Only skip if the rule's own skip conditions are met.

## Exceptions

- Single, straightforward tasks
- Rule 010 analysis (session start)

## Source

[rules/040-plans.md](../../rules/040-plans.md)
