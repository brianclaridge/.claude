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
| `/hello` | Test output |
| `/analyze` | Codebase analysis |
| `/cloud-auth` | AWS/GCP authentication |
| `/playwright` | Browser automation |
| `/gitops` | Git commit workflow |
| `/stack-manager` | Bootstrap stacks |
| `/taskfile` | Validate Taskfile |
| `/health` | Environment check |

## Structure

```text
.claude/
├── agents/          # Agent definitions
├── commands/        # Slash commands
├── config/          # Templates
├── docs/            # Documentation
├── hooks/           # Event handlers
├── lib/             # Python libraries
├── rules/           # Behavioral rules
├── skills/          # Skill implementations
├── stacks/          # Stack templates
├── config.yml       # Global config
└── Taskfile.yml     # Task runner
```

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

## Resources

- [Claude Code Docs](https://docs.anthropic.com/en/docs/claude-code)
- [Taskfile](https://taskfile.dev/)
- [gomplate](https://github.com/hairyhenderson/gomplate)
