---
name: aws-login
description: Authenticate to AWS using SSO. Use when user selects AWS from cloud provider selection, or says "login to AWS", "AWS SSO", "authenticate to AWS".
allowed-tools: Bash, Read, AskUserQuestion
---

# AWS Login Skill

Authenticate to AWS using SSO (Single Sign-On) with interactive account selection.

## Activation Triggers

- cloud-auth agent invokes this skill after user selects AWS
- User says: "login to AWS", "AWS SSO", "authenticate to AWS"
- User explicitly invokes: "use the aws-login skill"

## Prerequisites

- AWS CLI v2 installed with SSO support
- SSO configuration in `.aws.yml`
- Valid SSO session or ability to authenticate via browser

## Workflow

### Step 1: Check Configuration

Verify AWS SSO configuration exists:

```bash
cat ${CLAUDE_PATH}/.aws.yml 2>/dev/null | head -20
```

If config not found:
- Run setup wizard: `uv run --directory ${CLAUDE_SKILLS_PATH}/aws-login python scripts/config/setup_wizard.py`
- Wizard will prompt for SSO URL and detect region

### Step 2: Check Current Credentials

Check if valid SSO credentials exist:

```bash
uv run --directory ${CLAUDE_SKILLS_PATH}/aws-login python scripts/cli/sso_check.py --quiet ${ACCOUNT}
```

Where `${ACCOUNT}` is the account alias (e.g., "root", "sandbox", "manager").

Exit codes:
- 0: Valid credentials exist
- 1: Credentials expired or missing

### Step 3: Account Selection

If no account specified, use AskUserQuestion to present available accounts:

```json
{
  "question": "Which AWS account would you like to use?",
  "header": "AWS Account",
  "options": [
    {"label": "root", "description": "Management account (Organizations access)"},
    {"label": "sandbox", "description": "Development/testing account"},
    {"label": "Interactive menu", "description": "Show all available accounts"}
  ],
  "multiSelect": false
}
```

If "Interactive menu" selected:
```bash
uv run --directory ${CLAUDE_SKILLS_PATH}/aws-login python scripts/discovery/account_discovery.py
```

### Step 4: Authenticate

If credentials expired or missing, initiate SSO login:

```bash
uv run --directory ${CLAUDE_SKILLS_PATH}/aws-login python scripts/cli/sso_login.py ${ACCOUNT}
```

This will:
1. Open browser for SSO authentication (or provide device code URL)
2. Wait for authentication to complete
3. Cache credentials locally

### Step 5: Verify Authentication

After login completes:

```bash
aws sts get-caller-identity --profile ${ACCOUNT}
```

Report to user:
- Account ID
- ARN (identity)
- User/Role name

## Configuration File (.aws.yml)

Located at `${CLAUDE_PATH}/.aws.yml`:

```yaml
schema_version: "2.0"
sso:
  start_url: https://mycompany.awsapps.com/start
  region: us-east-1
  role_name: AdministratorAccess

defaults:
  region: us-east-1

accounts:
  root:
    account_number: "123456789012"
    role_name: AdministratorAccess
  sandbox:
    account_number: "234567890123"
```

## Error Handling

| Error | Resolution |
|-------|------------|
| Config not found | Run setup wizard |
| Account not in config | Offer to sync from Organizations |
| SSO session expired | Initiate new SSO login |
| Auth timeout | Offer retry or cancel |
| No browser available | Use device code flow |

## Taskfile Integration

Available via Taskfile.yml:

```bash
# Check credentials
task aws-check ACCOUNT=sandbox

# Login to account
task aws-login ACCOUNT=sandbox

# Ensure valid credentials (silent)
task aws-ensure-login ACCOUNT=sandbox

# List configured accounts
task aws-list-accounts
```

## Safety Rules

**NEVER**:
- Store long-term credentials
- Log SSO tokens or session data
- Modify AWS credentials outside SSO flow
- Run destructive AWS commands without confirmation

**ALWAYS**:
- Use SSO for authentication
- Verify identity after login
- Allow user to cancel authentication
- Respect existing valid credentials

## Example Flow

```text
User: login to AWS

Claude: Checking AWS configuration...
        SSO URL: https://mycompany.awsapps.com/start
        Configured accounts: root, sandbox, manager

Claude: Which AWS account would you like to use?
        [AskUserQuestion: root | sandbox | Interactive menu]

User: [selects sandbox]

Claude: Checking credentials for sandbox...
        Status: Expired

Claude: Starting SSO authentication for sandbox...
        Opening browser for SSO login...
        [Waiting for authentication...]

Claude: AWS authentication successful!
        Account: 234567890123
        Identity: arn:aws:sts::234567890123:assumed-role/AdministratorAccess/user@example.com
```

## Directory Structure

```
skills/aws-login/
├── SKILL.md              # This file
├── pyproject.toml        # Python dependencies
└── scripts/
    ├── cli/
    │   ├── sso_check.py   # Check credential status
    │   └── sso_login.py   # Perform SSO login
    ├── core/
    │   ├── auth_helper.py # Session/auth utilities
    │   ├── config_reader.py # Read .aws.yml
    │   └── logging_config.py
    ├── config/
    │   └── setup_wizard.py # First-run setup
    └── discovery/
        └── account_discovery.py # Org account discovery
```
