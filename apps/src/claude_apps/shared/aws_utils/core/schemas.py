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

    # VPC Configuration (for VPC-connected Lambda functions)
    vpc_id: str | None = Field(default=None, description="VPC ID if VPC-configured")
    subnet_ids: list[str] = Field(default_factory=list, description="Subnet IDs for VPC config")
    security_group_ids: list[str] = Field(
        default_factory=list, description="Security group IDs for VPC config"
    )

    # IAM Configuration
    execution_role_arn: str | None = Field(default=None, description="Execution role ARN")

    # Dead Letter Config
    dead_letter_target_arn: str | None = Field(
        default=None, description="DLQ target ARN (SQS queue or SNS topic)"
    )

    # Layers
    layer_arns: list[str] = Field(default_factory=list, description="Lambda Layer ARNs")


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

    # VPC Configuration (for relationship mapping)
    vpc_id: str | None = Field(default=None, description="VPC ID")
    db_subnet_group_name: str | None = Field(default=None, description="DB subnet group name")
    security_group_ids: list[str] = Field(
        default_factory=list, description="VPC security group IDs"
    )

    # Encryption Configuration
    kms_key_id: str | None = Field(default=None, description="KMS key ID for encryption")
    storage_encrypted: bool = Field(default=False, description="Whether storage is encrypted")

    # IAM Configuration
    monitoring_role_arn: str | None = Field(
        default=None, description="Enhanced monitoring IAM role ARN"
    )

    # Cluster Membership
    db_cluster_identifier: str | None = Field(
        default=None, description="Aurora cluster identifier if member"
    )


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

    # VPC Configuration (for relationship mapping)
    vpc_id: str | None = Field(default=None, description="VPC ID")
    db_subnet_group_name: str | None = Field(default=None, description="DB subnet group name")
    security_group_ids: list[str] = Field(
        default_factory=list, description="VPC security group IDs"
    )

    # Encryption Configuration
    kms_key_id: str | None = Field(default=None, description="KMS key ID for encryption")

    # Cluster Members
    db_cluster_members: list[str] = Field(
        default_factory=list, description="DB instance identifiers in this cluster"
    )

    # Associated IAM Roles
    associated_role_arns: list[str] = Field(
        default_factory=list, description="IAM role ARNs associated with cluster"
    )


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

    # Alias Record Configuration (for relationship mapping)
    is_alias: bool = Field(default=False, description="Whether this is an alias record")
    alias_target_dns_name: str | None = Field(
        default=None, description="Alias target DNS name (e.g., ALB DNS name)"
    )
    alias_target_hosted_zone_id: str | None = Field(
        default=None, description="Alias target hosted zone ID"
    )

    # Inferred Target Resource (populated during relationship mapping)
    target_resource_type: str | None = Field(
        default=None, description="Inferred resource type (alb, cloudfront, s3, etc.)"
    )
    target_resource_arn: str | None = Field(
        default=None, description="Inferred target resource ARN"
    )

    # Health Check
    health_check_id: str | None = Field(default=None, description="Associated health check ID")


class Route53Domain(BaseModel):
    """Route53 Registered Domain."""

    domain_name: str = Field(description="Domain name")
    auto_renew: bool = Field(default=True, description="Auto-renewal enabled")
    transfer_lock: bool = Field(default=True, description="Transfer lock enabled")
    expiration_date: str | None = Field(default=None, description="Domain expiration date")
    creation_date: str | None = Field(default=None, description="Domain registration date")
    registrar_name: str | None = Field(default=None, description="Registrar name")
    registrar_url: str | None = Field(default=None, description="Registrar URL")
    abuse_contact_email: str | None = Field(default=None, description="Abuse contact email")
    abuse_contact_phone: str | None = Field(default=None, description="Abuse contact phone")


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

    # IAM Configuration (for relationship mapping)
    role_arn: str | None = Field(default=None, description="Execution role ARN")

    # Logging Configuration
    log_group_arn: str | None = Field(
        default=None, description="CloudWatch Logs log group ARN"
    )
    log_level: str | None = Field(
        default=None, description="Log level (ALL, ERROR, FATAL, OFF)"
    )


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

    # VPC Configuration (for Fargate services)
    vpc_id: str | None = Field(default=None, description="VPC ID for awsvpc network mode")
    subnet_ids: list[str] = Field(
        default_factory=list, description="Subnet IDs for awsvpc network mode"
    )
    security_group_ids: list[str] = Field(
        default_factory=list, description="Security group IDs for awsvpc network mode"
    )

    # Load Balancer Configuration (for relationship mapping)
    load_balancer_target_groups: list[str] = Field(
        default_factory=list, description="Target group ARNs"
    )

    # Service Discovery (Cloud Map)
    service_registries: list[str] = Field(
        default_factory=list, description="Service registry ARNs (Cloud Map)"
    )


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

    # VPC Configuration (for relationship mapping)
    vpc_id: str | None = Field(default=None, description="VPC ID")
    subnet_ids: list[str] = Field(
        default_factory=list, description="Subnet IDs for cluster ENIs"
    )
    security_group_ids: list[str] = Field(
        default_factory=list, description="Additional security group IDs"
    )
    cluster_security_group_id: str | None = Field(
        default=None, description="Cluster security group created by EKS"
    )

    # IAM Configuration
    role_arn: str | None = Field(default=None, description="Cluster IAM role ARN")

    # Logging Configuration
    enabled_log_types: list[str] = Field(
        default_factory=list,
        description="Enabled log types (api, audit, authenticator, controllerManager, scheduler)",
    )


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

    # Network Configuration (for relationship mapping)
    subnet_ids: list[str] = Field(
        default_factory=list, description="Subnet IDs for node placement"
    )

    # IAM Configuration
    node_role_arn: str | None = Field(default=None, description="Node IAM role ARN")

    # Remote Access Configuration
    remote_access_security_group: str | None = Field(
        default=None, description="Security group for SSH access"
    )

    # Launch Template
    launch_template_id: str | None = Field(
        default=None, description="Custom launch template ID"
    )


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


# Cognito Resources
class CognitoUserPool(BaseModel):
    """AWS Cognito User Pool."""

    id: str = Field(description="User pool ID")
    name: str = Field(description="User pool name")
    arn: str = Field(description="User pool ARN")
    status: str | None = Field(default=None, description="User pool status")
    creation_date: str | None = Field(default=None, description="Creation date")
    last_modified_date: str | None = Field(default=None, description="Last modified date")
    mfa_configuration: str | None = Field(default=None, description="MFA configuration (OFF, ON, OPTIONAL)")
    estimated_number_of_users: int = Field(default=0, description="Estimated number of users")
    region: str = Field(description="AWS region")


class CognitoIdentityPool(BaseModel):
    """AWS Cognito Identity Pool (Federated Identities)."""

    identity_pool_id: str = Field(description="Identity pool ID")
    identity_pool_name: str = Field(description="Identity pool name")
    allow_unauthenticated: bool = Field(default=False, description="Allow unauthenticated identities")
    developer_provider_name: str | None = Field(default=None, description="Developer provider name")
    region: str = Field(description="AWS region")


# CloudFront Resources
class CloudFrontOrigin(BaseModel):
    """CloudFront origin configuration."""

    id: str = Field(description="Origin ID")
    domain_name: str = Field(description="Origin domain name")
    origin_type: str | None = Field(
        default=None, description="Origin type (s3, custom, elb, mediastore)"
    )
    s3_origin_config: dict | None = Field(
        default=None, description="S3 origin configuration"
    )
    custom_origin_config: dict | None = Field(
        default=None, description="Custom origin configuration"
    )


class CloudFrontDistribution(BaseModel):
    """AWS CloudFront Distribution."""

    id: str = Field(description="Distribution ID")
    arn: str = Field(description="Distribution ARN")
    domain_name: str = Field(description="CloudFront domain name")
    status: str = Field(description="Distribution status (Deployed, InProgress)")
    enabled: bool = Field(default=True, description="Whether distribution is enabled")
    price_class: str | None = Field(default=None, description="Price class")
    aliases: list[str] = Field(default_factory=list, description="CNAMEs/alternate domain names")
    origins: list[str] = Field(default_factory=list, description="Origin domain names")
    default_root_object: str | None = Field(default=None, description="Default root object")
    comment: str | None = Field(default=None, description="Distribution comment")
    last_modified_time: str | None = Field(default=None, description="Last modified time")

    # ACM Certificate (for relationship mapping)
    acm_certificate_arn: str | None = Field(
        default=None, description="ACM certificate ARN for HTTPS"
    )

    # WAF Configuration
    web_acl_id: str | None = Field(default=None, description="WAF Web ACL ID")

    # Structured Origin Details (for relationship mapping)
    origin_details: list[CloudFrontOrigin] = Field(
        default_factory=list, description="Detailed origin configurations"
    )


# CodeBuild Resources
class CodeBuildProject(BaseModel):
    """AWS CodeBuild Project."""

    name: str = Field(description="Project name")
    arn: str = Field(description="Project ARN")
    description: str | None = Field(default=None, description="Project description")
    source_type: str = Field(description="Source type (CODECOMMIT, GITHUB, S3, etc.)")
    source_location: str | None = Field(default=None, description="Source location")
    build_badge_url: str | None = Field(default=None, description="Build badge URL")
    environment_type: str | None = Field(default=None, description="Build environment type")
    environment_image: str | None = Field(default=None, description="Build environment image")
    compute_type: str | None = Field(default=None, description="Compute type")
    service_role: str | None = Field(default=None, description="Service role ARN")
    created: str | None = Field(default=None, description="Creation date")
    last_modified: str | None = Field(default=None, description="Last modified date")
    tags: dict[str, str] = Field(default_factory=dict, description="Resource tags")
    region: str = Field(description="AWS region")


# CodePipeline Resources
class CodePipeline(BaseModel):
    """AWS CodePipeline."""

    name: str = Field(description="Pipeline name")
    arn: str | None = Field(default=None, description="Pipeline ARN")
    role_arn: str | None = Field(default=None, description="Service role ARN")
    stage_count: int = Field(default=0, description="Number of stages")
    created: str | None = Field(default=None, description="Creation date")
    updated: str | None = Field(default=None, description="Last updated date")
    version: int | None = Field(default=None, description="Pipeline version")
    tags: dict[str, str] = Field(default_factory=dict, description="Resource tags")
    region: str = Field(description="AWS region")


# EC2 Instance Resources
class EC2Instance(BaseModel):
    """EC2 Instance."""

    instance_id: str = Field(description="Instance ID (i-xxx)")
    instance_type: str = Field(description="Instance type (t3.micro, etc.)")
    state: str = Field(description="Instance state (running, stopped, etc.)")
    private_ip: str | None = Field(default=None, description="Private IP address")
    public_ip: str | None = Field(default=None, description="Public IP address")
    vpc_id: str | None = Field(default=None, description="VPC ID")
    subnet_id: str | None = Field(default=None, description="Subnet ID")
    launch_time: str | None = Field(default=None, description="Launch timestamp")
    name: str | None = Field(default=None, description="Name tag value")
    platform: str | None = Field(default=None, description="Platform (windows or None for Linux)")
    image_id: str | None = Field(default=None, description="AMI ID")
    key_name: str | None = Field(default=None, description="SSH key pair name")
    security_groups: list[str] = Field(default_factory=list, description="Security group IDs")
    iam_instance_profile: str | None = Field(default=None, description="IAM instance profile ARN")
    tags: dict[str, str] = Field(default_factory=dict, description="Resource tags")
    arn: str = Field(description="Instance ARN")
    region: str = Field(description="AWS region")


# IAM Resources
class IAMRole(BaseModel):
    """IAM Role."""

    role_name: str = Field(description="Role name")
    role_id: str = Field(description="Role ID")
    arn: str = Field(description="Role ARN")
    path: str = Field(default="/", description="Role path")
    description: str | None = Field(default=None, description="Role description")
    create_date: str | None = Field(default=None, description="Creation date")
    max_session_duration: int = Field(default=3600, description="Max session duration in seconds")
    assume_role_policy_document: str | None = Field(
        default=None, description="Trust policy document (JSON)"
    )
    tags: dict[str, str] = Field(default_factory=dict, description="Resource tags")


class IAMPolicy(BaseModel):
    """IAM Policy (customer managed)."""

    policy_name: str = Field(description="Policy name")
    policy_id: str = Field(description="Policy ID")
    arn: str = Field(description="Policy ARN")
    path: str = Field(default="/", description="Policy path")
    description: str | None = Field(default=None, description="Policy description")
    create_date: str | None = Field(default=None, description="Creation date")
    update_date: str | None = Field(default=None, description="Last update date")
    attachment_count: int = Field(default=0, description="Number of entities attached")
    is_attachable: bool = Field(default=True, description="Whether policy is attachable")
    default_version_id: str | None = Field(default=None, description="Default version ID")


class IAMUser(BaseModel):
    """IAM User."""

    user_name: str = Field(description="User name")
    user_id: str = Field(description="User ID")
    arn: str = Field(description="User ARN")
    path: str = Field(default="/", description="User path")
    create_date: str | None = Field(default=None, description="Creation date")
    password_last_used: str | None = Field(default=None, description="Last password use timestamp")
    tags: dict[str, str] = Field(default_factory=dict, description="Resource tags")


class IAMGroup(BaseModel):
    """IAM Group."""

    group_name: str = Field(description="Group name")
    group_id: str = Field(description="Group ID")
    arn: str = Field(description="Group ARN")
    path: str = Field(default="/", description="Group path")
    create_date: str | None = Field(default=None, description="Creation date")


# CloudWatch Resources
class CloudWatchLogGroup(BaseModel):
    """CloudWatch Logs Log Group."""

    log_group_name: str = Field(description="Log group name")
    arn: str = Field(description="Log group ARN")
    creation_time: str | None = Field(default=None, description="Creation timestamp (ms)")
    retention_days: int | None = Field(default=None, description="Retention in days (null = never)")
    stored_bytes: int = Field(default=0, description="Stored data size in bytes")
    metric_filter_count: int = Field(default=0, description="Number of metric filters")
    kms_key_id: str | None = Field(default=None, description="KMS key for encryption")
    region: str = Field(description="AWS region")


class CloudWatchAlarm(BaseModel):
    """CloudWatch Alarm."""

    alarm_name: str = Field(description="Alarm name")
    alarm_arn: str = Field(description="Alarm ARN")
    alarm_description: str | None = Field(default=None, description="Alarm description")
    state_value: str = Field(description="Current state (OK, ALARM, INSUFFICIENT_DATA)")
    state_reason: str | None = Field(default=None, description="State reason")
    metric_name: str | None = Field(default=None, description="Metric name")
    namespace: str | None = Field(default=None, description="Metric namespace")
    statistic: str | None = Field(default=None, description="Statistic (Average, Sum, etc.)")
    period: int | None = Field(default=None, description="Period in seconds")
    evaluation_periods: int | None = Field(default=None, description="Evaluation periods")
    threshold: float | None = Field(default=None, description="Threshold value")
    comparison_operator: str | None = Field(default=None, description="Comparison operator")
    actions_enabled: bool = Field(default=True, description="Actions enabled")
    alarm_actions: list[str] = Field(default_factory=list, description="Actions on ALARM state")
    ok_actions: list[str] = Field(default_factory=list, description="Actions on OK state")
    region: str = Field(description="AWS region")


# ECR Resources
class ECRRepository(BaseModel):
    """ECR Repository."""

    repository_name: str = Field(description="Repository name")
    arn: str = Field(description="Repository ARN")
    uri: str = Field(description="Repository URI for docker push/pull")
    registry_id: str = Field(description="AWS account ID of the registry")
    created_at: datetime | None = Field(default=None, description="Creation timestamp")
    image_count: int = Field(default=0, description="Number of images in repository")
    image_tag_mutability: str = Field(
        default="MUTABLE", description="Image tag mutability (MUTABLE or IMMUTABLE)"
    )
    scan_on_push: bool = Field(
        default=False, description="Whether images are scanned on push"
    )
    region: str = Field(description="AWS region")


# Elastic Load Balancing Resources
class ApplicationLoadBalancer(BaseModel):
    """Application Load Balancer (ALB)."""

    name: str = Field(description="Load balancer name")
    arn: str = Field(description="Load balancer ARN")
    dns_name: str = Field(description="DNS name")
    scheme: str = Field(description="Scheme (internet-facing or internal)")
    vpc_id: str = Field(description="VPC ID")
    state: str = Field(description="State (active, provisioning, etc.)")
    type: str = Field(default="application", description="Load balancer type")
    created_time: str | None = Field(default=None, description="Creation timestamp")
    availability_zones: list[str] = Field(default_factory=list, description="Availability zones")
    security_groups: list[str] = Field(default_factory=list, description="Security group IDs")
    ip_address_type: str | None = Field(default=None, description="IP address type (ipv4, dualstack)")
    region: str = Field(description="AWS region")


class NetworkLoadBalancer(BaseModel):
    """Network Load Balancer (NLB)."""

    name: str = Field(description="Load balancer name")
    arn: str = Field(description="Load balancer ARN")
    dns_name: str = Field(description="DNS name")
    scheme: str = Field(description="Scheme (internet-facing or internal)")
    vpc_id: str = Field(description="VPC ID")
    state: str = Field(description="State (active, provisioning, etc.)")
    type: str = Field(default="network", description="Load balancer type")
    created_time: str | None = Field(default=None, description="Creation timestamp")
    availability_zones: list[str] = Field(default_factory=list, description="Availability zones")
    ip_address_type: str | None = Field(default=None, description="IP address type (ipv4, dualstack)")
    region: str = Field(description="AWS region")


class ClassicLoadBalancer(BaseModel):
    """Classic Load Balancer (ELB)."""

    name: str = Field(description="Load balancer name")
    dns_name: str = Field(description="DNS name")
    scheme: str = Field(description="Scheme (internet-facing or internal)")
    vpc_id: str | None = Field(default=None, description="VPC ID (None for EC2-Classic)")
    created_time: str | None = Field(default=None, description="Creation timestamp")
    availability_zones: list[str] = Field(default_factory=list, description="Availability zones")
    subnets: list[str] = Field(default_factory=list, description="Subnet IDs")
    security_groups: list[str] = Field(default_factory=list, description="Security group IDs")
    instances: list[str] = Field(default_factory=list, description="Registered instance IDs")
    health_check_target: str | None = Field(default=None, description="Health check target")
    region: str = Field(description="AWS region")


# Auto Scaling Resources
class AutoScalingGroup(BaseModel):
    """Auto Scaling Group."""

    name: str = Field(description="Auto Scaling group name")
    arn: str = Field(description="Auto Scaling group ARN")
    launch_template_id: str | None = Field(default=None, description="Launch template ID")
    launch_template_name: str | None = Field(default=None, description="Launch template name")
    launch_configuration_name: str | None = Field(default=None, description="Launch configuration name")
    min_size: int = Field(description="Minimum size")
    max_size: int = Field(description="Maximum size")
    desired_capacity: int = Field(description="Desired capacity")
    default_cooldown: int | None = Field(default=None, description="Default cooldown in seconds")
    availability_zones: list[str] = Field(default_factory=list, description="Availability zones")
    vpc_zone_identifier: str | None = Field(default=None, description="Subnet IDs (comma-separated)")
    health_check_type: str = Field(description="Health check type (EC2 or ELB)")
    health_check_grace_period: int | None = Field(default=None, description="Health check grace period")
    target_group_arns: list[str] = Field(default_factory=list, description="Target group ARNs")
    load_balancer_names: list[str] = Field(default_factory=list, description="Classic LB names")
    instances: list[str] = Field(default_factory=list, description="Instance IDs")
    created_time: str | None = Field(default=None, description="Creation timestamp")
    tags: dict[str, str] = Field(default_factory=dict, description="Resource tags")
    region: str = Field(description="AWS region")


# =============================================================================
# Relationship Mapping Models
# =============================================================================


class ResourceReference(BaseModel):
    """Reference to an AWS resource."""

    resource_type: str = Field(description="Resource type (e.g., 'lambda', 'vpc', 'iam_role')")
    resource_id: str = Field(description="Resource identifier (name, ID, or ARN)")
    arn: str | None = Field(default=None, description="Full ARN if available")


class RelationshipEdge(BaseModel):
    """Directed edge representing a relationship between resources."""

    relationship_type: str = Field(
        description="Relationship type (deployed_in, uses_role, uses_security_group, etc.)"
    )
    target: ResourceReference = Field(description="Target resource of this relationship")


class RelationshipGraph(BaseModel):
    """Graph of relationships between AWS resources.

    The graph stores directed edges from source resources to target resources.
    Each source is identified by a key in format "type:id" (e.g., "lambda:my-func").

    Relationship types:
    - deployed_in: Resource runs in VPC (Lambda → VPC)
    - uses_role: Uses IAM role (Lambda → IAM Role)
    - uses_security_group: Attached to security group (EC2 → SG)
    - uses_subnet: Deployed in subnet (Lambda → Subnet)
    - encrypted_with: Uses KMS key for encryption (RDS → KMS)
    - targets: Points to resource (Route53 → ALB)
    - manages: Controls lifecycle (ASG → EC2)
    - uses_certificate: Uses ACM certificate (CloudFront → ACM)
    - member_of: Belongs to cluster (RDS Instance → RDS Cluster)
    - uses_target_group: Routes to target group (ECS Service → Target Group)
    - logs_to: Sends logs to (Step Functions → CloudWatch Logs)
    """

    edges: dict[str, list[RelationshipEdge]] = Field(
        default_factory=dict, description="Source key -> list of relationship edges"
    )
    reverse_edges: dict[str, list[str]] = Field(
        default_factory=dict, description="Target key -> list of source keys"
    )

    def _make_key(self, resource_type: str, resource_id: str) -> str:
        """Create a canonical key for a resource."""
        return f"{resource_type}:{resource_id}"

    def add_relationship(
        self,
        source_type: str,
        source_id: str,
        relationship_type: str,
        target_type: str,
        target_id: str,
        target_arn: str | None = None,
    ) -> None:
        """Add a relationship between two resources.

        Args:
            source_type: Type of source resource (e.g., 'lambda')
            source_id: ID of source resource (e.g., 'my-function')
            relationship_type: Type of relationship (e.g., 'deployed_in')
            target_type: Type of target resource (e.g., 'vpc')
            target_id: ID of target resource (e.g., 'vpc-123')
            target_arn: Optional ARN of target resource
        """
        source_key = self._make_key(source_type, source_id)
        target_key = self._make_key(target_type, target_id)

        # Create edge
        edge = RelationshipEdge(
            relationship_type=relationship_type,
            target=ResourceReference(
                resource_type=target_type,
                resource_id=target_id,
                arn=target_arn,
            ),
        )

        # Add forward edge
        if source_key not in self.edges:
            self.edges[source_key] = []
        self.edges[source_key].append(edge)

        # Add reverse edge
        if target_key not in self.reverse_edges:
            self.reverse_edges[target_key] = []
        if source_key not in self.reverse_edges[target_key]:
            self.reverse_edges[target_key].append(source_key)

    def get_relationships(self, resource_type: str, resource_id: str) -> list[RelationshipEdge]:
        """Get all relationships from a resource."""
        key = self._make_key(resource_type, resource_id)
        return self.edges.get(key, [])

    def get_resources_targeting(self, resource_type: str, resource_id: str) -> list[str]:
        """Get all resources that have a relationship to this resource."""
        key = self._make_key(resource_type, resource_id)
        return self.reverse_edges.get(key, [])

    def get_resources_in_vpc(self, vpc_id: str) -> list[str]:
        """Get all resources deployed in a specific VPC."""
        return self.get_resources_targeting("vpc", vpc_id)

    def get_resources_using_role(self, role_name: str) -> list[str]:
        """Get all resources using a specific IAM role."""
        return self.get_resources_targeting("iam_role", role_name)

    def get_resources_in_security_group(self, sg_id: str) -> list[str]:
        """Get all resources attached to a security group."""
        return self.get_resources_targeting("security_group", sg_id)


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
    route53_domains: list[Route53Domain] = Field(
        default_factory=list, description="Route53 registered domains"
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

    # ECR Resources
    ecr_repositories: list[ECRRepository] = Field(
        default_factory=list, description="ECR repositories in the account"
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

    # Cognito Resources
    cognito_user_pools: list[CognitoUserPool] = Field(
        default_factory=list, description="Cognito User Pools"
    )
    cognito_identity_pools: list[CognitoIdentityPool] = Field(
        default_factory=list, description="Cognito Identity Pools"
    )

    # CloudFront Resources
    cloudfront_distributions: list[CloudFrontDistribution] = Field(
        default_factory=list, description="CloudFront distributions"
    )

    # CodeBuild Resources
    codebuild_projects: list[CodeBuildProject] = Field(
        default_factory=list, description="CodeBuild projects"
    )

    # CodePipeline Resources
    codepipelines: list[CodePipeline] = Field(
        default_factory=list, description="CodePipeline pipelines"
    )

    # EC2 Instances
    ec2_instances: list[EC2Instance] = Field(
        default_factory=list, description="EC2 instances in the account"
    )

    # IAM Resources
    iam_roles: list[IAMRole] = Field(
        default_factory=list, description="IAM roles in the account"
    )
    iam_policies: list[IAMPolicy] = Field(
        default_factory=list, description="IAM customer managed policies"
    )
    iam_users: list[IAMUser] = Field(
        default_factory=list, description="IAM users in the account"
    )
    iam_groups: list[IAMGroup] = Field(
        default_factory=list, description="IAM groups in the account"
    )

    # CloudWatch Resources
    cloudwatch_log_groups: list[CloudWatchLogGroup] = Field(
        default_factory=list, description="CloudWatch log groups"
    )
    cloudwatch_alarms: list[CloudWatchAlarm] = Field(
        default_factory=list, description="CloudWatch alarms"
    )

    # Load Balancers
    application_load_balancers: list[ApplicationLoadBalancer] = Field(
        default_factory=list, description="Application Load Balancers"
    )
    network_load_balancers: list[NetworkLoadBalancer] = Field(
        default_factory=list, description="Network Load Balancers"
    )
    classic_load_balancers: list[ClassicLoadBalancer] = Field(
        default_factory=list, description="Classic Load Balancers"
    )

    # Auto Scaling
    auto_scaling_groups: list[AutoScalingGroup] = Field(
        default_factory=list, description="Auto Scaling Groups"
    )

    # Standalone network resources (also nested in VPCs, but available top-level for flat queries)
    internet_gateways: list[InternetGateway] = Field(
        default_factory=list, description="Internet Gateways in the account"
    )
    nat_gateways: list[NATGateway] = Field(
        default_factory=list, description="NAT Gateways in the account"
    )
    subnets: list[Subnet] = Field(
        default_factory=list, description="Subnets in the account"
    )

    # Route53 Records (individual DNS records within zones)
    route53_records: list[Route53Record] = Field(
        default_factory=list, description="Route53 DNS records across all zones"
    )

    # SSO Resources
    sso_instances: list[SSOInstance] = Field(
        default_factory=list, description="AWS SSO instances (requires sso-admin permissions)"
    )

    # Relationship Graph (built after discovery)
    relationships: RelationshipGraph = Field(
        default_factory=RelationshipGraph,
        description="Graph of relationships between resources",
    )

    def build_relationships(self) -> None:
        """Build the relationship graph from discovered resources.

        Call this method after discovery is complete to populate the relationships field.
        The graph is built from resource fields like vpc_id, execution_role_arn, etc.
        """
        graph = RelationshipGraph()

        # Lambda functions
        for func in self.lambda_functions:
            if func.vpc_id:
                graph.add_relationship(
                    "lambda", func.function_name, "deployed_in", "vpc", func.vpc_id
                )
            for subnet_id in func.subnet_ids:
                graph.add_relationship(
                    "lambda", func.function_name, "uses_subnet", "subnet", subnet_id
                )
            for sg_id in func.security_group_ids:
                graph.add_relationship(
                    "lambda", func.function_name, "uses_security_group", "security_group", sg_id
                )
            if func.execution_role_arn:
                # Extract role name from ARN
                role_name = func.execution_role_arn.split("/")[-1]
                graph.add_relationship(
                    "lambda",
                    func.function_name,
                    "uses_role",
                    "iam_role",
                    role_name,
                    func.execution_role_arn,
                )

        # RDS Instances
        for db in self.rds_instances:
            if db.vpc_id:
                graph.add_relationship(
                    "rds_instance", db.db_instance_identifier, "deployed_in", "vpc", db.vpc_id
                )
            for sg_id in db.security_group_ids:
                graph.add_relationship(
                    "rds_instance",
                    db.db_instance_identifier,
                    "uses_security_group",
                    "security_group",
                    sg_id,
                )
            if db.kms_key_id:
                graph.add_relationship(
                    "rds_instance",
                    db.db_instance_identifier,
                    "encrypted_with",
                    "kms_key",
                    db.kms_key_id,
                )
            if db.db_cluster_identifier:
                graph.add_relationship(
                    "rds_instance",
                    db.db_instance_identifier,
                    "member_of",
                    "rds_cluster",
                    db.db_cluster_identifier,
                )

        # RDS Clusters
        for cluster in self.rds_clusters:
            if cluster.vpc_id:
                graph.add_relationship(
                    "rds_cluster", cluster.cluster_identifier, "deployed_in", "vpc", cluster.vpc_id
                )
            for sg_id in cluster.security_group_ids:
                graph.add_relationship(
                    "rds_cluster",
                    cluster.cluster_identifier,
                    "uses_security_group",
                    "security_group",
                    sg_id,
                )
            if cluster.kms_key_id:
                graph.add_relationship(
                    "rds_cluster",
                    cluster.cluster_identifier,
                    "encrypted_with",
                    "kms_key",
                    cluster.kms_key_id,
                )

        # EC2 Instances
        for inst in self.ec2_instances:
            if inst.vpc_id:
                graph.add_relationship(
                    "ec2", inst.instance_id, "deployed_in", "vpc", inst.vpc_id
                )
            if inst.subnet_id:
                graph.add_relationship(
                    "ec2", inst.instance_id, "uses_subnet", "subnet", inst.subnet_id
                )
            for sg_id in inst.security_groups:
                graph.add_relationship(
                    "ec2", inst.instance_id, "uses_security_group", "security_group", sg_id
                )
            if inst.iam_instance_profile:
                graph.add_relationship(
                    "ec2",
                    inst.instance_id,
                    "uses_role",
                    "iam_instance_profile",
                    inst.iam_instance_profile,
                )

        # ECS Services
        for svc in self.ecs_services:
            if svc.vpc_id:
                graph.add_relationship(
                    "ecs_service", svc.service_name, "deployed_in", "vpc", svc.vpc_id
                )
            for subnet_id in svc.subnet_ids:
                graph.add_relationship(
                    "ecs_service", svc.service_name, "uses_subnet", "subnet", subnet_id
                )
            for sg_id in svc.security_group_ids:
                graph.add_relationship(
                    "ecs_service",
                    svc.service_name,
                    "uses_security_group",
                    "security_group",
                    sg_id,
                )
            for tg_arn in svc.load_balancer_target_groups:
                graph.add_relationship(
                    "ecs_service",
                    svc.service_name,
                    "uses_target_group",
                    "target_group",
                    tg_arn,
                )

        # EKS Clusters
        for cluster in self.eks_clusters:
            if cluster.vpc_id:
                graph.add_relationship(
                    "eks_cluster", cluster.cluster_name, "deployed_in", "vpc", cluster.vpc_id
                )
            for subnet_id in cluster.subnet_ids:
                graph.add_relationship(
                    "eks_cluster", cluster.cluster_name, "uses_subnet", "subnet", subnet_id
                )
            for sg_id in cluster.security_group_ids:
                graph.add_relationship(
                    "eks_cluster",
                    cluster.cluster_name,
                    "uses_security_group",
                    "security_group",
                    sg_id,
                )
            if cluster.role_arn:
                role_name = cluster.role_arn.split("/")[-1]
                graph.add_relationship(
                    "eks_cluster",
                    cluster.cluster_name,
                    "uses_role",
                    "iam_role",
                    role_name,
                    cluster.role_arn,
                )

        # EKS Node Groups
        for ng in self.eks_node_groups:
            for subnet_id in ng.subnet_ids:
                graph.add_relationship(
                    "eks_nodegroup", ng.nodegroup_name, "uses_subnet", "subnet", subnet_id
                )
            if ng.node_role_arn:
                role_name = ng.node_role_arn.split("/")[-1]
                graph.add_relationship(
                    "eks_nodegroup",
                    ng.nodegroup_name,
                    "uses_role",
                    "iam_role",
                    role_name,
                    ng.node_role_arn,
                )

        # ALBs
        for alb in self.application_load_balancers:
            if alb.vpc_id:
                graph.add_relationship("alb", alb.name, "deployed_in", "vpc", alb.vpc_id)
            for sg_id in alb.security_groups:
                graph.add_relationship(
                    "alb", alb.name, "uses_security_group", "security_group", sg_id
                )

        # CloudFront Distributions
        for dist in self.cloudfront_distributions:
            if dist.acm_certificate_arn:
                graph.add_relationship(
                    "cloudfront",
                    dist.id,
                    "uses_certificate",
                    "acm_certificate",
                    dist.acm_certificate_arn,
                )

        # Step Functions State Machines
        for sm in self.state_machines:
            if sm.role_arn:
                role_name = sm.role_arn.split("/")[-1]
                graph.add_relationship(
                    "state_machine", sm.name, "uses_role", "iam_role", role_name, sm.role_arn
                )
            if sm.log_group_arn:
                graph.add_relationship(
                    "state_machine", sm.name, "logs_to", "log_group", sm.log_group_arn
                )

        # Auto Scaling Groups
        for asg in self.auto_scaling_groups:
            for inst_id in asg.instances:
                graph.add_relationship("asg", asg.name, "manages", "ec2", inst_id)
            for tg_arn in asg.target_group_arns:
                graph.add_relationship(
                    "asg", asg.name, "uses_target_group", "target_group", tg_arn
                )

        self.relationships = graph

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
