# Plan: Improve git-manager Headless Identity Handling

## Summary
Enhance git-manager skill to automatically detect and persist git identity for headless CLI environments.

## Problem Statement
Git commits fail in headless CLI when:
1. `user.email` and `user.name` not configured
2. No `${CLAUDE_PATH}/.env` credentials stored
3. Interactive prompts cannot complete (no AskUserQuestion for free-form)

## Current State
- SSH authentication: Working (verified `Hi brianclaridge!`)
- Remote type: SSH (`git@github.com:`)
- Identity storage: Empty (no `GIT_USER_*` in .env)
- git-manager Step 0: Checks .env but doesn't persist after asking

## Target File
`.claude/skills/git-manager/SKILL.md`

## Implementation

### Enhanced Step 0: Identity Auto-Detection

```bash
# 1. Check .env first
source ${CLAUDE_PATH}/.env 2>/dev/null || true

# 2. If missing, try to detect from SSH
if [ -z "$GIT_USER_NAME" ]; then
  # Extract from SSH test
  GIT_USER_NAME=$(ssh -T git@github.com 2>&1 | grep -oP 'Hi \K[^!]+' || echo "")
fi

# 3. If still missing, check global config
if [ -z "$GIT_USER_NAME" ]; then
  GIT_USER_NAME=$(git config --global user.name 2>/dev/null || echo "")
fi

# 4. Derive email from GitHub noreply pattern
if [ -z "$GIT_USER_EMAIL" ] && [ -n "$GIT_USER_NAME" ]; then
  GIT_USER_EMAIL="${GIT_USER_NAME}@users.noreply.github.com"
fi
```

### Workflow Changes

1. **Auto-detect before asking**: Try SSH detection first
2. **Suggest derived values**: Show user what we detected, ask to confirm
3. **Persist to .env**: After confirmation, append to `${CLAUDE_PATH}/.env`
4. **Silent on subsequent runs**: If .env has values, use them without prompting

### New Step 0 Logic (pseudo-code)

```
IF .env has GIT_USER_EMAIL and GIT_USER_NAME:
  → Configure git, proceed silently

ELSE IF SSH auth works:
  → Detect username from SSH
  → Derive email: {username}@users.noreply.github.com
  → Present to user via AskUserQuestion:
    - "Accept detected: {name} <{email}>"
    - "Enter custom values"
  → Persist to .env

ELSE:
  → Ask for free-form email/name (plain text, per DIRECTIVE 080 exception)
  → Persist to .env
```

### AskUserQuestion Integration

```json
{
  "question": "Git identity detected from SSH. Use these values?",
  "header": "Git ID",
  "options": [
    {"label": "Yes, use detected", "description": "brianclaridge <brianclaridge@users.noreply.github.com>"},
    {"label": "Enter custom", "description": "I'll ask for your preferred email/name"}
  ],
  "multiSelect": false
}
```

## TODO
- [ ] Seed ${CLAUDE_PATH}/.env with GIT_USER_NAME and GIT_USER_EMAIL now
- [ ] Update Step 0 in SKILL.md with auto-detection logic
- [ ] Add SSH username extraction command
- [ ] Add .env persistence after confirmation
- [ ] Update error handling for no-SSH-auth scenario
- [ ] Commit video recorder changes (pending from earlier)
- [ ] Test full workflow in headless environment

## Files to Modify
- `${CLAUDE_PATH}/.env` (seed GIT_USER_* variables)
- `.claude/skills/git-manager/SKILL.md` (enhance Step 0)

## Testing
1. Clear ${CLAUDE_PATH}/.env of GIT_* vars
2. Invoke git-manager skill
3. Verify SSH detection works
4. Confirm values persisted to .env
5. Run again, verify silent config
