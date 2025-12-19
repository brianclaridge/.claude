# Rule 030: agents

> Consider agent use for every request.

## Priority

Workflow (030-049)

## Directive

When reasoning, thinking, or planning, always consider using an agent before responding. Document the decision for each available agent.

## Behavior

Include in response:
```
Agent Decision Matrix:
| Agent | Reason | Decision |
|-------|--------|----------|
| project-analysis | Not analyzing codebase | Skip |
| gitops | Implementation complete | Use |
```

## Purpose

Ensures appropriate delegation to specialized agents for complex tasks.

## Reinforcement

Enabled in `config.yml`:
```yaml
hooks:
  rules_loader:
    rules:
      030-agents:
        reinforce: true
```

## Source

[rules/030-agents.md](../../rules/030-agents.md)
