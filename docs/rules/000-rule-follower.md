# Rule 000: rule-follower

> Always evaluate adherence to every core directive.

## Priority

**Highest** - This is the foundational rule that ensures all other rules are followed.

## Directive

Claude must evaluate adherence to EVERY core directive during the thinking phase and before responding to the user.

## Behavior

Before each response:
1. Review all loaded rules
2. Evaluate compliance with each
3. Adjust response to maintain compliance
4. Document rule considerations in thinking

## Reinforcement

This rule is reinforced on every message via `config.yml`:
```yaml
hooks:
  rules_loader:
    rules:
      000-rule-follower:
        reinforce: true
```

## Source

[rules/000-rule-follower.md](../../rules/000-rule-follower.md)
