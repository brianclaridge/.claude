# .claude

> My opinionated, docker-ized development environment for Claude Code CLI.

## Quick Start

```bash
# clone and ignore
cd /path/to/your/project
git clone git@github.com:brianclaridge/.claude.git

# add .claude/ to your .gitignore
echo ".claude" >> .gitignore

# start claude
cd .claude/
task claude

# optional, add .claude as a submodule
git submodule add -b main git@github.com:brianclaridge/.claude.git
git submodule update --init --recursive --remote
```

## Updating .claude Submodule

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

## Removing .claude Submodule

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
└── .claude/                        # Git submodule
    ├── .data/                      # Runtime data (gitignored)
    │   ├── logs/                   # Hook and service logs
    │   └── playwright/             # Screenshots, videos, traces
    ├── .vscode/                    # VS Code workspace settings
    ├── agents/                     # Specialized sub-agents
    ├── aws/                        # AWS SSO utilities
    ├── config/                     # confd templates and conf.d
    ├── directives/                 # Behavioral rules (000-080)
    ├── docker/                     # Dockerfile, entrypoints, assets
    ├── hooks/                      # Python event handlers
    │   ├── directive_loader/       # Injects directives into sessions
    │   └── logger/                 # Logs all hook events
    ├── includes/                   # Shared Taskfile includes
    ├── prompts/                    # Prompt templates
    ├── scripts/                    # PowerShell host utilities
    ├── skills/                     # Model-invoked capabilities
    │   ├── git-manager/            # Git commit workflow
    │   └── playwright-automation/  # Browser automation
    ├── settings.json               # Claude Code settings
    ├── docker-compose.yml          # Container configuration
    └── Taskfile.yml                # Task runner commands
```

## Technologies

- Container: Ubuntu 24.04, Docker-in-Docker, NVIDIA Container Toolkit
- Languages: Python 3 (uv, Black), Node.js 24, Go 1.25.4, Rust 1.91.1, JDK 21/Maven, PowerShell 7.5.4
- Cloud: AWS CLI v2/SAM/CDK, Google Cloud CLI/SQL Proxy, Pulumi, OpenTofu
- Kubernetes: kubectl 1.34.2, minikube, Helm
- Browser: Playwright, Chrome/Chromium, Headless Shell
- Security: Vault (Hashicorp)
- Config: Ansible, confd 0.16.0
- AI: Claude Code CLI, Google MCP GenMedia (Imagen, Veo, Chirp3, Lyria)
- Automation: Task (Taskfile), oh-my-posh
- Integration: Context7 MCP, Playwright MCP
