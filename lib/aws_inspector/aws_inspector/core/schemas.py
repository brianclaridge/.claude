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

    def to_dict(self) -> dict:
        """Convert to dictionary for YAML serialization."""
        data = self.model_dump()
        # Convert datetime to ISO string
        data["discovered_at"] = self.discovered_at.isoformat()
        for bucket in data.get("s3_buckets", []):
            if bucket.get("created"):
                bucket["created"] = bucket["created"].isoformat()
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
