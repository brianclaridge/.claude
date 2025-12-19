# Skills

Model-invoked capabilities that Claude activates when trigger conditions match.

## Overview

Skills are implementations in `skills/*/` that Claude invokes automatically based on:
- Conversation triggers ("commit changes", "login to AWS")
- Workflow states (all TODOs complete)
- Explicit slash commands

Unlike agents (which are sub-processes), skills are workflow definitions that Claude executes directly.

## Available Skills

| Skill | Trigger | Description |
|-------|---------|-------------|
| [git-manager](git-manager.md) | TODOs complete, "commit" | Interactive git commit workflow |
| [aws-login](aws-login.md) | "login to AWS", cloud-auth | AWS SSO authentication |
| [gcp-login](gcp-login.md) | "login to GCP", cloud-auth | GCP authentication |
| [playwright-automation](playwright-automation.md) | "screenshot", "video" | Browser automation |
| [session-context](session-context.md) | Session start | Gather session context |
| [project-metadata-builder](project-metadata-builder.md) | Analysis complete | Update project registry |
| [stack-manager](stack-manager.md) | "/stack-manager" | Stack recommendations |
| [taskfile-manager](taskfile-manager.md) | "/taskfile" | Taskfile validation |
| [gomplate-manager](gomplate-manager.md) | "/gomplate" | Template validation |
| [health-check](health-check.md) | "/health" | Environment validation |
| [rule-builder](rule-builder.md) | "/build-rule" | Create new rules |

## Skill Categories

### Git Workflow
- **git-manager** - Commit workflow with branch selection, message generation, push confirmation

### Cloud Authentication
- **aws-login** - AWS SSO device authorization flow
- **gcp-login** - GCP Application Default Credentials

### Browser Automation
- **playwright-automation** - Screenshots, video recording, web scraping

### Session Management
- **session-context** - Git status, recent changes, environment info
- **project-metadata-builder** - Project registry updates

### Validation
- **taskfile-manager** - Taskfile.yml best practices
- **gomplate-manager** - gomplate template validation
- **health-check** - Environment integrity checks

### Extensibility
- **stack-manager** - Bootstrap application stacks
- **rule-builder** - Scaffold new behavioral rules

## Skill Structure

Each skill has:

```
skills/my-skill/
├── README.md           # Skill definition, triggers, workflow
├── lib/                # Python implementation (optional)
│   ├── __init__.py
│   └── main.py
└── scripts/            # Helper scripts (optional)
```

## Activation Flow

```
1. User message or state change
2. Claude evaluates triggers in skill README
3. If match: Claude executes skill workflow
4. Skill may use tools (Bash, Read, Write, etc.)
5. Skill completes or invokes another skill
```

## Creating New Skills

See [Development Guide](../DEVELOPMENT.md#creating-skills).

## See Also

- [Agents](../agents/README.md) - Specialized sub-agents
- [Rules](../rules/README.md) - Behavioral directives
- [Development](../DEVELOPMENT.md) - Extension guide
