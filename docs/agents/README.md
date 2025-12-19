# Agents

Specialized sub-agents invoked via the Task tool for complex, multi-step tasks.

## Overview

Agents are markdown files in `agents/` that define specialized Claude instances with focused capabilities. They're invoked when:
- User explicitly requests via slash command
- Claude determines the task matches an agent's specialty
- Rule 030 requires agent consideration

## Available Agents

| Agent | Slash Command | Description |
|-------|---------------|-------------|
| [hello-world](hello-world.md) | `/hello` | Simple Hello World output |
| [project-analysis](project-analysis.md) | `/analyze` | Comprehensive codebase analysis |
| [cloud-auth](cloud-auth.md) | `/cloud-auth` | Cloud provider authentication |
| [browser-automation](browser-automation.md) | `/playwright` | Browser tasks (screenshots, video) |
| [gitops](gitops.md) | `/gitops` | Git commit workflow |
| [stack-manager](stack-manager.md) | `/stack-manager` | Stack recommendations |
| [taskfile-manager](taskfile-manager.md) | `/taskfile` | Taskfile validation |
| [gomplate-manager](gomplate-manager.md) | `/gomplate` | Template validation |
| [health-check](health-check.md) | `/health` | Environment validation |
| [skill-builder](skill-builder.md) | `/build-skill` | Create new skills |
| [agent-builder](agent-builder.md) | `/build-agent` | Create new agents |
| [rule-builder](rule-builder.md) | `/build-rule` | Create new rules |

## Agent Categories

### Session Management
- **project-analysis** - Automatically invoked on session start (Rule 010)
- **health-check** - Environment integrity validation

### Development Workflow
- **gitops** - Git commit with branch management
- **stack-manager** - Application stack bootstrapping

### Cloud & Infrastructure
- **cloud-auth** - AWS SSO and GCP authentication
- **browser-automation** - Playwright browser control

### Validation
- **taskfile-manager** - Taskfile.yml best practices (Rule 090)
- **gomplate-manager** - Template validation (Rule 095)

### Extensibility
- **agent-builder** - Create new agents
- **skill-builder** - Create new skills
- **rule-builder** - Create new rules

## Invocation

### Via Slash Command

```
User: /analyze
Claude: [Invokes project-analysis agent]
```

### Via Task Tool

```
Claude uses Task tool with:
- subagent_type: "project-analysis"
- prompt: "Analyze the current directory"
```

### Via Rule 030

Claude considers agents on every request:
```
Agent Decision Matrix:
| Agent | Reason | Decision |
|-------|--------|----------|
| project-analysis | Not analyzing codebase | Skip |
| gitops | Implementation complete | Use |
```

## Creating New Agents

See [Development Guide](../DEVELOPMENT.md#creating-agents).

## See Also

- [Skills](../skills/README.md) - Model-invoked capabilities
- [Rules](../rules/README.md) - Behavioral directives
- [Development](../DEVELOPMENT.md) - Extension guide
