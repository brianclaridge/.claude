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

## Documentation

| Guide | Description |
|-------|-------------|
| [Setup](docs/SETUP.md) | Prerequisites, installation, configuration |
| [Architecture](docs/ARCHITECTURE.md) | System design, directory structure |
| [Claude Guide](CLAUDE.md) | Workflow and rules reference |
| [Development](docs/DEVELOPMENT.md) | Extending with agents, skills, hooks |
| [Troubleshooting](docs/TROUBLESHOOTING.md) | Common issues and solutions |

## Reference

| Section | Description |
|---------|-------------|
| [Agents](docs/agents/README.md) | Specialized sub-agents (11) |
| [Skills](docs/skills/README.md) | Model-invoked capabilities (11) |
| [Rules](docs/rules/README.md) | Behavioral directives (000-095) |
| [Stacks](docs/stacks/README.md) | Application templates (6) |

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
├── CLAUDE.md        # Workflow guide
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
