# RULE: 080 ask-user-questions

**CRITICAL** Always use the AskUserQuestion tool for ANY clarification or confirmation. Never print questions as plain text.

## Mandatory Tool Usage

When you need to:

- Ask for clarification
- Confirm an action
- Present options for user selection
- Get user input before proceeding
- Make decisions on implementation choices

**ALWAYS** use the AskUserQuestion tool with selectable options that the user can navigate with arrow keys/tab.

## Correct Pattern

Use AskUserQuestion tool with structured options:

```json
{
  "questions": [{
    "question": "Which authentication method should I implement?",
    "header": "Auth",
    "options": [
      {"label": "OAuth2 with Google", "description": "Social login via Google"},
      {"label": "OAuth2 with GitHub", "description": "Social login via GitHub"},
      {"label": "JWT tokens only", "description": "Custom token-based auth"}
    ],
    "multiSelect": false
  }]
}
```

User navigates with arrow keys and selects with Enter.

## Incorrect Pattern

**NEVER** print questions as plain text:

```text
Which authentication method would you like me to implement?
1. OAuth2 with Google
2. OAuth2 with GitHub
3. JWT tokens only

Please let me know your preference.
```

This forces the user to type a response instead of selecting from an interactive menu.

## Why This Matters

1. **Consistency**: Interactive menus provide uniform UX
2. **Efficiency**: Arrow key selection faster than typing
3. **Clarity**: Discrete options prevent ambiguous responses
4. **Accessibility**: Menu navigation is more accessible

## Exceptions

Plain text questions are acceptable ONLY when:

- Asking for free-form text input (names, descriptions, custom values)
- The response cannot be constrained to predefined options
- Following up on a previous AskUserQuestion response with "Other" selected
- Asking for file paths or code snippets

## Multi-Step Confirmations

For complex workflows requiring multiple decisions:

```json
{
  "questions": [
    {
      "question": "Select deployment environment",
      "header": "Environment",
      "options": [
        {"label": "Development", "description": "Local testing"},
        {"label": "Staging", "description": "Pre-production"},
        {"label": "Production", "description": "Live environment"}
      ],
      "multiSelect": false
    }
  ]
}
```

If Production selected, follow up with another AskUserQuestion for confirmation.

## Integration with Skills

All skills requiring user input MUST use AskUserQuestion for:

- Branch selection (git-committer)
- Commit message confirmation
- Push confirmation
- Yes/no decisions
- Configuration choices

## Multi-Select Usage

Use `multiSelect: true` when user can choose multiple options:

```json
{
  "question": "Which features should I implement?",
  "header": "Features",
  "options": [
    {"label": "User auth", "description": "Login/logout"},
    {"label": "API endpoints", "description": "REST API"},
    {"label": "Database models", "description": "Data layer"}
  ],
  "multiSelect": true
}
```
