# Rule 080: ask-user-questions

> Use AskUserQuestion tool for clarification.

## Priority

Domain-specific (050-099)

## Directive

ALWAYS use the AskUserQuestion tool for ANY clarification or confirmation. Never print questions as plain text.

## When to Use

- Asking for clarification
- Confirming an action
- Presenting options
- Getting input before proceeding
- Making implementation choices

## Correct Pattern

```json
{
  "questions": [{
    "question": "Which authentication method?",
    "header": "Auth",
    "options": [
      {"label": "OAuth2", "description": "Social login"},
      {"label": "JWT", "description": "Token-based"}
    ],
    "multiSelect": false
  }]
}
```

## Incorrect Pattern

```text
Which authentication method would you like?
1. OAuth2
2. JWT
Please let me know...
```

## Prompt Categories

### Clarifying Questions

Gather missing information. **Can be skipped** when user provides context or defers.

### Mandatory Workflow Prompts

Required by rules (e.g., Rule 040 plan updates, git confirmations). **Cannot be skipped** even when user says "continue without questions" or session resumes.

## Exceptions

- Free-form text input (names, descriptions)
- File paths or code snippets
- Following up on "Other" selection

## Source

[rules/080-ask-user-questions.md](../../rules/080-ask-user-questions.md)
