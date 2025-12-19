# Claude Code Guide - .claude Submodule

> Workflow guide for Claude Code in the .claude development environment.

## Behavioral Rules

This environment enforces 11 rules. See [Rules Documentation](docs/rules/README.md).

| Rule | Name | Purpose |
|------|------|---------|
| [000](docs/rules/000-rule-follower.md) | rule-follower | Evaluate all directives |
| [010](docs/rules/010-session-starter.md) | session-starter | Auto-analyze on start |
| [020](docs/rules/020-persona.md) | persona | Spock-like logical persona |
| [030](docs/rules/030-agents.md) | agents | Consider agents for tasks |
| [040](docs/rules/040-plans.md) | plans | Create plans before work |
| [050](docs/rules/050-python.md) | python | Use uv, structured logging |
| [060](docs/rules/060-context7.md) | context7 | Use Context7 for libraries |
| [070](docs/rules/070-backward-compat.md) | backward-compat | No compat unless requested |
| [080](docs/rules/080-ask-user-questions.md) | ask-user-questions | Use AskUserQuestion tool |
| [090](docs/rules/090-taskfile-usage.md) | taskfile-usage | Taskfile best practices |
| [095](docs/rules/095-gomplate-usage.md) | gomplate-usage | gomplate best practices |

## Available Agents

See [Agents Documentation](docs/agents/README.md).

| Command | Agent | Purpose |
|---------|-------|---------|
| `/hello` | hello-world | Test output |
| `/analyze` | project-analysis | Codebase analysis |
| `/cloud-auth` | cloud-auth | AWS/GCP authentication |
| `/playwright` | browser-automation | Browser tasks |
| `/gitops` | gitops | Git commit workflow |
| `/stack-manager` | stack-manager | Stack recommendations |
| `/taskfile` | taskfile-manager | Validate Taskfile |
| `/gomplate` | gomplate-manager | Validate templates |
| `/health` | health-check | Environment validation |
| `/build-skill` | skill-builder | Create skills |
| `/build-agent` | agent-builder | Create agents |
| `/build-rule` | rule-builder | Create rules |

## Available Skills

See [Skills Documentation](docs/skills/README.md).

| Skill | Trigger |
|-------|---------|
| git-manager | TODOs complete, "commit" |
| aws-login | "login to AWS" |
| gcp-login | "login to GCP" |
| playwright-automation | "screenshot", "video" |
| session-context | Session start |
| project-metadata-builder | Analysis complete |

## Development Workflow

```
1. Session Start
   └─→ project-analysis agent runs (Rule 010)

2. User Request
   └─→ Create plan in plans/ (Rule 040)
   └─→ Ask user approval

3. Implementation
   └─→ Track progress with TodoWrite
   └─→ Use Context7 for libraries (Rule 060)

4. Completion
   └─→ git-manager skill commits (Rule 040)
   └─→ Enter plan mode for next task
```

## Key Patterns

- **Plans**: Always create in `plans/` before implementation
- **Questions**: Use AskUserQuestion tool (Rule 080)
- **Libraries**: Use Context7 MCP for documentation (Rule 060)
- **Python**: Use `uv run` syntax (Rule 050)
- **Agents**: Consider for every request (Rule 030)

## Configuration

- `config.yml` - Global settings
- `settings.json` - Claude Code settings
- `.env` - Environment variables (gitignored)

## Documentation

- [Setup Guide](docs/SETUP.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Development](docs/DEVELOPMENT.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
