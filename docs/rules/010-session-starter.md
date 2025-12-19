# Rule 010: session-starter

> Auto-invoke project-analysis agent on session start.

## Priority

Session management (010-019)

## Directive

Session start triggers automatically invoke the `project-analysis` agent.

## Trigger Patterns

| Pattern | Example | Action |
|---------|---------|--------|
| Generic | "hello", "vibe", "hi" | Analyze current directory |
| Project Group | "work on [group]" | Analyze project group |

## Validation

Before invoking with a project group:
1. Read `${CLAUDE_PROJECTS_YML_PATH}`
2. Check if group exists
3. Error if not found

## Examples

| User Says | Agent Context |
|-----------|---------------|
| "hello" | Analyze current directory |
| "let's work on camelot" | Analyze project group: camelot |
| "work on foobar" | Error: foobar not found |

## Source

[rules/010-session-starter.md](../../rules/010-session-starter.md)
