# Architecture

## Overview

The `.claude` environment is a Docker-ized development environment for Claude Code CLI. It provides:

- **Agents**: Specialized sub-agents for complex tasks
- **Skills**: Model-invoked capabilities and automation
- **Rules**: Behavioral directives that govern all operations
- **Hooks**: Event handlers for Claude Code lifecycle events
- **Stacks**: Application templates for bootstrapping projects

## Directory Structure

```text
/workspace
├── README.md               # Parent project README
├── CLAUDE.md               # Claude Code workflow guide
├── Taskfile.yml            # Task definitions
├── plans/                  # Implementation plans (created by Rule 040)
└── .claude/                # Development environment (submodule)
    ├── README.md           # Environment overview
    ├── CLAUDE.md           # Submodule workflow guide
    ├── config.yml          # Global configuration
    ├── settings.json       # Claude Code settings
    ├── .env                # Environment variables (gitignored)
    ├── .data/              # Runtime data (gitignored)
    │   ├── logs/           # Hook and service logs
    │   ├── aws/            # AWS auth cache
    │   └── playwright/     # Browser artifacts
    ├── agents/             # Agent definitions (*.md)
    ├── commands/           # Slash command definitions (*.md)
    ├── config/             # gomplate templates
    ├── docker/             # Docker build context
    ├── docs/               # Documentation
    ├── hooks/              # Python event handlers
    ├── lib/                # Shared Python libraries
    ├── plans/              # Submodule plans (not parent)
    ├── prompts/            # Prompt templates
    ├── rules/              # Behavioral rules (000-095)
    ├── skills/             # Skill implementations
    └── stacks/             # Application stack templates
```

## Component Relationships

```
┌─────────────────────────────────────────────────────────────┐
│                      Claude Code CLI                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐  │
│  │  Rules  │───▶│ Agents  │───▶│ Skills  │───▶│  Hooks  │  │
│  └─────────┘    └─────────┘    └─────────┘    └─────────┘  │
│       │              │              │              │        │
│       ▼              ▼              ▼              ▼        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                    config.yml                         │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Rules (Behavioral Directives)

Located in `rules/`, numbered 000-095. Loaded at session start by Claude Code. Define:
- How Claude should behave
- What patterns to follow
- Required workflows

See [Rules Documentation](rules/README.md).

### Agents (Specialized Sub-Agents)

Located in `agents/*.md`. Markdown files describing specialized agents invoked via the Task tool. Examples:
- `project-analysis` - Codebase exploration
- `browser-automation` - Playwright operations
- `gitops` - Git commit workflow

See [Agents Documentation](agents/README.md).

### Skills (Model-Invoked Capabilities)

Located in `skills/*/`. Each skill has a README.md defining triggers and workflow. Invoked by Claude when conditions match. Examples:
- `git-manager` - Commit workflow after TODOs complete
- `aws-login` - AWS SSO authentication
- `playwright-automation` - Browser scripts

See [Skills Documentation](skills/README.md).

### Hooks (Event Handlers)

Located in `hooks/*/`. Python scripts executed on Claude Code events:
- `Stop` - After Claude completes a turn
- `UserPromptSubmit` - Before user message is sent
- `SessionStart` - When session begins/resumes

Hooks inject context, log events, or modify behavior.

### Slash Commands

Located in `commands/*.md`. Shortcut triggers that map to agents/skills. User says `/hello` → invokes hello-world agent.

## Data Flow

### Session Start

```
1. User: task claude (starts container)
2. Hook: SessionStart → session_context_injector
3. Agent: project-analysis → analyzes codebase
4. Skill: project-metadata-builder → updates registry
5. Claude: Presents analysis to user
```

### Implementation Flow

```
1. User: Requests feature/fix
2. Rule 040: Claude creates plan in plans/
3. Claude: Asks for approval
4. User: Approves
5. Claude: Implements (tracks via TodoWrite)
6. Rule 040: Invokes git-manager skill
7. Skill: Commits changes
8. Claude: Enters plan mode for next task
```

## Configuration

### config.yml

Global settings for:
- Cloud provider configuration
- Hook settings
- Session behavior
- Logging configuration

### settings.json

Claude Code settings:
- Model preferences
- Tool permissions
- MCP server configuration

### .env

Environment-specific secrets (gitignored):
- AWS SSO credentials
- Git identity
- API keys

## Technologies

| Category | Technologies |
|----------|-------------|
| Container | Ubuntu 24.04, Docker-in-Docker, NVIDIA Toolkit |
| Languages | Python 3 (uv), Node.js 24, Go 1.25, Rust 1.91, JDK 21 |
| Cloud | AWS CLI v2, GCP CLI, Pulumi, OpenTofu |
| Kubernetes | kubectl, minikube, Helm |
| Browser | Playwright, Chrome, Headless Shell |
| Config | Ansible, gomplate |
| MCP | Context7, Playwright |

## See Also

- [Setup Guide](SETUP.md) - Installation and configuration
- [Development](DEVELOPMENT.md) - Extending the environment
