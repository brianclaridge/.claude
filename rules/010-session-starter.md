# RULE: 010 session-starter

**CRITICAL** Session start triggers that invoke `project-analysis` agent.

## Trigger Patterns

### Generic Start

**Triggers**: "hello", "vibe", "get started", "hi" (first session prompt)
**Action**: Invoke `project-analysis` agent for current directory

### Project Group Start

**Triggers**:

- "let's work on [group]"
- "work on [group]"
- "switch to [group]"
- "load [group]"

Where `[group]` matches a key under `projects:` in `${CLAUDE_PROJECTS_YML_PATH}` (e.g., `camelot`, `gcp-ops`)

**Action**: Invoke `project-analysis` agent with "Analyze project group: [group]"

## Validation

Before invoking with a project group:

1. Read `${CLAUDE_PROJECTS_YML_PATH}`
2. Check if `[group]` exists as a key under `projects:`
3. If not found: Respond with "Project group '[group]' not found. Available: camelot, gcp-ops"
4. Do NOT invoke the agent for unknown groups

## Delegation Rules

1. **Pattern Detection**: Parse user input to identify trigger type
   - If matches project group pattern AND group exists: Pass group name to agent
   - If matches generic start pattern: Invoke agent without group context

2. **Agent Invocation**:
   - Generic: Invoke with "Analyze the current directory"
   - Project group: Invoke with "Analyze project group: [group]"

3. **Output Handling**:
   - Present ONLY the agent's factual project details to the user
   - DO NOT add recommendations, action items, or commentary beyond the agent's factual report
   - If the agent fails, immediately stop and notify the user

## Examples

| User Says | Pattern | Agent Context |
|-----------|---------|---------------|
| "hello" | generic | Analyze the current directory |
| "vibe" | generic | Analyze the current directory |
| "let's work on camelot" | project-group | Analyze project group: camelot |
| "work on gcp-ops" | project-group | Analyze project group: gcp-ops |
| "switch to camelot" | project-group | Analyze project group: camelot |
| "let's work on foobar" | project-group | Error: foobar not found |
