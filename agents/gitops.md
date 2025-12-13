---
name: gitops
description: Manage git workflow with interactive commit, push, and branch operations. Use when user says "commit changes", "push to git", "/gitops", or after completing implementation tasks.
allowed-tools: Bash, Read, Glob, Grep, AskUserQuestion, EnterPlanMode
---

# Git Operations Agent

Orchestrates git commit workflow using the git-manager skill.

## Activation

- User invokes `/gitops`
- User says "commit changes", "commit my work", "save to git"
- After completing implementation tasks when all TODOs are marked complete

## Workflow

Invoke the git-manager skill to handle:

1. Git identity configuration
2. Change detection and status check
3. Mode selection (auto/interactive)
4. Branch selection
5. Commit message generation
6. Push confirmation
7. Next action selection

## Invocation

```
Invoke the git-manager skill with: "Execute git commit workflow for current changes."
```
