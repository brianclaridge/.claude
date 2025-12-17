---
name: aws-login
description: Authenticate to AWS using SSO. Use when user selects AWS from cloud provider selection, or says "login to AWS", "AWS SSO", "authenticate to AWS".
allowed-tools: Bash, Read, AskUserQuestion
---

# AWS Login Skill

Authenticate to AWS using SSO (Single Sign-On) with optional resource discovery.

## Activation Triggers

- `/auth-aws` slash command
- User says: "login to AWS", "AWS SSO", "authenticate to AWS"

## Prerequisites

Environment variables in `.env`:

```bash
AWS_SSO_START_URL="https://your-org.awsapps.com/start"
AWS_ROOT_ACCOUNT_ID="123456789012"
AWS_ROOT_ACCOUNT_NAME="your-org"
AWS_DEFAULT_REGION="us-east-1"  # Optional, defaults to us-east-1
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

# First-time setup (full discovery)
./scripts/aws-auth.ps1 -Setup

# Setup with auth only (no resource discovery)
./scripts/aws-auth.ps1 -Setup -SkipVpc

# Setup with VPCs only (skip S3/SQS/SNS/SES)
./scripts/aws-auth.ps1 -Setup -SkipResources

# Rebuild config (re-auth only if needed)
./scripts/aws-auth.ps1 -Rebuild
```

### Claude Agent

```bash
# Via skill invocation
uv run --directory ${CLAUDE_SKILLS_PATH}/aws-login python -m lib [account] [--force]

# With flags
uv run --directory ${CLAUDE_SKILLS_PATH}/aws-login python -m lib --setup --skip-resources
```

## First-Run Setup

When no `accounts.yml` config exists:

1. Reads env vars for root account configuration
2. Creates AWS CLI profile for root account
3. Runs SSO login for root (presents URL and device code)
4. Discovers accounts from AWS Organizations
5. Discovers resources for each account (parallel, 8 workers)
6. Saves auth config to `${CLAUDE_DATA_PATH}/.data/aws/accounts.yml`
7. Saves inventory per account to `${CLAUDE_DATA_PATH}/.data/aws/{org-id}/{ou-path}/{alias}.yml`

## Discovery Flags

| Flag | Effect |
|------|--------|
| `--skip-vpc` | Skip ALL resource discovery (auth only) |
| `--skip-resources` | Skip S3/SQS/SNS/SES (VPCs still discovered) |
| (none) | Full discovery (VPCs + S3 + SQS + SNS + SES) |

## SSO URL Detection

The skill captures and displays the SSO URL and device code:

| Field | Value |
|-------|-------|
| URL | https://your-org.awsapps.com/start/#/device |
| Code | **XXXX-XXXX** |

## Data Architecture (v1.0)

### Directory Structure

```
.data/aws/
├── accounts.yml                    # Auth-only config
└── {org-id}/                       # Organization ID (o-xxx)
    ├── {ou-path}/                  # OU hierarchy path
    │   └── {alias}.yml             # Per-account inventory
    └── root/                       # Root-level accounts
        └── {alias}.yml
```

Example:
```
.data/aws/
├── accounts.yml
└── o-abc123xyz/
    ├── piam-dev-accounts/
    │   └── sandbox.yml
    └── piam-ops-accounts/
        └── operations.yml
```

### accounts.yml Schema

```yaml
schema_version: "1.0"
organization_id: "o-abc123xyz"
default_region: us-east-1
sso_start_url: "https://your-org.awsapps.com/start"

accounts:
  sandbox:
    id: "411713055198"
    name: "provision-iam-sandbox"
    ou_path: "piam-dev-accounts"
    sso_role: "AdministratorAccess"
    inventory_path: "piam-dev-accounts/sandbox.yml"
  root:
    id: "123456789012"
    name: "Management Account"
    ou_path: "root"
    sso_role: "AdministratorAccess"
    inventory_path: "root/root.yml"
```

### Inventory File Schema ({alias}.yml)

```yaml
schema_version: "1.0"
account_id: "411713055198"
account_alias: "sandbox"
discovered_at: "2025-12-16T15:56:49Z"
region: "us-east-1"

vpcs:
  - id: "vpc-xxx"
    cidr: "10.0.0.0/16"
    is_default: false
    internet_gateways:
      - id: "igw-xxx"
        state: "attached"
    subnets:
      - id: "subnet-xxx"
        cidr: "10.0.1.0/24"
        az: "us-east-1a"
        type: "public"
      - id: "subnet-yyy"
        cidr: "10.0.2.0/24"
        az: "us-east-1b"
        type: "private"
        nat_gateway:
          id: "nat-xxx"
          state: "available"
          elastic_ip: "eipalloc-xxx"

elastic_ips:
  - allocation_id: "eipalloc-xxx"
    public_ip: "54.123.45.67"
    region: "us-east-1"

s3_buckets:
  - name: "my-bucket"
    region: "us-east-1"
    arn: "arn:aws:s3:::my-bucket"

sqs_queues:
  - name: "my-queue"
    region: "us-east-1"
    arn: "arn:aws:sqs:us-east-1:411713055198:my-queue"

sns_topics:
  - name: "my-topic"
    region: "us-east-1"
    arn: "arn:aws:sns:us-east-1:411713055198:my-topic"

ses_identities:
  - identity: "example.com"
    type: "Domain"
    region: "us-east-1"
```

## Skill Directory Structure

```
skills/aws-login/
├── lib/
│   ├── __init__.py
│   ├── __main__.py    # Entry point with CLI
│   ├── config.py      # Auth config (accounts.yml)
│   ├── sso.py         # SSO login with URL detection
│   ├── discovery.py   # Resource discovery (uses aws_inspector)
│   └── profiles.py    # AWS CLI profile management
├── pyproject.toml
└── SKILL.md

lib/aws_inspector/      # Shared library
├── __init__.py
├── pyproject.toml
├── core/
│   ├── session.py     # Boto3 session factory
│   └── schemas.py     # Pydantic models
├── services/
│   ├── ec2.py         # VPC, subnet, IGW, NAT, EIP
│   ├── s3.py          # S3 bucket discovery
│   ├── sqs.py         # SQS queue discovery
│   ├── sns.py         # SNS topic discovery
│   ├── ses.py         # SES identity discovery
│   └── organizations.py  # Org/account discovery
└── inventory/
    ├── reader.py      # Load inventory files
    └── writer.py      # Save inventory files
```
