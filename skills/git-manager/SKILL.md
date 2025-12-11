---
name: git-manager
description: Commit implementation changes to git with interactive branch selection and push confirmation. Use after completing implementation tasks, when all TODOs are marked complete, or when user requests to commit changes.
allowed-tools: Bash, Read, Glob, Grep, AskUserQuestion
---

# Git Manager

Interactive git commit workflow with safety checks and user confirmation.

## Activation Triggers

- All plan TODOs marked complete (invoked via DIRECTIVE 040)
- User says "commit changes", "commit my work", "save to git"
- User explicitly invokes: "use the git-manager skill"

## Workflow

### Step 0: Git Identity Configuration

Before any git operations, ensure git identity is configured:

```bash
# Load git credentials from /workspace/.env
source /workspace/.env 2>/dev/null || true

# Configure git if credentials are available
if [ -n "$GIT_USER_EMAIL" ]; then
  git config user.email "$GIT_USER_EMAIL"
fi
if [ -n "$GIT_USER_NAME" ]; then
  git config user.name "$GIT_USER_NAME"
fi
```

If `GIT_USER_EMAIL` and `GIT_USER_NAME` are not set in `/workspace/.claude/.env`:
- Check if git already has identity configured: `git config user.email`
- If not configured, ask user for email and name using AskUserQuestion
- Suggest saving to `/workspace/.claude/.env` for future sessions

### Step 1: Status Check

Run `git status` to detect changes:

- If no changes: Inform user "No uncommitted changes detected" and exit
- If changes exist: Proceed to step 2

### Step 2: Branch Selection

Use AskUserQuestion to present branch options:

- Current branch: {current_branch_name}
- Create new branch (I'll ask for name)
- Cancel commit

If "Create new branch" selected:

- Ask for branch name using AskUserQuestion
- Create and checkout: `git checkout -b {branch_name}`

### Step 3: Review Changes

Display summary of changes:

- Run `git diff --stat` to show file changes
- List modified, new, and deleted files

### Step 4: Generate Commit Message

Analyze implementation context to generate commit message:

- Review recent conversation for task context
- Check TODO list completions if available
- Follow conventional commit format when appropriate:
  - `feat:` for new features
  - `fix:` for bug fixes
  - `docs:` for documentation
  - `refactor:` for refactoring
  - `chore:` for maintenance
- Generate multi-line message with summary and details

Use AskUserQuestion to confirm or edit:

- Accept this message
- Edit message (I'll ask for new text)
- Cancel commit

### Step 5: Stage and Commit

1. Stage all changes: `git add -A`
2. Commit with message using HEREDOC format:

```bash
git commit -m "$(cat <<'EOF'
{commit_message}
EOF
)"
```

### Step 6: Push Confirmation

Use AskUserQuestion:

- Yes, push to origin/{branch}
- No, keep local only

If yes: `git push -u origin {branch}` (use -u for new branches)

## Safety Rules

**NEVER**:

- Force push (`--force`, `-f`)
- Skip hooks (`--no-verify`)
- Commit files matching these patterns:
  - `.env`, `.env.*` (except `.env.example`)
  - `*credentials*`, `*secret*`, `*.pem`, `*.key`
  - `aws-exports.js`
  - Files in `.gitignore`
- Amend commits not created in this session
- Push to main/master without explicit user confirmation

**ALWAYS**:

- Verify `.gitignore` is respected
- Check for sensitive file patterns before staging
- Confirm branch before committing
- Use standard push (never force)

## Error Handling

- **Not a git repo**: Inform user "This directory is not a git repository" and exit
- **Conflicts detected**: Inform user about conflicts, provide guidance, exit workflow
- **Command failure**: Display error message, do not retry automatically
- **No remote**: Report error, commit preserved locally

## Sensitive File Detection

Before staging, scan for sensitive patterns:

```bash
git status --porcelain | grep -E '\.(env|pem|key)$|credentials|secret'
```

If found:

- Warn user about detected sensitive files
- Ask whether to exclude them from commit
- Use `git add` with explicit file list instead of `-A`

## Example Flow

```text
User: [completes implementation, all TODOs done]

Claude: I'll help commit these changes.
[Runs git status: 5 files modified, 2 new]

Claude: Where should I commit?
[AskUserQuestion: Current branch: feature/auth | Create new | Cancel]
User: [selects Current branch]

Claude: Changes to commit:
 src/auth.py    | 45 +++++++++
 src/config.py  | 12 ++-
 tests/test_auth.py | 78 ++++++++++++++++

Claude: Proposed commit message:
---
feat(auth): implement OAuth2 login flow

- Add OAuth2 provider configuration
- Create login callback handler
- Add session management
- Update user model with provider fields
---
[AskUserQuestion: Accept | Edit | Cancel]
User: [selects Accept]

Claude: Committed! Push to origin/feature/auth?
[AskUserQuestion: Yes | No]
User: [selects Yes]

Claude: Changes pushed to origin/feature/auth.
```
