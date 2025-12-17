# Plan: AWS Inspector Library & Split Architecture

## Summary

1. Create shared library `.claude/lib/aws_inspector/` for AWS resource discovery
2. Refactor aws-login skill to use shared library
3. Split `.aws.yml` into accounts.yml (auth) + per-account inventory files

## Architecture

```
.claude/
├── lib/
│   └── aws_inspector/              # NEW: Shared library
│       ├── __init__.py             # Public API
│       ├── pyproject.toml          # Dependencies
│       ├── core/
│       │   ├── __init__.py
│       │   ├── session.py          # Boto3 session management
│       │   └── schemas.py          # Pydantic models
│       ├── services/
│       │   ├── __init__.py
│       │   ├── ec2.py              # VPC, subnet, IGW, NAT, EIP
│       │   ├── s3.py               # S3 buckets
│       │   ├── sqs.py              # SQS queues
│       │   ├── sns.py              # SNS topics
│       │   ├── ses.py              # SES identities
│       │   └── organizations.py    # Org/account discovery
│       └── inventory/
│           ├── __init__.py
│           ├── reader.py           # Load inventory files
│           └── writer.py           # Save inventory files
└── skills/
    └── aws-login/
        └── lib/
            ├── __main__.py         # CLI (imports aws_inspector)
            ├── config.py           # Auth config only
            ├── sso.py              # Unchanged
            └── profiles.py         # Unchanged
```

## Data Directory Structure

```
.data/aws/
├── accounts.yml                    # Auth-only (v4.0)
└── {org-id}/
    └── {ou-path}/
        └── {alias}.yml             # Inventory (v1.0)
```

Example:
```
.data/aws/
├── accounts.yml
└── o-abc123xyz/
    ├── piam-dev-accounts/
    │   └── sandbox.yml
    └── piam-ops-accounts/
        └── root.yml
```

## Schema: accounts.yml (v4.0)

```yaml
schema_version: "4.0"
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
```

## Schema: {alias}.yml (v1.0)

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

## CLI Changes

- Add `--skip-resources` flag (default: enabled, flag disables extended resources)
- Existing `--skip-vpc` skips VPC + all resources

## Files to Create/Modify

### New Files (aws_inspector library)

| File | Purpose |
|------|---------|
| `.claude/lib/aws_inspector/__init__.py` | Public API exports |
| `.claude/lib/aws_inspector/pyproject.toml` | Dependencies (boto3, pydantic, loguru, pyyaml) |
| `.claude/lib/aws_inspector/core/__init__.py` | Core module exports |
| `.claude/lib/aws_inspector/core/session.py` | Boto3 session factory |
| `.claude/lib/aws_inspector/core/schemas.py` | Pydantic models for inventory |
| `.claude/lib/aws_inspector/services/__init__.py` | Service module exports |
| `.claude/lib/aws_inspector/services/ec2.py` | VPC, subnet, IGW, NAT, EIP discovery |
| `.claude/lib/aws_inspector/services/s3.py` | S3 bucket discovery |
| `.claude/lib/aws_inspector/services/sqs.py` | SQS queue discovery |
| `.claude/lib/aws_inspector/services/sns.py` | SNS topic discovery |
| `.claude/lib/aws_inspector/services/ses.py` | SES identity discovery |
| `.claude/lib/aws_inspector/services/organizations.py` | Org/account discovery |
| `.claude/lib/aws_inspector/inventory/__init__.py` | Inventory module exports |
| `.claude/lib/aws_inspector/inventory/reader.py` | Load inventory files |
| `.claude/lib/aws_inspector/inventory/writer.py` | Save inventory files |

### Modified Files (aws-login skill)

| File | Changes |
|------|---------|
| `skills/aws-login/lib/config.py` | Auth-only config, remove VPC logic |
| `skills/aws-login/lib/discovery.py` | Import from aws_inspector, thin wrapper |
| `skills/aws-login/lib/__main__.py` | --skip-resources flag, use aws_inspector |
| `skills/aws-login/SKILL.md` | v4.0 schema documentation |

## Implementation Phases

### Phase 1: aws_inspector Core
- [ ] Create `.claude/lib/aws_inspector/` directory structure
- [ ] Create `pyproject.toml` with dependencies
- [ ] Implement `core/session.py` - Boto3 session factory
- [ ] Implement `core/schemas.py` - Pydantic models for inventory

### Phase 2: aws_inspector Services
- [ ] Implement `services/ec2.py` - VPC, subnet, IGW, NAT, EIP
- [ ] Implement `services/s3.py` - S3 bucket discovery
- [ ] Implement `services/sqs.py` - SQS queue discovery
- [ ] Implement `services/sns.py` - SNS topic discovery
- [ ] Implement `services/ses.py` - SES identity discovery
- [ ] Implement `services/organizations.py` - Org/account discovery

### Phase 3: aws_inspector Inventory
- [ ] Implement `inventory/reader.py` - Load inventory files
- [ ] Implement `inventory/writer.py` - Save inventory files
- [ ] Implement directory structure creation (OU hierarchy)

### Phase 4: aws-login Skill Refactor
- [ ] Update `config.py` - Auth-only, remove VPC logic
- [ ] Update `discovery.py` - Import from aws_inspector
- [ ] Update `__main__.py` - Add --skip-resources, use aws_inspector
- [ ] Implement migration from v3.1 to v4.0

### Phase 5: Testing & Documentation
- [ ] Update SKILL.md with v4.0 schema documentation
- [ ] Test migration from v3.1 to v4.0
- [ ] Test first-run setup with split architecture
- [ ] Test --skip-vpc and --skip-resources flags

## Error Handling

All resource discovery failures are **non-blocking**:
- S3/SQS/SNS/SES failures: Log warning, return empty array
- NAT Gateway failures: Subnet has no `nat_gateway` key
- Migration failures: Abort, leave original .aws.yml intact

## Migration Strategy

1. Detect schema_version in existing .aws.yml
2. If v3.x: Run automatic migration
3. Create .data/aws/ directory structure
4. Write accounts.yml (auth-only)
5. Write individual {alias}.yml inventory files
6. Backup old .aws.yml to .aws.yml.v3.bak
