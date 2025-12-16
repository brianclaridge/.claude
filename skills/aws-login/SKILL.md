---
name: aws-login
description: Authenticate to AWS using SSO. Use when user selects AWS from cloud provider selection, or says "login to AWS", "AWS SSO", "authenticate to AWS".
allowed-tools: Bash, Read, AskUserQuestion
---

# AWS Login Skill

Authenticate to AWS using SSO (Single Sign-On).

## Activation Triggers

- `/auth-aws` slash command
- User says: "login to AWS", "AWS SSO", "authenticate to AWS"

## Prerequisites

Environment variables in `.env`:

```bash
AWS_SSO_START_URL="https://your-org.awsapps.com/start"
AWS_ROOT_ACCOUNT_ID="123456789012"
AWS_ROOT_ACCOUNT_NAME="your-org"
```

## Usage

### Human CLI

```powershell
# Interactive account selection
./scripts/aws-auth.ps1

# Login to specific account
./scripts/aws-auth.ps1 root

# Force re-login
./scripts/aws-auth.ps1 sandbox -Force

# First-time setup
./scripts/aws-auth.ps1 -Setup
```

### Claude Agent

```bash
# Via skill invocation
uv run --directory ${CLAUDE_SKILLS_PATH}/aws-login python -m lib [account] [--force]
```

## First-Run Setup

When no `.aws.yml` config exists:

1. Reads env vars for root account configuration
2. Creates AWS CLI profile for root account
3. Runs SSO login for root (presents URL and device code)
4. Discovers accounts from AWS Organizations
5. Saves accounts to `${CLAUDE_DATA_PATH}/.aws.yml`

## SSO URL Detection

The skill captures and displays the SSO URL and device code:

| Field | Value |
|-------|-------|
| URL | https://your-org.awsapps.com/start/#/device |
| Code | **XXXX-XXXX** |

## Configuration

Accounts stored at `${CLAUDE_DATA_PATH}/.aws.yml`:

```yaml
schema_version: "1.0"
default_region: us-east-1

accounts:
  root:
    account_name: "Management Account"
    account_number: "123456789012"
    sso_role_name: AdministratorAccess
  sandbox:
    account_name: "Development"
    account_number: "234567890123"
    sso_role_name: AdministratorAccess
```

## Directory Structure

```
skills/aws-login/
├── lib/
│   ├── __init__.py
│   ├── __main__.py    # Entry point
│   ├── config.py      # Config from env vars + .aws.yml
│   ├── sso.py         # SSO login with URL detection
│   ├── discovery.py   # Organizations account discovery
│   └── profiles.py    # AWS CLI profile management
├── pyproject.toml
└── SKILL.md
```
