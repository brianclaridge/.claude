"""AWS service discovery modules."""

from aws_utils.services.ec2 import (
    discover_vpcs,
    discover_elastic_ips,
    discover_internet_gateways,
    discover_nat_gateways,
    discover_subnets,
)
from aws_utils.services.s3 import discover_s3_buckets
from aws_utils.services.sqs import discover_sqs_queues
from aws_utils.services.sns import discover_sns_topics
from aws_utils.services.ses import discover_ses_identities
from aws_utils.services.organizations import (
    discover_organization,
    get_organization_id,
    collect_all_accounts,
)

__all__ = [
    # EC2
    "discover_vpcs",
    "discover_elastic_ips",
    "discover_internet_gateways",
    "discover_nat_gateways",
    "discover_subnets",
    # S3
    "discover_s3_buckets",
    # SQS
    "discover_sqs_queues",
    # SNS
    "discover_sns_topics",
    # SES
    "discover_ses_identities",
    # Organizations
    "discover_organization",
    "get_organization_id",
    "collect_all_accounts",
]
