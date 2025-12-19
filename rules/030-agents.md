# RULE: 030 agents

**CRITICAL** When reasoning, thinking or planning, always consider using agent use before making a response. Always tell the user why/how you made your decision on agent. Do this for each agent available (list agent -> reason). Include this list in the user response.

## Output Format

Present agent decisions in a concise table or list:

**Agent Analysis:**
- `agent-name` → **Selected/Not applicable** - Brief reason
- `another-agent` → **Not applicable** - Brief reason

## Example

```
**Agent Analysis:**
- `project-analysis` → **Selected** - Task requires codebase exploration
- `Explore` → Defer - project-analysis provides broader context
- `health-check` → Not applicable - Not a setup validation task
- `gitops` → Not applicable - No git operations needed
```

## When to Include

Include this analysis when:
- Starting a new task or session
- The task could benefit from agent delegation
- Multiple agents might be relevant

Skip when:
- Continuing an in-progress task
- Simple follow-up questions
- Agent has already been selected for current workflow
