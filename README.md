# .claude

> A customized development environment for Claude Code CLI providing Docker-based containerized workspace with custom directives, agents, hooks, and skills.

## Quick Start

```bash
cd /path/to/your/project
git submodule add -b main git@github.com:brianclaridge/.claude.git
git submodule update --init --recursive --remote
cd .claude/
task claude
```

## Updating .claude

```pwsh
# run
task claude:fetch

# or 
git submodule update --init --remote --merge .claude

# or
git -C .claude checkout main && git -C .claude pull origin main

# nuclear reset
git -C .claude fetch origin
git -C .claude reset --hard origin/main
git -C .claude clean -fd
```

## Removing .claude

```bash
git submodule deinit -f .claude
rm -rf .git/modules/.claude
git rm -f .claude
git commit -m "Remove .claude submodule"
```

## Structure

```text
/workspace
├── README.md
├── Taskfile.yml
└── .claude/              # Git submodule
    ├── settings.json
    ├── docker-compose.yml
    ├── directives/       # Behavioral rules (000-080)
    ├── agents/           # Specialized analysis agents
    ├── skills/           # Model-invoked capabilities (git-manager)
    ├── hooks/            # Python event handlers (directive_loader, logger)
    ├── docker/           # Container build files
    ├── config/           # confd templates
    └── aws/              # AWS SSO utilities
```

## Technologies

- Container: Ubuntu 24.04, Docker-in-Docker
- Languages: Python (uv), Node.js 24, Go 1.25.4, Rust 1.91.1, JDK 21, PowerShell 7.5.4
- Model: Claude Opus 4.5 with extended thinking (29999 tokens)
- Automation: Task (Taskfile), confd
- Integration: Context7 MCP, AWS SSO, Git
