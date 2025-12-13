# Plan: Multi-Cloud Authentication System

## Summary

Convert the AWS toolkit into a skill-based architecture and add GCP support, with a SessionStart hook that prompts for cloud provider selection.

## Architecture

```
Entry Points:
├── SessionStart hook              →  Auto-prompt at session start
└── /cloud-auth command            →  User-initiated anytime
                ↓
        cloud-auth-agent           →  Orchestrates provider selection (AskUserQuestion)
                ↓
        Skills (aws-login, gcp-login)  →  Execute provider-specific auth flows
```

**Key insight:** This pattern (hook + command + agent + skill) is reusable for other capabilities.

## Target Structure

```
.claude/
├── config.yml                              # ADD: cloud_providers section
├── settings.json                           # ADD: cloud_auth_prompt hook
├── commands/
│   └── cloud-auth.md                       # NEW: /cloud-auth slash command
├── agents/
│   └── cloud-auth-agent.md                 # NEW: Orchestrator agent
├── hooks/
│   └── cloud_auth_prompt/                  # NEW: SessionStart hook
│       ├── pyproject.toml
│       └── src/
│           ├── __main__.py
│           ├── config_reader.py
│           └── formatter.py
├── skills/
│   ├── aws-login/                          # NEW: Move from ./aws/
│   │   ├── SKILL.md
│   │   ├── pyproject.toml
│   │   └── scripts/                        # Existing Python modules
│   │       ├── cli/sso_check.py
│   │       ├── cli/sso_login.py
│   │       ├── core/auth_helper.py
│   │       └── ...
│   └── gcp-login/                          # NEW: Convert from PowerShell
│       ├── SKILL.md
│       ├── pyproject.toml
│       └── scripts/
│           ├── auth.py
│           ├── quota_project.py
│           └── bucket_policy.py
└── scripts/
    └── gcloud-auth.ps1                     # DELETE: Replaced by gcp-login skill
```

## Config Schema (config.yml addition)

```yaml
cloud_providers:
  aws:
    enabled: true
    display_name: "AWS"
    description: "Amazon Web Services SSO"
    config_file: .aws.yml                   # Provider-specific config stays separate
    prompt_at_start: true

  gcp:
    enabled: true
    display_name: "GCP"
    description: "Google Cloud Platform"
    default_project: ${GOOGLE_CLOUD_PROJECT}
    prompt_at_start: true
```

## Implementation Phases

### Phase 1: Create cloud-auth-agent and /cloud-auth command
1. Create `commands/` directory (doesn't exist yet)
2. Create `commands/cloud-auth.md` - slash command that invokes agent
3. Create `agents/cloud-auth-agent.md` - orchestrator with:
   - Multi-select provider prompt (AskUserQuestion)
   - Invokes aws-login and/or gcp-login skills
   - Handles errors and retries

### Phase 2: Create cloud_auth_prompt Hook
1. Create `hooks/cloud_auth_prompt/` directory
2. Create `pyproject.toml` with pyyaml dependency
3. Create `src/__main__.py` - reads stdin, outputs hook JSON
4. Create `src/config_reader.py` - reads cloud_providers from config.yml
5. Create `src/formatter.py` - generates context to invoke cloud-auth-agent
6. Add hook to `settings.json` SessionStart hooks list

### Phase 3: Create gcp-login Skill
1. Create `skills/gcp-login/` directory
2. Write `SKILL.md` with workflow instructions
3. Create `pyproject.toml` with loguru dependency
4. Convert `scripts/gcloud-auth.ps1` to Python:
   - `scripts/auth.py` - `gcloud auth login --update-adc --no-browser`
   - `scripts/quota_project.py` - set project and quota project
   - `scripts/bucket_policy.py` - optional IAM binding
5. Delete `scripts/gcloud-auth.ps1`

### Phase 4: Create aws-login Skill
1. Create `skills/aws-login/` directory
2. Write `SKILL.md` with workflow instructions
3. Move `aws/` contents to `skills/aws-login/scripts/`
4. Update imports in moved files
5. Create `pyproject.toml` with boto3, pyyaml, loguru dependencies
6. Update Taskfile.yml AWS_SCRIPTS_PATH
7. Delete empty `aws/` directory

### Phase 5: Configuration Updates
1. Add `cloud_providers:` section to `config.yml`
2. Add skill permissions to `settings.local.json`
3. Test end-to-end flow

### Phase 6: Integration Testing
1. Test /cloud-auth command invokes agent correctly
2. Test SessionStart hook triggers prompt
3. Test AWS SSO login flow
4. Test GCP ADC login flow
5. Test multi-select with both providers

### Phase 7: Cleanup
1. Delete `scripts/gcloud-auth.ps1`
2. Delete empty `aws/` directory after move
3. Verify no broken references

### (Future) Update skill-builder-agent
- Add this pattern (hook + command + agent + skill) as recommended workflow

## Files to Create

| File | Purpose |
|------|---------|
| `commands/cloud-auth.md` | /cloud-auth slash command |
| `agents/cloud-auth-agent.md` | Orchestrator agent |
| `hooks/cloud_auth_prompt/pyproject.toml` | Hook dependencies |
| `hooks/cloud_auth_prompt/src/__main__.py` | Hook entry point |
| `hooks/cloud_auth_prompt/src/config_reader.py` | Read cloud_providers |
| `hooks/cloud_auth_prompt/src/formatter.py` | Generate hook output |
| `skills/aws-login/SKILL.md` | AWS skill definition |
| `skills/aws-login/pyproject.toml` | AWS dependencies |
| `skills/gcp-login/SKILL.md` | GCP skill definition |
| `skills/gcp-login/pyproject.toml` | GCP dependencies |
| `skills/gcp-login/scripts/auth.py` | GCP auth logic |
| `skills/gcp-login/scripts/quota_project.py` | Project selection |
| `skills/gcp-login/scripts/bucket_policy.py` | Optional IAM binding |

## Files to Modify

| File | Change |
|------|--------|
| `config.yml` | Add cloud_providers section |
| `settings.json` | Add cloud_auth_prompt hook |
| `settings.local.json` | Add Skill(aws-login), Skill(gcp-login) permissions |
| `Taskfile.yml` | Update AWS_SCRIPTS_PATH to skills/aws-login/scripts |

## Files to Move

| From | To |
|------|-----|
| `aws/*` | `skills/aws-login/scripts/` |

## Files to Delete

| File | Reason |
|------|--------|
| `scripts/gcloud-auth.ps1` | Replaced by gcp-login skill |
| `aws/` (directory) | Moved to skills/aws-login/scripts/ |

## TODO

- [x] Phase 1: Create cloud-auth-agent and /cloud-auth command
- [x] Phase 2: Create cloud_auth_prompt hook
- [x] Phase 3: Create gcp-login skill
- [x] Phase 4: Create aws-login skill (move aws/)
- [x] Phase 5: Update configurations
- [x] Phase 6: Integration testing
- [x] Phase 7: Cleanup old files
- [ ] (Future) Update skill-builder-agent with this pattern
