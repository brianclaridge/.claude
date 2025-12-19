# aws-login Skill

> AWS SSO authentication via device authorization flow.

## Overview

Handles AWS Identity Center (SSO) authentication using the device authorization flow. Creates AWS CLI profiles for discovered accounts.

## Activation Triggers

- "login to AWS"
- "AWS SSO"
- "authenticate to AWS"
- cloud-auth agent invocation

## Workflow

1. Start device authorization (generates code + URL)
2. User completes browser authentication
3. Poll for token
4. Discover SSO accounts and roles
5. Generate AWS CLI profiles
6. Cache credentials

## Configuration

Required in `.env`:
```bash
AWS_SSO_START_URL="https://your-org.awsapps.com/start"
AWS_SSO_REGION="us-west-2"
AWS_DEFAULT_REGION="us-east-1"
AWS_SSO_ROLE_NAME="AdministratorAccess"
```

## Data Storage

- Accounts: `.data/aws/accounts.yml`
- Profiles: `~/.aws/config`

## Source

[skills/aws-login/README.md](../../skills/aws-login/README.md)
