# .claude

> My opinionated, docker-ized development environment for Claude Code CLI.

## Software Requirements

- [Git](https://git-scm.com/downloads)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [PowerShell 7+](https://github.com/PowerShell/PowerShell) (`pwsh`)
- [Task](https://taskfile.dev/) (Taskfile runner)

## Quick Start

```bash
# clone and ignore
cd /path/to/your/project
git clone https://github.com/brianclaridge/.claude.git

# add .claude/ to your .gitignore
echo ".claude" >> .gitignore

# start claude
cd .claude/
task claude
```

## Slash Commands

| Command | Description |
|---------|-------------|
| `/hello` | Output Hello World message |
| `/analyze` | Project analysis and codebase exploration |
| `/cloud-auth` | Authenticate to cloud providers (AWS, GCP) |
| `/playwright` | Browser automation (screenshots, video, scraping) |
| `/build-agent` | Create a new Claude Code agent |
| `/build-skill` | Create a new Claude Code skill |
| `/gitops` | Git commit workflow with branch/push management |
| `/context` | Gather session context (git status, environment) |
| `/metadata` | Update project metadata registry |
| `/stack-manager` | Recommend and bootstrap application stacks |
| `/taskfile` | Validate Taskfile.yml against best practices |

## Agents

| Agent | Description | Skills Used |
|-------|-------------|-------------|
| hello-world | Simple Hello World output | — |
| project-analysis | Comprehensive codebase analysis | session-context, project-metadata-builder |
| cloud-auth | Cloud provider authentication | aws-login, gcp-login |
| browser-automation | Browser tasks (screenshots, video, scraping) | playwright-automation |
| agent-builder | Create new agents | — |
| skill-builder | Create new skills | — |
| gitops | Git commit workflow | git-manager |
| stack-manager | Recommend and bootstrap app stacks | stack-manager |
| taskfile-manager | Validate Taskfile against Rule 090 | taskfile-manager |

## Skills

| Skill | Description | Trigger |
|-------|-------------|---------|
| git-manager | Interactive git commit workflow | After TODOs complete, "commit changes" |
| playwright-automation | Browser automation scripts | "record video", "screenshot", "scrape" |
| aws-login | AWS SSO authentication | "login to AWS", cloud-auth agent |
| gcp-login | GCP authentication | "login to GCP", cloud-auth agent |
| session-context | Gather session context | project-analysis agent |
| project-metadata-builder | Update project registry | project-analysis agent |
| stack-manager | Recommend and bootstrap stacks | "/stack-manager", "suggest a stack" |
| taskfile-manager | Validate Taskfile best practices | "/taskfile", "validate tasks" |

## [OPTIONAL] Add as submodule

```bash
# optional, add .claude as a submodule
git submodule add -b main https://github.com/brianclaridge/.claude.git
git submodule update --init --recursive --remote
```

### Updating .claude Submodule

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

### Removing .claude Submodule

```bash
git submodule deinit -f .claude
rm -rf .git/modules/.claude
git rm -f .claude
git commit -m "Remove .claude submodule"
```

## Stacks

Available application stacks for bootstrapping via `/stack-manager`:

| Stack | Language | Use Cases |
|-------|----------|-----------|
| htmx-fastapi | Python | Server-rendered apps, dashboards |
| nextjs-prisma | TypeScript | SaaS, e-commerce, content sites |
| django-htmx | Python | Admin panels, rapid prototyping |
| go-templ-htmx | Go | High-performance APIs, microservices |
| sveltekit-supabase | TypeScript | MVPs, real-time apps |
| vue-vite-fastapi | Python/TS | Data apps, dashboards |

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
    │   ├── agent-builder.md
    │   ├── browser-automation.md
    │   ├── cloud-auth.md
    │   ├── gitops.md
    │   ├── hello-world.md
    │   ├── project-analysis.md
    │   ├── skill-builder.md
    │   ├── stack-manager.md
    │   └── taskfile-manager.md
    ├── assets/                     # Static assets (images, etc.)
    ├── commands/                   # Slash commands
    │   ├── analyze.md
    │   ├── build-agent.md
    │   ├── build-skill.md
    │   ├── cloud-auth.md
    │   ├── context.md
    │   ├── gitops.md
    │   ├── hello.md
    │   ├── metadata.md
    │   ├── playwright.md
    │   ├── stack-manager.md
    │   └── taskfile.md
    ├── config/                     # confd templates and conf.d
    ├── docker/                     # Dockerfile, entrypoints, assets
    ├── hooks/                      # Python event handlers
    │   ├── cloud_auth_prompt/      # Cloud authentication prompts
    │   ├── logger/                 # Logs all hook events
    │   ├── playwright_healer/      # Playwright error recovery
    │   ├── rules_loader/           # Reinforces rules on prompts
    │   └── session_context_injector/
    ├── plans/                      # Implementation plans
    ├── prompts/                    # Prompt templates
    ├── rules/                      # Behavioral rules (000-090)
    ├── scripts/                    # PowerShell host utilities
    ├── skills/                     # Model-invoked capabilities
    │   ├── aws-login/              # AWS SSO authentication
    │   ├── gcp-login/              # GCP authentication
    │   ├── git-manager/            # Git commit workflow
    │   ├── playwright-automation/  # Browser automation
    │   ├── project-metadata-builder/
    │   ├── session-context/        # Session context gathering
    │   ├── stack-manager/          # Stack recommendations & bootstrap
    │   └── taskfile-manager/       # Taskfile validation
    ├── config.yml                  # Global feature configuration
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
