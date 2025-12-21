# .claude

> Opinionated, Docker-ized development environment for Claude Code CLI.

## Quick Start

```bash
cd /path/to/your/project
git clone https://github.com/brianclaridge/.claude.git
echo ".claude" >> .gitignore
cd .claude/
task claude
```

Or as submodule:

```bash
git submodule add -b main https://github.com/brianclaridge/.claude.git
git submodule update --init --recursive --remote
```

## Prerequisites

### Required Software

| Software | Description | Installation |
|----------|-------------|--------------|
| [Git](https://git-scm.com/downloads) | Version control | System package manager |
| [Docker Desktop](https://www.docker.com/products/docker-desktop/) | Container runtime | Download from Docker |
| [PowerShell 7+](https://github.com/PowerShell/PowerShell) | Cross-platform shell | `pwsh` command |
| [Task](https://taskfile.dev/) | Taskfile runner | `brew install go-task` or equivalent |

### Optional Software

| Software | Description | Installation |
|----------|-------------|--------------|
| [GitHub CLI](https://cli.github.com/) | GitHub operations | `gh` command |
| [GitLab CLI](https://gitlab.com/gitlab-org/cli) | GitLab operations | `glab` command |

## Docker Desktop Configuration

> **CRITICAL**: Docker Desktop must allow access to these paths for bind mounts.

Open Docker Desktop → Settings → Resources → File Sharing, and add:

```yaml
volumes:
  # Docker socket for DinD
  - ${DOCKER_SOCK_PATH}:/var/run/docker.sock
  - /sys/fs/cgroup:/sys/fs/cgroup:ro

  # SSH keys (read-only)
  - ${HOME_SSH_PATH}:/ssh:ro

  # Root directory and workspace
  - ${CLAUDE_ROOT_PATH}:/root
  - ${CLAUDE_PARENT_DIR}:/workspace/:delegated
```

## Installation

### Option 1: Clone and Ignore

```bash
cd /path/to/your/project
git clone https://github.com/brianclaridge/.claude.git
echo ".claude" >> .gitignore
```

### Option 2: Add as Submodule

```bash
git submodule add -b main https://github.com/brianclaridge/.claude.git
git submodule update --init --recursive --remote
```

## Starting the Environment

```bash
cd .claude/
task claude
```

This starts the Docker container and opens Claude Code CLI.

## Environment Variables

Create a `.env` file in `.claude/` with:

```bash
# AWS SSO Configuration
AWS_SSO_START_URL="https://your-org.awsapps.com/start"
AWS_SSO_REGION="us-west-2"
AWS_DEFAULT_REGION="us-east-1"
AWS_SSO_ROLE_NAME="AdministratorAccess"

# Git Identity (optional - auto-detected from SSH)
GIT_USER_NAME="Your Name"
GIT_USER_EMAIL="your.email@example.com"
```

## Workflow

```text
1. Session Start → project-analysis agent runs
2. User Request  → Create plan in plans/, ask approval
3. Implementation → Track with TodoWrite, use Context7
4. Completion    → git-manager commits, enter plan mode
```

**Key Patterns:**

- Plans in `plans/` before implementation
- Use AskUserQuestion tool for clarification
- Use Context7 MCP for library docs
- Python: `uv run` syntax
- Consider agents for every request

## Slash Commands

| Command | Description |
|---------|-------------|
| `/analyze` | Comprehensive codebase analysis |
| `/auth-aws` | AWS SSO authentication |
| `/auth-gcp` | GCP authentication |
| `/build-agent` | Create new agent definitions |
| `/build-rule` | Create behavioral rules |
| `/build-skill` | Create skill implementations |
| `/context` | Session context gathering |
| `/gitops` | Interactive git commit workflow |
| `/gomplate` | Validate gomplate templates |
| `/health` | Environment integrity check |
| `/hello` | Test output |
| `/metadata` | Build project metadata registry |
| `/playwright` | Browser automation scripts |
| `/stack-manager` | Bootstrap application stacks |
| `/taskfile` | Validate Taskfile.yml |

## Core Systems

### Agents

Autonomous task handlers that Claude can delegate to. Located in `agents/`.

| Agent | Purpose |
|-------|---------|
| `project-analysis` | Session startup codebase exploration |
| `Explore` | Quick file/code searching |
| `Plan` | Implementation design and planning |
| `gitops` | Git workflow management |
| `browser-automation` | Playwright browser tasks |
| `agent-builder` | Create new agents |
| `skill-builder` | Create new skills |
| `rule-builder` | Create behavioral rules |
| `stack-manager` | Application stack bootstrapping |
| `health-check` | Environment validation |
| `taskfile-manager` | Taskfile best practices |
| `gomplate-manager` | Template validation |

### Rules

Behavioral directives that enforce patterns. Located in `rules/`.

| Rule | Purpose |
|------|---------|
| `000-rule-follower` | Core directive enforcement |
| `010-session-starter` | Project analysis triggers |
| `020-persona` | Response persona (Spock) |
| `030-agents` | Agent consideration pattern |
| `040-plans` | Planning before implementation |
| `050-python` | Python standards (uv, logging) |
| `060-context7` | Library documentation lookup |
| `070-backward-compat` | No backward compatibility by default |
| `080-ask-user-questions` | Interactive UX tool usage |
| `090-taskfile-usage` | Taskfile best practices |
| `095-gomplate-usage` | Gomplate template standards |

### Skills

Python implementations invoked by agents. See `skills/README.md` for details.

| Skill | Purpose |
|-------|---------|
| `aws-login` | AWS SSO authentication flow |
| `gcp-login` | GCP ADC authentication |
| `git-manager` | Commit workflow orchestration |
| `session-context` | Session context gathering |
| `project-metadata-builder` | Project registry updates |
| `playwright-automation` | Browser automation scripts |
| `gomplate-manager` | Template validation |
| `taskfile-manager` | Taskfile validation |
| `health-check` | Environment integrity |
| `stack-manager` | Stack bootstrapping |
| `rule-builder` | Rule creation |

### Hooks

Event-driven automation. Configured in `config/config.yml`.

| Hook | Trigger | Purpose |
|------|---------|---------|
| `logger` | Tool calls | Log all tool invocations |
| `rules_loader` | Session start | Inject behavioral rules |
| `session_context_injector` | Session start | Add project context |
| `plan_distributor` | Plan save | Copy plans to `${CLAUDE_PLANS_PATH}` |
| `changelog_monitor` | Notification | Parse Claude Code changelogs |
| `playwright_healer` | Browser error | Auto-recovery for Playwright |
| `cloud_auth_prompt` | Session start | Prompt for cloud auth |
| `submodule_auto_updater` | Session start | Update .claude submodule |

## Structure

```text
.claude/
├── agents/          # Agent definitions (12 agents)
├── apps/            # Python implementations
│   ├── src/claude_apps/
│   │   ├── hooks/   # Hook implementations
│   │   ├── skills/  # Skill implementations
│   │   └── shared/  # Shared utilities (aws_utils, config_helper)
│   └── tests/       # pytest test suite (1079 tests)
├── commands/        # Slash command definitions
├── config/          # Configuration
│   ├── templates/   # Gomplate templates
│   └── config.yml   # Global settings
├── docker/          # Container setup
│   ├── Dockerfile
│   └── docker-entrypoint.sh
├── docs/            # Documentation
├── hooks/           # Hook entry points
├── plans/           # Implementation plans
├── rules/           # Behavioral rules (11 rules)
├── skills/          # Skill definitions and SKILL.md
├── stacks/          # Application stack templates
├── tasks/           # Taskfile includes
│   ├── docker/      # Container tasks
│   ├── git/         # Git workflow tasks
│   ├── playwright/  # Browser automation tasks
│   ├── rules/       # Rule management tasks
│   └── tests/       # Test runner tasks
├── .data/           # Runtime data (logs, cache)
└── Taskfile.yml     # Main task runner
```

## Configuration

The `config/config.yml` file controls system behavior:

```yaml
cloud_providers:
  aws:
    enabled: true
    sso_start_url: "${AWS_SSO_START_URL}"
  gcp:
    enabled: true

project_metadata:
  auto_update: true
  stale_threshold_hours: 24

hooks:
  logger:
    enabled: true
    output_dir: ".data/logs"
  playwright_healer:
    enabled: true
    max_retries: 3
  rules_loader:
    enabled: true
  # ... additional hook settings
```

## Stacks

Application templates for rapid project scaffolding. Use `/stack-manager` to bootstrap.

| Stack | Frontend | Backend | Database |
|-------|----------|---------|----------|
| `django-htmx` | HTMX | Django | SQLite/Postgres |
| `electron-react` | React | Electron | Local |
| `go-templ-htmx` | HTMX/Templ | Go | SQLite |
| `htmx-fastapi` | HTMX | FastAPI | SQLite |
| `nextjs-prisma` | Next.js | Next.js API | Prisma/Postgres |
| `sveltekit-supabase` | SvelteKit | SvelteKit | Supabase |
| `vue-vite-fastapi` | Vue 3/Vite | FastAPI | SQLite |

## Updating the Submodule

### Via Task

```bash
task claude:fetch
```

### Via Git

```bash
# Standard update
git submodule update --init --remote --merge .claude

# Manual pull
git -C .claude checkout main && git -C .claude pull origin main

# Nuclear reset
git -C .claude fetch origin
git -C .claude reset --hard origin/main
git -C .claude clean -fd
```

## Removing the Submodule

```bash
git submodule deinit -f .claude
rm -rf .git/modules/.claude
git rm -f .claude
git commit -m "Remove .claude submodule"
```

## Technologies

- **Container**: Ubuntu 24.04, Docker-in-Docker
- **Languages**: Python (uv), Node.js, Go, Rust, JDK
- **Cloud**: AWS CLI, GCP CLI, Pulumi, OpenTofu
- **Browser**: Playwright, Chrome
- **MCP**: Context7, Playwright
- **Templating**: gomplate (Go templates)
- **Logging**: structlog, loguru
- **Testing**: pytest, pytest-cov, moto (1079 tests)
- **Tasks**: Taskfile (go-task)

## Resources

- [Claude Code Docs](https://docs.anthropic.com/en/docs/claude-code)
- [Taskfile](https://taskfile.dev/)
- [gomplate](https://github.com/hairyhenderson/gomplate)
