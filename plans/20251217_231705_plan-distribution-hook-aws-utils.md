# Plan: Plan Distribution Hook + aws_utils Extension

**Created**: 2025-12-17 23:17:05
**Status**: Draft
**Canonical Location**: `/workspace/.claude/plans/` (per Rule 040 submodule exception)

> **NOTE**: This plan modifies `.claude/` submodule files. Per Rule 040, it must be
> committed to the `.claude` repo at `/workspace/.claude/plans/`.

---

## Part 1: Plan Distribution Hook (Priority)

### Objective

Create a `PostToolUse` hook that triggers on `ExitPlanMode` to automatically distribute plan files to appropriate project directories.

### Distribution Rules

| Files Touched | Target Directory |
|---------------|------------------|
| `/workspace/.claude/**` | `/workspace/.claude/plans/` (always) |
| `/workspace/projects/<name>/**` | `/workspace/projects/<name>/plans/` |
| `/workspace/**` (root files) | `/workspace/plans/` |

### Hook Design

**Trigger**: `PostToolUse` with matcher `ExitPlanMode`

**Input** (from stdin):
```json
{
  "tool_name": "ExitPlanMode",
  "tool_response": [...],
  "session_id": "..."
}
```

**Logic**:
1. Extract plan file path from tool_response
2. Read plan content
3. Parse file paths from "File Summary" or content
4. Group paths by project root
5. Copy plan to each identified project's `plans/` directory
6. Return success with distribution summary

### Files to Create

| File | Purpose |
|------|---------|
| `hooks/plan_distributor/pyproject.toml` | Package config |
| `hooks/plan_distributor/src/__init__.py` | Package init |
| `hooks/plan_distributor/src/__main__.py` | Entry point |
| `hooks/plan_distributor/src/parser.py` | Extract file paths from plan |
| `hooks/plan_distributor/src/distributor.py` | Copy logic |

### Settings Update

Add to `config/templates/settings.json`:
```json
"PostToolUse": [
  {
    "matcher": "ExitPlanMode",
    "hooks": [
      {
        "type": "command",
        "command": "uv run --directory {{ .Env.CLAUDE_HOOKS_PATH }}/plan_distributor python -m src"
      }
    ]
  },
  // ... existing hooks
]
```

---

## Part 2: aws_utils Service Extension

### Objective

Extend `/workspace/.claude/lib/aws_utils` with six new AWS service discovery modules and refactor `sso_discovery.py` from the aws-login skill into the library.

## New Services to Add

| Service | Module | Resources |
|---------|--------|-----------|
| Lambda | `lambda_svc.py` | Functions, configurations |
| RDS | `rds.py` | DB instances, clusters |
| Route53 | `route53.py` | Hosted zones, DNS records |
| DynamoDB | `dynamodb.py` | Tables |
| Step Functions | `stepfunctions.py` | State machines, activities |
| SSO | `sso.py` | SSO instances, accounts (moved from aws-login) |

## Implementation Tasks

### 1. Create Service Discovery Modules

**Pattern** (from existing services):
```python
from typing import TYPE_CHECKING
from botocore.exceptions import ClientError
from ..core.session import create_session
from ..core.schemas import ResourceSchema

if TYPE_CHECKING:
    import boto3

def discover_resources(profile: str | None = None) -> list[ResourceSchema]:
    session = create_session(profile)
    client = session.client("service-name")
    resources = []
    try:
        # API calls with pagination
    except ClientError:
        return []
    return resources
```

**Files to create**:
- `/workspace/.claude/lib/aws_utils/services/lambda_svc.py`
- `/workspace/.claude/lib/aws_utils/services/rds.py`
- `/workspace/.claude/lib/aws_utils/services/route53.py`
- `/workspace/.claude/lib/aws_utils/services/dynamodb.py`
- `/workspace/.claude/lib/aws_utils/services/stepfunctions.py`
- `/workspace/.claude/lib/aws_utils/services/sso.py`

### 2. Add Pydantic Schemas

**File**: `/workspace/.claude/lib/aws_utils/core/schemas.py`

New schemas to add:
```python
class LambdaFunction(BaseModel):
    function_name: str
    runtime: str | None
    memory_size: int
    timeout: int
    last_modified: str
    arn: str

class RDSInstance(BaseModel):
    db_instance_identifier: str
    engine: str
    engine_version: str
    instance_class: str
    status: str
    endpoint: str | None
    arn: str

class RDSCluster(BaseModel):
    cluster_identifier: str
    engine: str
    engine_version: str
    status: str
    endpoint: str | None
    arn: str

class Route53Zone(BaseModel):
    zone_id: str
    name: str
    is_private: bool
    record_count: int

class Route53Record(BaseModel):
    zone_id: str
    name: str
    record_type: str
    ttl: int | None
    values: list[str]

class DynamoDBTable(BaseModel):
    table_name: str
    status: str
    item_count: int
    size_bytes: int
    arn: str

class StateMachine(BaseModel):
    name: str
    arn: str
    status: str
    machine_type: str  # STANDARD or EXPRESS
    creation_date: str

class SFNActivity(BaseModel):
    name: str
    arn: str
    creation_date: str

class SSOInstance(BaseModel):
    instance_arn: str
    identity_store_id: str

class SSOAccount(BaseModel):
    account_id: str
    account_name: str
    email_address: str
```

### 3. Update Exports

**File**: `/workspace/.claude/lib/aws_utils/services/__init__.py`
- Add imports for all new service modules

**File**: `/workspace/.claude/lib/aws_utils/__init__.py`
- Add schema exports
- Add service function exports

### 4. Refactor aws-login Skill

**Source**: `/workspace/.claude/skills/aws-login/lib/sso_discovery.py`
**Target**: `/workspace/.claude/lib/aws_utils/services/sso.py`

**Changes to aws-login**:
- Update `/workspace/.claude/skills/aws-login/lib/discovery.py` to import from aws_utils
- Delete original `sso_discovery.py` after migration

### 5. Update AccountInventory Schema

**File**: `/workspace/.claude/lib/aws_utils/core/schemas.py`

Extend `AccountInventory` to include new resource types:
```python
class AccountInventory(BaseModel):
    account_id: str
    account_name: str
    # Existing
    ec2_instances: list[EC2Instance] = []
    s3_buckets: list[S3Bucket] = []
    # ... existing fields ...

    # New fields
    lambda_functions: list[LambdaFunction] = []
    rds_instances: list[RDSInstance] = []
    rds_clusters: list[RDSCluster] = []
    route53_zones: list[Route53Zone] = []
    dynamodb_tables: list[DynamoDBTable] = []
    state_machines: list[StateMachine] = []
    sfn_activities: list[SFNActivity] = []
```

### 6. Create Tests

**File**: `/workspace/.claude/lib/aws_utils/tests/test_new_services.py`

Test coverage for:
- Each new schema instantiation
- Each discovery function (mocked boto3 responses)
- Error handling (ClientError returns empty list)

---

## Combined File Summary

### Part 1: Plan Distribution Hook

| Action | File |
|--------|------|
| CREATE | `hooks/plan_distributor/pyproject.toml` |
| CREATE | `hooks/plan_distributor/src/__init__.py` |
| CREATE | `hooks/plan_distributor/src/__main__.py` |
| CREATE | `hooks/plan_distributor/src/parser.py` |
| CREATE | `hooks/plan_distributor/src/distributor.py` |
| MODIFY | `config/templates/settings.json` |

### Part 2: aws_utils Extension

| Action | File |
|--------|------|
| CREATE | `lib/aws_utils/services/lambda_svc.py` |
| CREATE | `lib/aws_utils/services/rds.py` |
| CREATE | `lib/aws_utils/services/route53.py` |
| CREATE | `lib/aws_utils/services/dynamodb.py` |
| CREATE | `lib/aws_utils/services/stepfunctions.py` |
| CREATE | `lib/aws_utils/services/sso.py` |
| CREATE | `lib/aws_utils/tests/test_new_services.py` |
| MODIFY | `lib/aws_utils/core/schemas.py` |
| MODIFY | `lib/aws_utils/services/__init__.py` |
| MODIFY | `lib/aws_utils/__init__.py` |
| MODIFY | `skills/aws-login/lib/discovery.py` |
| DELETE | `skills/aws-login/lib/sso_discovery.py` |

---

## Execution Order

### Phase A: Plan Distribution Hook (Priority)

1. Create `hooks/plan_distributor/` directory structure
2. Implement `parser.py` - extract file paths from plan markdown
3. Implement `distributor.py` - copy logic with project root detection
4. Implement `__main__.py` - entry point for PostToolUse
5. Create `pyproject.toml` with dependencies
6. Update `config/templates/settings.json` with new hook
7. Regenerate settings via gomplate
8. Test hook manually

### Phase B: aws_utils Extension

9. Add new schemas to `lib/aws_utils/core/schemas.py`
10. Create service modules (lambda_svc, rds, route53, dynamodb, stepfunctions)
11. Move sso_discovery.py to sso.py with adaptations
12. Update `services/__init__.py` exports
13. Update main `__init__.py` exports
14. Update aws-login skill to import from aws_utils
15. Delete original sso_discovery.py
16. Create test suite
17. Run tests: `task lib:test`
18. Run lint: `task lib:lint`
