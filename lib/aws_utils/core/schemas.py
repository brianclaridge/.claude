"""Pydantic models for AWS inventory schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class NATGateway(BaseModel):
    """NAT Gateway attached to a subnet."""

    id: str = Field(description="NAT Gateway ID (nat-xxx)")
    state: str = Field(description="State (available, pending, etc.)")
    elastic_ip: str | None = Field(default=None, description="Elastic IP allocation ID")
    public_ip: str | None = Field(default=None, description="Public IP address")


class Subnet(BaseModel):
    """VPC Subnet."""

    id: str = Field(description="Subnet ID (subnet-xxx)")
    cidr: str = Field(description="CIDR block (e.g., 10.0.1.0/24)")
    az: str = Field(description="Availability zone (e.g., us-east-1a)")
    type: str = Field(description="Subnet type: public or private")
    nat_gateway: NATGateway | None = Field(
        default=None, description="NAT Gateway if present in this subnet"
    )


class InternetGateway(BaseModel):
    """Internet Gateway attached to a VPC."""

    id: str = Field(description="Internet Gateway ID (igw-xxx)")
    state: str = Field(default="attached", description="Attachment state")


class VPC(BaseModel):
    """Virtual Private Cloud."""

    id: str = Field(description="VPC ID (vpc-xxx)")
    cidr: str = Field(description="Primary CIDR block")
    is_default: bool = Field(default=False, description="Whether this is the default VPC")
    internet_gateways: list[InternetGateway] = Field(
        default_factory=list, description="Attached Internet Gateways"
    )
    subnets: list[Subnet] = Field(default_factory=list, description="Subnets in this VPC")


class ElasticIP(BaseModel):
    """Elastic IP address."""

    allocation_id: str = Field(description="Allocation ID (eipalloc-xxx)")
    public_ip: str = Field(description="Public IP address")
    association_id: str | None = Field(default=None, description="Association ID if attached")
    domain: str = Field(default="vpc", description="Domain (vpc or standard)")
    region: str = Field(description="AWS region")


class S3Bucket(BaseModel):
    """S3 Bucket."""

    name: str = Field(description="Bucket name")
    region: str = Field(description="Bucket region")
    arn: str = Field(description="Bucket ARN")
    created: datetime | None = Field(default=None, description="Creation date")


class SQSQueue(BaseModel):
    """SQS Queue."""

    name: str = Field(description="Queue name")
    url: str = Field(description="Queue URL")
    arn: str = Field(description="Queue ARN")
    region: str = Field(description="AWS region")


class SNSTopic(BaseModel):
    """SNS Topic."""

    name: str = Field(description="Topic name")
    arn: str = Field(description="Topic ARN")
    region: str = Field(description="AWS region")


class SESIdentity(BaseModel):
    """SES Identity (email or domain)."""

    identity: str = Field(description="Email address or domain")
    type: str = Field(description="Identity type: EmailAddress or Domain")
    verification_status: str | None = Field(
        default=None, description="Verification status"
    )
    region: str = Field(description="AWS region")


class LambdaFunction(BaseModel):
    """AWS Lambda Function."""

    function_name: str = Field(description="Function name")
    runtime: str | None = Field(default=None, description="Runtime (e.g., python3.12)")
    memory_size: int = Field(description="Memory size in MB")
    timeout: int = Field(description="Timeout in seconds")
    last_modified: str = Field(description="Last modified timestamp")
    arn: str = Field(description="Function ARN")
    region: str = Field(description="AWS region")


class RDSInstance(BaseModel):
    """RDS Database Instance."""

    db_instance_identifier: str = Field(description="DB instance identifier")
    engine: str = Field(description="Database engine (mysql, postgres, etc.)")
    engine_version: str = Field(description="Engine version")
    instance_class: str = Field(description="Instance class (db.t3.micro, etc.)")
    status: str = Field(description="Instance status")
    endpoint: str | None = Field(default=None, description="Endpoint address")
    port: int | None = Field(default=None, description="Endpoint port")
    arn: str = Field(description="Instance ARN")
    region: str = Field(description="AWS region")


class RDSCluster(BaseModel):
    """RDS Aurora Cluster."""

    cluster_identifier: str = Field(description="Cluster identifier")
    engine: str = Field(description="Database engine (aurora-mysql, aurora-postgresql)")
    engine_version: str = Field(description="Engine version")
    status: str = Field(description="Cluster status")
    endpoint: str | None = Field(default=None, description="Writer endpoint")
    reader_endpoint: str | None = Field(default=None, description="Reader endpoint")
    port: int | None = Field(default=None, description="Endpoint port")
    arn: str = Field(description="Cluster ARN")
    region: str = Field(description="AWS region")


class Route53Zone(BaseModel):
    """Route53 Hosted Zone."""

    zone_id: str = Field(description="Hosted zone ID")
    name: str = Field(description="Zone name (domain)")
    is_private: bool = Field(default=False, description="Whether zone is private")
    record_count: int = Field(default=0, description="Number of resource records")


class Route53Record(BaseModel):
    """Route53 DNS Record."""

    zone_id: str = Field(description="Parent zone ID")
    name: str = Field(description="Record name (FQDN)")
    record_type: str = Field(description="Record type (A, AAAA, CNAME, etc.)")
    ttl: int | None = Field(default=None, description="TTL in seconds")
    values: list[str] = Field(default_factory=list, description="Record values")


class DynamoDBTable(BaseModel):
    """DynamoDB Table."""

    table_name: str = Field(description="Table name")
    status: str = Field(description="Table status (ACTIVE, etc.)")
    item_count: int = Field(default=0, description="Approximate item count")
    size_bytes: int = Field(default=0, description="Table size in bytes")
    arn: str = Field(description="Table ARN")
    region: str = Field(description="AWS region")


class StateMachine(BaseModel):
    """Step Functions State Machine."""

    name: str = Field(description="State machine name")
    arn: str = Field(description="State machine ARN")
    status: str = Field(description="Status (ACTIVE, DELETING)")
    machine_type: str = Field(description="Type (STANDARD or EXPRESS)")
    creation_date: str = Field(description="Creation timestamp")
    region: str = Field(description="AWS region")


class SFNActivity(BaseModel):
    """Step Functions Activity."""

    name: str = Field(description="Activity name")
    arn: str = Field(description="Activity ARN")
    creation_date: str = Field(description="Creation timestamp")
    region: str = Field(description="AWS region")


class SSOInstance(BaseModel):
    """AWS SSO Instance."""

    instance_arn: str = Field(description="SSO instance ARN")
    identity_store_id: str = Field(description="Identity store ID")


class SSOAccount(BaseModel):
    """AWS Account accessible via SSO."""

    account_id: str = Field(description="AWS Account ID")
    account_name: str = Field(description="Account name")
    email_address: str = Field(description="Account email")


# ECS Resources
class ECSCluster(BaseModel):
    """ECS Cluster."""

    cluster_name: str = Field(description="Cluster name")
    cluster_arn: str = Field(description="Cluster ARN")
    status: str = Field(description="Cluster status (ACTIVE, etc.)")
    registered_container_instances: int = Field(
        default=0, description="Number of registered container instances"
    )
    running_tasks: int = Field(default=0, description="Number of running tasks")
    pending_tasks: int = Field(default=0, description="Number of pending tasks")
    active_services: int = Field(default=0, description="Number of active services")
    region: str = Field(description="AWS region")


class ECSService(BaseModel):
    """ECS Service."""

    service_name: str = Field(description="Service name")
    service_arn: str = Field(description="Service ARN")
    cluster_arn: str = Field(description="Parent cluster ARN")
    status: str = Field(description="Service status")
    desired_count: int = Field(default=0, description="Desired task count")
    running_count: int = Field(default=0, description="Running task count")
    launch_type: str = Field(description="Launch type (FARGATE or EC2)")
    task_definition: str = Field(description="Task definition ARN")
    region: str = Field(description="AWS region")


class ECSTaskDefinition(BaseModel):
    """ECS Task Definition."""

    family: str = Field(description="Task definition family")
    task_definition_arn: str = Field(description="Task definition ARN")
    revision: int = Field(description="Revision number")
    status: str = Field(description="Status (ACTIVE, INACTIVE)")
    cpu: str | None = Field(default=None, description="CPU units")
    memory: str | None = Field(default=None, description="Memory in MB")
    requires_compatibilities: list[str] = Field(
        default_factory=list, description="Required compatibilities (FARGATE, EC2)"
    )
    region: str = Field(description="AWS region")


# EKS Resources
class EKSCluster(BaseModel):
    """EKS Kubernetes Cluster."""

    cluster_name: str = Field(description="Cluster name")
    cluster_arn: str = Field(description="Cluster ARN")
    status: str = Field(description="Cluster status (ACTIVE, CREATING, etc.)")
    version: str = Field(description="Kubernetes version")
    endpoint: str | None = Field(default=None, description="API server endpoint")
    platform_version: str | None = Field(default=None, description="EKS platform version")
    created_at: datetime | None = Field(default=None, description="Creation timestamp")
    region: str = Field(description="AWS region")


class EKSNodeGroup(BaseModel):
    """EKS Managed Node Group."""

    nodegroup_name: str = Field(description="Node group name")
    nodegroup_arn: str = Field(description="Node group ARN")
    cluster_name: str = Field(description="Parent cluster name")
    status: str = Field(description="Node group status")
    instance_types: list[str] = Field(default_factory=list, description="EC2 instance types")
    desired_size: int = Field(default=0, description="Desired node count")
    min_size: int = Field(default=0, description="Minimum node count")
    max_size: int = Field(default=0, description="Maximum node count")
    region: str = Field(description="AWS region")


class EKSFargateProfile(BaseModel):
    """EKS Fargate Profile."""

    fargate_profile_name: str = Field(description="Fargate profile name")
    fargate_profile_arn: str = Field(description="Fargate profile ARN")
    cluster_name: str = Field(description="Parent cluster name")
    status: str = Field(description="Profile status")
    pod_execution_role_arn: str = Field(description="Pod execution role ARN")
    selectors: list[dict] = Field(default_factory=list, description="Pod selectors")
    region: str = Field(description="AWS region")


# ACM Resources
class ACMCertificate(BaseModel):
    """ACM Certificate."""

    certificate_arn: str = Field(description="Certificate ARN")
    domain_name: str = Field(description="Primary domain name")
    status: str = Field(description="Certificate status (ISSUED, PENDING_VALIDATION, etc.)")
    certificate_type: str = Field(description="Certificate type (AMAZON_ISSUED, IMPORTED)")
    issuer: str | None = Field(default=None, description="Certificate issuer")
    not_before: datetime | None = Field(default=None, description="Valid from")
    not_after: datetime | None = Field(default=None, description="Valid until")
    in_use_by: list[str] = Field(default_factory=list, description="Resources using this cert")
    subject_alternative_names: list[str] = Field(
        default_factory=list, description="Subject alternative names (SANs)"
    )
    region: str = Field(description="AWS region")


# Secrets Manager Resources
class SecretsManagerSecret(BaseModel):
    """AWS Secrets Manager secret metadata (not values)."""

    name: str = Field(description="Secret name")
    arn: str = Field(description="Secret ARN")
    description: str | None = Field(default=None, description="Secret description")
    kms_key_id: str | None = Field(default=None, description="KMS key ID for encryption")
    rotation_enabled: bool = Field(default=False, description="Whether rotation is enabled")
    last_rotated_date: str | None = Field(default=None, description="Last rotation date")
    last_accessed_date: str | None = Field(default=None, description="Last access date")
    tags: dict[str, str] = Field(default_factory=dict, description="Resource tags")
    region: str = Field(description="AWS region")


# API Gateway Resources
class APIGatewayRestAPI(BaseModel):
    """AWS API Gateway REST API (v1)."""

    id: str = Field(description="API ID")
    name: str = Field(description="API name")
    description: str | None = Field(default=None, description="API description")
    endpoint_type: str = Field(description="Endpoint type (REGIONAL, EDGE, PRIVATE)")
    created_date: str | None = Field(default=None, description="Creation date")
    api_key_source: str | None = Field(default=None, description="API key source")
    tags: dict[str, str] = Field(default_factory=dict, description="Resource tags")
    region: str = Field(description="AWS region")


class APIGatewayV2API(BaseModel):
    """AWS API Gateway v2 (HTTP/WebSocket)."""

    api_id: str = Field(description="API ID")
    name: str = Field(description="API name")
    description: str | None = Field(default=None, description="API description")
    protocol_type: str = Field(description="Protocol type (HTTP, WEBSOCKET)")
    api_endpoint: str | None = Field(default=None, description="API endpoint URL")
    created_date: str | None = Field(default=None, description="Creation date")
    tags: dict[str, str] = Field(default_factory=dict, description="Resource tags")
    region: str = Field(description="AWS region")


class AccountInventory(BaseModel):
    """Complete inventory for an AWS account."""

    schema_version: str = Field(default="1.0", description="Inventory schema version")
    account_id: str = Field(description="AWS Account ID")
    account_alias: str = Field(description="Account alias")
    discovered_at: datetime = Field(
        default_factory=datetime.utcnow, description="Discovery timestamp"
    )
    region: str = Field(description="Primary region for discovery")

    vpcs: list[VPC] = Field(default_factory=list, description="VPCs in the account")
    elastic_ips: list[ElasticIP] = Field(
        default_factory=list, description="Elastic IPs in the account"
    )
    s3_buckets: list[S3Bucket] = Field(
        default_factory=list, description="S3 buckets in the account"
    )
    sqs_queues: list[SQSQueue] = Field(
        default_factory=list, description="SQS queues in the account"
    )
    sns_topics: list[SNSTopic] = Field(
        default_factory=list, description="SNS topics in the account"
    )
    ses_identities: list[SESIdentity] = Field(
        default_factory=list, description="SES identities in the account"
    )
    lambda_functions: list[LambdaFunction] = Field(
        default_factory=list, description="Lambda functions in the account"
    )
    rds_instances: list[RDSInstance] = Field(
        default_factory=list, description="RDS instances in the account"
    )
    rds_clusters: list[RDSCluster] = Field(
        default_factory=list, description="RDS Aurora clusters in the account"
    )
    route53_zones: list[Route53Zone] = Field(
        default_factory=list, description="Route53 hosted zones"
    )
    dynamodb_tables: list[DynamoDBTable] = Field(
        default_factory=list, description="DynamoDB tables in the account"
    )
    state_machines: list[StateMachine] = Field(
        default_factory=list, description="Step Functions state machines"
    )
    sfn_activities: list[SFNActivity] = Field(
        default_factory=list, description="Step Functions activities"
    )

    # ECS Resources
    ecs_clusters: list[ECSCluster] = Field(
        default_factory=list, description="ECS clusters in the account"
    )
    ecs_services: list[ECSService] = Field(
        default_factory=list, description="ECS services in the account"
    )
    ecs_task_definitions: list[ECSTaskDefinition] = Field(
        default_factory=list, description="ECS task definitions in the account"
    )

    # EKS Resources
    eks_clusters: list[EKSCluster] = Field(
        default_factory=list, description="EKS clusters in the account"
    )
    eks_node_groups: list[EKSNodeGroup] = Field(
        default_factory=list, description="EKS node groups in the account"
    )
    eks_fargate_profiles: list[EKSFargateProfile] = Field(
        default_factory=list, description="EKS Fargate profiles in the account"
    )

    # ACM Resources
    acm_certificates: list[ACMCertificate] = Field(
        default_factory=list, description="ACM certificates in the account"
    )

    # Secrets Manager Resources
    secrets: list[SecretsManagerSecret] = Field(
        default_factory=list, description="Secrets Manager secrets (metadata only)"
    )

    # API Gateway Resources
    api_gateway_rest_apis: list[APIGatewayRestAPI] = Field(
        default_factory=list, description="API Gateway REST APIs (v1)"
    )
    api_gateway_v2_apis: list[APIGatewayV2API] = Field(
        default_factory=list, description="API Gateway HTTP/WebSocket APIs (v2)"
    )

    def to_dict(self) -> dict:
        """Convert to dictionary for YAML serialization."""
        data = self.model_dump()
        # Convert datetime to ISO string
        data["discovered_at"] = self.discovered_at.isoformat()
        for bucket in data.get("s3_buckets", []):
            if bucket.get("created"):
                bucket["created"] = bucket["created"].isoformat()
        # EKS cluster created_at
        for cluster in data.get("eks_clusters", []):
            if cluster.get("created_at"):
                cluster["created_at"] = cluster["created_at"].isoformat()
        # ACM certificate dates
        for cert in data.get("acm_certificates", []):
            if cert.get("not_before"):
                cert["not_before"] = cert["not_before"].isoformat()
            if cert.get("not_after"):
                cert["not_after"] = cert["not_after"].isoformat()
        return data


class AccountConfig(BaseModel):
    """Account configuration for auth (v4.0 schema)."""

    id: str = Field(description="AWS Account ID")
    name: str = Field(description="Account name")
    ou_path: str = Field(description="OU path (e.g., piam-dev-accounts)")
    sso_role: str = Field(default="AdministratorAccess", description="SSO role name")
    inventory_path: str | None = Field(
        default=None, description="Relative path to inventory file"
    )


class AccountsConfig(BaseModel):
    """Root configuration for accounts.yml (v4.0 schema)."""

    schema_version: str = Field(default="4.0", description="Config schema version")
    organization_id: str = Field(description="AWS Organization ID (o-xxx)")
    default_region: str = Field(default="us-east-1", description="Default AWS region")
    sso_start_url: str = Field(description="AWS SSO start URL")

    accounts: dict[str, AccountConfig] = Field(
        default_factory=dict, description="Account configurations by alias"
    )

    def to_dict(self) -> dict:
        """Convert to dictionary for YAML serialization."""
        return self.model_dump()
