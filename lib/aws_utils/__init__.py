"""AWS Utils - Resource discovery and inventory library.

This library provides AWS resource discovery capabilities for:
- EC2: VPCs, subnets, internet gateways, NAT gateways, elastic IPs
- S3: Bucket listing
- SQS: Queue listing
- SNS: Topic listing
- SES: Identity listing
- Organizations: Account and OU hierarchy discovery

Usage:
    from aws_utils import discover_account_inventory, save_inventory

    # Discover all resources for an account
    inventory = discover_account_inventory(profile_name="sandbox")

    # Save to inventory file
    save_inventory(org_id="o-xxx", ou_path="dev-accounts", alias="sandbox", data=inventory)
"""

from aws_utils.core.session import create_session, get_default_region
from aws_utils.core.schemas import (
    AccountInventory,
    ElasticIP,
    InternetGateway,
    NATGateway,
    S3Bucket,
    SESIdentity,
    SNSTopic,
    SQSQueue,
    Subnet,
    VPC,
)
from aws_utils.inventory.reader import load_inventory, load_accounts_config
from aws_utils.inventory.writer import save_inventory, save_accounts_config
from aws_utils.services.ec2 import (
    discover_vpcs,
    discover_elastic_ips,
)
from aws_utils.services.s3 import discover_s3_buckets
from aws_utils.services.sqs import discover_sqs_queues
from aws_utils.services.sns import discover_sns_topics
from aws_utils.services.ses import discover_ses_identities
from aws_utils.services.organizations import (
    discover_organization,
    get_organization_id,
)

__all__ = [
    # Session
    "create_session",
    "get_default_region",
    # Schemas
    "AccountInventory",
    "VPC",
    "Subnet",
    "InternetGateway",
    "NATGateway",
    "ElasticIP",
    "S3Bucket",
    "SQSQueue",
    "SNSTopic",
    "SESIdentity",
    # Inventory I/O
    "load_inventory",
    "save_inventory",
    "load_accounts_config",
    "save_accounts_config",
    # Discovery
    "discover_vpcs",
    "discover_elastic_ips",
    "discover_s3_buckets",
    "discover_sqs_queues",
    "discover_sns_topics",
    "discover_ses_identities",
    "discover_organization",
    "get_organization_id",
]

__version__ = "1.0.0"
