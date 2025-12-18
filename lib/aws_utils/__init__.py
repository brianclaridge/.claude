"""AWS Utils - Resource discovery and inventory library.

This library provides AWS resource discovery capabilities for:
- EC2: VPCs, subnets, internet gateways, NAT gateways, elastic IPs
- S3: Bucket listing
- SQS: Queue listing
- SNS: Topic listing
- SES: Identity listing
- Lambda: Function listing
- RDS: Instance and cluster listing
- Route53: Hosted zones and records
- DynamoDB: Table listing
- Step Functions: State machines and activities
- SSO: Instance and account discovery
- Organizations: Account and OU hierarchy discovery
- ECS: Clusters, services, and task definitions
- EKS: Clusters, node groups, and Fargate profiles
- ACM: Certificate management

Usage:
    from aws_utils import discover_account_inventory, save_inventory

    # Discover all resources for an account
    inventory = discover_account_inventory(profile_name="sandbox")

    # Save to inventory file
    save_inventory(org_id="o-xxx", ou_path="dev-accounts", alias="sandbox", data=inventory)
"""

from aws_utils.core.schemas import (
    VPC,
    AccountInventory,
    ACMCertificate,
    DynamoDBTable,
    ECSCluster,
    ECSService,
    ECSTaskDefinition,
    EKSCluster,
    EKSFargateProfile,
    EKSNodeGroup,
    ElasticIP,
    InternetGateway,
    LambdaFunction,
    NATGateway,
    RDSCluster,
    RDSInstance,
    Route53Record,
    Route53Zone,
    S3Bucket,
    SESIdentity,
    SFNActivity,
    SNSTopic,
    SQSQueue,
    SSOAccount,
    SSOInstance,
    StateMachine,
    Subnet,
)
from aws_utils.core.session import create_session, get_default_region
from aws_utils.inventory.reader import load_accounts_config, load_inventory
from aws_utils.inventory.writer import save_accounts_config, save_inventory
from aws_utils.services.acm import discover_acm_certificates
from aws_utils.services.dynamodb import discover_dynamodb_tables
from aws_utils.services.ec2 import (
    discover_elastic_ips,
    discover_vpcs,
)
from aws_utils.services.ecs import (
    discover_all_ecs_services,
    discover_ecs_clusters,
    discover_ecs_services,
    discover_ecs_task_definitions,
)
from aws_utils.services.eks import (
    discover_all_eks_fargate_profiles,
    discover_all_eks_node_groups,
    discover_eks_clusters,
    discover_eks_fargate_profiles,
    discover_eks_node_groups,
)
from aws_utils.services.lambda_svc import discover_lambda_functions
from aws_utils.services.organizations import (
    discover_organization,
    get_organization_id,
)
from aws_utils.services.rds import discover_rds_clusters, discover_rds_instances
from aws_utils.services.route53 import (
    discover_all_route53_records,
    discover_route53_records,
    discover_route53_zones,
)
from aws_utils.services.s3 import discover_s3_buckets
from aws_utils.services.ses import discover_ses_identities
from aws_utils.services.sns import discover_sns_topics
from aws_utils.services.sqs import discover_sqs_queues
from aws_utils.services.sso import (
    DeviceAuthResult,
    discover_account_roles,
    discover_sso_accounts,
    discover_sso_instances,
    poll_for_token,
    start_device_authorization,
)
from aws_utils.services.stepfunctions import (
    discover_sfn_activities,
    discover_state_machines,
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
    "LambdaFunction",
    "RDSInstance",
    "RDSCluster",
    "Route53Zone",
    "Route53Record",
    "DynamoDBTable",
    "StateMachine",
    "SFNActivity",
    "SSOInstance",
    "SSOAccount",
    "ECSCluster",
    "ECSService",
    "ECSTaskDefinition",
    "EKSCluster",
    "EKSNodeGroup",
    "EKSFargateProfile",
    "ACMCertificate",
    # Inventory I/O
    "load_inventory",
    "save_inventory",
    "load_accounts_config",
    "save_accounts_config",
    # Discovery - EC2
    "discover_vpcs",
    "discover_elastic_ips",
    # Discovery - S3
    "discover_s3_buckets",
    # Discovery - SQS
    "discover_sqs_queues",
    # Discovery - SNS
    "discover_sns_topics",
    # Discovery - SES
    "discover_ses_identities",
    # Discovery - Lambda
    "discover_lambda_functions",
    # Discovery - RDS
    "discover_rds_instances",
    "discover_rds_clusters",
    # Discovery - Route53
    "discover_route53_zones",
    "discover_route53_records",
    "discover_all_route53_records",
    # Discovery - DynamoDB
    "discover_dynamodb_tables",
    # Discovery - Step Functions
    "discover_state_machines",
    "discover_sfn_activities",
    # Discovery - SSO
    "discover_sso_instances",
    "discover_sso_accounts",
    "discover_account_roles",
    "start_device_authorization",
    "poll_for_token",
    "DeviceAuthResult",
    # Discovery - Organizations
    "discover_organization",
    "get_organization_id",
    # Discovery - ECS
    "discover_ecs_clusters",
    "discover_ecs_services",
    "discover_all_ecs_services",
    "discover_ecs_task_definitions",
    # Discovery - EKS
    "discover_eks_clusters",
    "discover_eks_node_groups",
    "discover_all_eks_node_groups",
    "discover_eks_fargate_profiles",
    "discover_all_eks_fargate_profiles",
    # Discovery - ACM
    "discover_acm_certificates",
]

__version__ = "1.0.0"
