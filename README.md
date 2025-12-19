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

## Workflow

```
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

## Documentation

| Guide | Description |
|-------|-------------|
| [Setup](docs/SETUP.md) | Prerequisites, installation, configuration |
| [Architecture](docs/ARCHITECTURE.md) | System design, directory structure |
| [Development](docs/DEVELOPMENT.md) | Extending with agents, skills, hooks |
| [Troubleshooting](docs/TROUBLESHOOTING.md) | Common issues and solutions |

## Reference

| Section | Description |
|---------|-------------|
| [Agents](docs/agents/README.md) | Specialized sub-agents (11) |
| [Skills](docs/skills/README.md) | Model-invoked capabilities (11) |
| [Rules](docs/rules/README.md) | Behavioral directives (000-095) |
| [Stacks](docs/stacks/README.md) | Application templates (6) |

## Structure

```
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
