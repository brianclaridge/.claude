# Plan: Slash Command Architecture & Documentation

**Date:** 2025-12-13
**Status:** COMPLETED
**Objective:** Create slash commands for all agents/skills, create gitops agent, update README.md

---

## Command Architecture

| Command | Agent | Skills Invoked |
|---------|-------|----------------|
| `/hello` | hello-world | — |
| `/analyze` | project-analysis | session-context, project-metadata-builder |
| `/cloud-auth` | cloud-auth | aws-login, gcp-login |
| `/playwright` | browser-automation | playwright-automation |
| `/build-agent` | agent-builder | — |
| `/build-skill` | skill-builder | — |
| `/gitops` | **gitops** (NEW) | git-manager |
| `/context` | — | session-context (direct) |
| `/metadata` | — | project-metadata-builder (direct) |

---

## Tasks

### 1. Create gitops Agent
**File:** `.claude/agents/gitops.md`

```yaml
---
name: gitops
description: Manage git workflow with interactive commit, push, and branch operations.
allowed-tools: Bash, Read, Glob, Grep, AskUserQuestion, EnterPlanMode
---
```
Invoke git-manager skill for commit workflow.

### 2. Create Slash Commands

| File | Content Summary |
|------|-----------------|
| `commands/hello.md` | Invoke hello-world agent |
| `commands/analyze.md` | Invoke project-analysis agent |
| `commands/playwright.md` | Invoke browser-automation agent |
| `commands/build-agent.md` | Invoke agent-builder agent |
| `commands/build-skill.md` | Invoke skill-builder agent |
| `commands/gitops.md` | Invoke gitops agent |
| `commands/context.md` | Invoke session-context skill directly |
| `commands/metadata.md` | Invoke project-metadata-builder skill directly |

### 3. Update README.md

Add tables for:
- **Slash Commands** - command, description, usage
- **Agents** - name, description, skills used
- **Skills** - name, description, trigger

Update **Structure** section to reflect current directories.

---

## Files to Create/Modify

| File | Action |
|------|--------|
| `.claude/agents/gitops.md` | Create |
| `.claude/commands/hello.md` | Create |
| `.claude/commands/analyze.md` | Create |
| `.claude/commands/playwright.md` | Create |
| `.claude/commands/build-agent.md` | Create |
| `.claude/commands/build-skill.md` | Create |
| `.claude/commands/gitops.md` | Create |
| `.claude/commands/context.md` | Create |
| `.claude/commands/metadata.md` | Create |
| `.claude/README.md` | Update |

---

## Command Format Template

```markdown
{Description}. Use the {agent-name} agent.

Invoke the {agent-name} agent with: "{prompt}"
```

---

## README Updates

### Software Requirements
Add Git to existing requirements:
- [Git](https://git-scm.com/download/)

### Structure Section
Replace outdated tree with current directories:
- commands/ directory
- All current hooks (rules_loader, logger, cloud_auth_prompt, session_context_injector, playwright_healer)
- All current skills (6 total)
- All current agents (7 total after gitops)
