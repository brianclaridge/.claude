# Plan: Extend aws_utils with ECS, EKS, and ACM Service Discovery

**Created**: 2025-12-18T00:13:59
**Scope**: Add container orchestration and certificate management discovery to aws_utils

## Summary

Extend `lib/aws_utils` with three new AWS service modules (ECS, EKS, ACM) following the established discovery pattern. Integrate new resource types into the `AccountInventory` schema for YAML serialization.

## New Schemas

### ECS Resources
```python
class ECSCluster(BaseModel):
    cluster_name: str
    cluster_arn: str
    status: str
    registered_container_instances: int
    running_tasks: int
    pending_tasks: int
    active_services: int
    region: str

class ECSService(BaseModel):
    service_name: str
    service_arn: str
    cluster_arn: str
    status: str
    desired_count: int
    running_count: int
    launch_type: str  # FARGATE | EC2
    task_definition: str
    region: str

class ECSTaskDefinition(BaseModel):
    family: str
    task_definition_arn: str
    revision: int
    status: str
    cpu: str | None
    memory: str | None
    requires_compatibilities: list[str]
    region: str
```

### EKS Resources
```python
class EKSCluster(BaseModel):
    cluster_name: str
    cluster_arn: str
    status: str
    version: str
    endpoint: str | None
    platform_version: str | None
    created_at: datetime | None
    region: str

class EKSNodeGroup(BaseModel):
    nodegroup_name: str
    nodegroup_arn: str
    cluster_name: str
    status: str
    instance_types: list[str]
    desired_size: int
    min_size: int
    max_size: int
    region: str

class EKSFargateProfile(BaseModel):
    fargate_profile_name: str
    fargate_profile_arn: str
    cluster_name: str
    status: str
    pod_execution_role_arn: str
    selectors: list[dict]
    region: str
```

### ACM Resources
```python
class ACMCertificate(BaseModel):
    certificate_arn: str
    domain_name: str
    status: str  # ISSUED | PENDING_VALIDATION | EXPIRED | etc.
    type: str  # AMAZON_ISSUED | IMPORTED
    issuer: str | None
    not_before: datetime | None
    not_after: datetime | None
    in_use_by: list[str]
    subject_alternative_names: list[str]
    region: str
```

## New Service Modules

### 1. `/workspace/.claude/lib/aws_utils/services/ecs.py`
```
discover_ecs_clusters(profile_name, region) -> list[ECSCluster]
discover_ecs_services(profile_name, region, cluster_arn) -> list[ECSService]
discover_all_ecs_services(profile_name, region) -> list[ECSService]
discover_ecs_task_definitions(profile_name, region) -> list[ECSTaskDefinition]
```

### 2. `/workspace/.claude/lib/aws_utils/services/eks.py`
```
discover_eks_clusters(profile_name, region) -> list[EKSCluster]
discover_eks_node_groups(profile_name, region, cluster_name) -> list[EKSNodeGroup]
discover_all_eks_node_groups(profile_name, region) -> list[EKSNodeGroup]
discover_eks_fargate_profiles(profile_name, region, cluster_name) -> list[EKSFargateProfile]
```

### 3. `/workspace/.claude/lib/aws_utils/services/acm.py`
```
discover_acm_certificates(profile_name, region) -> list[ACMCertificate]
```

## Files to Modify

| File | Change |
|------|--------|
| `lib/aws_utils/core/schemas.py` | Add 9 new Pydantic models, extend AccountInventory |
| `lib/aws_utils/services/ecs.py` | **NEW** - ECS discovery functions |
| `lib/aws_utils/services/eks.py` | **NEW** - EKS discovery functions |
| `lib/aws_utils/services/acm.py` | **NEW** - ACM discovery functions |
| `lib/aws_utils/services/__init__.py` | Export new modules |
| `lib/aws_utils/__init__.py` | Export new schemas and functions |
| `lib/tests/test_aws_utils/test_ecs_eks_acm.py` | **NEW** - Test suite |

## AccountInventory Extensions

Add to `AccountInventory` schema:
```python
ecs_clusters: list[ECSCluster] = []
ecs_services: list[ECSService] = []
ecs_task_definitions: list[ECSTaskDefinition] = []
eks_clusters: list[EKSCluster] = []
eks_node_groups: list[EKSNodeGroup] = []
eks_fargate_profiles: list[EKSFargateProfile] = []
acm_certificates: list[ACMCertificate] = []
```

## Implementation Order

1. Add Pydantic schemas to `core/schemas.py`
2. Create `services/ecs.py` with discovery functions
3. Create `services/eks.py` with discovery functions
4. Create `services/acm.py` with discovery functions
5. Update `services/__init__.py` exports
6. Update main `__init__.py` exports
7. Create test suite with mocked boto3
8. Run tests and lint

## AWS API Reference

### ECS
- `list_clusters()` + `describe_clusters()`
- `list_services(cluster)` + `describe_services()`
- `list_task_definitions()` (ACTIVE status filter)

### EKS
- `list_clusters()` + `describe_cluster()`
- `list_nodegroups(cluster)` + `describe_nodegroup()`
- `list_fargate_profiles(cluster)` + `describe_fargate_profile()`

### ACM
- `list_certificates()` + `describe_certificate()`

## Test Strategy

- Mock boto3 clients with realistic API responses
- Test pagination scenarios
- Test empty results handling
- Test ClientError resilience
- Validate Pydantic model serialization
