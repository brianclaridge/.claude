"""AWS Organizations and resource discovery using aws_utils library."""

import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from loguru import logger

# Add aws_utils to path
# Path: .claude/skills/aws-login/lib/discovery.py -> .claude/lib/aws_utils
_lib_path = Path(__file__).parent.parent.parent.parent / "lib" / "aws_utils"
if str(_lib_path) not in sys.path:
    sys.path.insert(0, str(_lib_path))

from aws_utils.core.schemas import AccountInventory
from aws_utils.services.ec2 import discover_vpcs, discover_elastic_ips
from aws_utils.services.s3 import discover_s3_buckets
from aws_utils.services.sqs import discover_sqs_queues
from aws_utils.services.sns import discover_sns_topics
from aws_utils.services.ses import discover_ses_identities
from aws_utils.services.organizations import (
    discover_organization as _discover_org,
    get_organization_id,
    collect_all_accounts,
)
from aws_utils.inventory.writer import save_inventory, get_relative_inventory_path

# Phase A: Additional service imports (16 services)
from aws_utils.services.lambda_svc import discover_lambda_functions
from aws_utils.services.rds import discover_rds_instances, discover_rds_clusters
from aws_utils.services.dynamodb import discover_dynamodb_tables
from aws_utils.services.route53 import discover_route53_zones, discover_route53_domains
from aws_utils.services.ecs import (
    discover_ecs_clusters,
    discover_all_ecs_services,
    discover_ecs_task_definitions,
)
from aws_utils.services.eks import (
    discover_eks_clusters,
    discover_all_eks_node_groups,
    discover_all_eks_fargate_profiles,
)
from aws_utils.services.stepfunctions import discover_state_machines, discover_sfn_activities
from aws_utils.services.acm import discover_acm_certificates
from aws_utils.services.secrets_manager import discover_secrets
from aws_utils.services.cognito import discover_user_pools, discover_identity_pools
from aws_utils.services.api_gateway import discover_rest_apis, discover_v2_apis
from aws_utils.services.cloudfront import discover_distributions
from aws_utils.services.codebuild import discover_codebuild_projects
from aws_utils.services.codepipeline import discover_pipelines

# Phase B-D: EC2 Instances, IAM, CloudWatch, Load Balancers, Auto Scaling
from aws_utils.services.ec2 import discover_ec2_instances
from aws_utils.services.iam import (
    discover_iam_roles,
    discover_iam_policies,
    discover_iam_users,
    discover_iam_groups,
)
from aws_utils.services.cloudwatch import discover_log_groups, discover_alarms
from aws_utils.services.elbv2 import (
    discover_application_load_balancers,
    discover_network_load_balancers,
)
from aws_utils.services.elb import discover_classic_load_balancers
from aws_utils.services.autoscaling import discover_auto_scaling_groups

from .config import get_default_region


def discover_organization(profile_name: str = "root") -> tuple[str, dict[str, Any]]:
    """Discover organization hierarchy and return org_id + tree.

    Args:
        profile_name: AWS profile with Organizations access

    Returns:
        Tuple of (organization_id, organization_tree)
    """
    tree = _discover_org(profile_name)
    org_id = get_organization_id(profile_name) or tree.get("organization_id", "unknown")

    return org_id, tree


def discover_account_inventory(
    profile_name: str,
    region: str | None = None,
    skip_resources: bool = False,
) -> AccountInventory:
    """Discover full inventory for an account.

    Args:
        profile_name: AWS CLI profile name
        region: AWS region
        skip_resources: If True, skip extended resource discovery (only VPCs/EIPs)

    Returns:
        AccountInventory with all discovered resources
    """
    region = region or get_default_region()

    # Always discover VPCs (core networking)
    vpcs = discover_vpcs(profile_name, region)
    eips = discover_elastic_ips(profile_name, region)

    # Initialize all resource lists
    s3_buckets = []
    sqs_queues = []
    sns_topics = []
    ses_identities = []
    lambda_functions = []
    rds_instances = []
    rds_clusters = []
    dynamodb_tables = []
    route53_zones = []
    route53_domains = []
    state_machines = []
    sfn_activities = []
    ecs_clusters = []
    ecs_services = []
    ecs_task_definitions = []
    eks_clusters = []
    eks_node_groups = []
    eks_fargate_profiles = []
    acm_certificates = []
    secrets = []
    cognito_user_pools = []
    cognito_identity_pools = []
    api_gateway_rest_apis = []
    api_gateway_v2_apis = []
    cloudfront_distributions = []
    codebuild_projects = []
    codepipelines = []
    # Phase B-D: New services
    ec2_instances = []
    iam_roles = []
    iam_policies = []
    iam_users = []
    iam_groups = []
    cloudwatch_log_groups = []
    cloudwatch_alarms = []
    application_load_balancers = []
    network_load_balancers = []
    classic_load_balancers = []
    auto_scaling_groups = []

    if not skip_resources:
        # Original services
        s3_buckets = discover_s3_buckets(profile_name, region)
        sqs_queues = discover_sqs_queues(profile_name, region)
        sns_topics = discover_sns_topics(profile_name, region)
        ses_identities = discover_ses_identities(profile_name, region)

        # Compute
        lambda_functions = discover_lambda_functions(profile_name, region)

        # Database
        rds_instances = discover_rds_instances(profile_name, region)
        rds_clusters = discover_rds_clusters(profile_name, region)
        dynamodb_tables = discover_dynamodb_tables(profile_name, region)

        # DNS (Route53 is global but we pass region for session)
        route53_zones = discover_route53_zones(profile_name, region)
        route53_domains = discover_route53_domains(profile_name, region)

        # Step Functions
        state_machines = discover_state_machines(profile_name, region)
        sfn_activities = discover_sfn_activities(profile_name, region)

        # Container orchestration - ECS
        ecs_clusters = discover_ecs_clusters(profile_name, region)
        ecs_services = discover_all_ecs_services(profile_name, region)
        ecs_task_definitions = discover_ecs_task_definitions(profile_name, region)

        # Container orchestration - EKS
        eks_clusters = discover_eks_clusters(profile_name, region)
        eks_node_groups = discover_all_eks_node_groups(profile_name, region)
        eks_fargate_profiles = discover_all_eks_fargate_profiles(profile_name, region)

        # Security & Certificates
        acm_certificates = discover_acm_certificates(profile_name, region)
        secrets = discover_secrets(profile_name, region)

        # Identity
        cognito_user_pools = discover_user_pools(profile_name, region)
        cognito_identity_pools = discover_identity_pools(profile_name, region)

        # API Gateway
        api_gateway_rest_apis = discover_rest_apis(profile_name, region)
        api_gateway_v2_apis = discover_v2_apis(profile_name, region)

        # CDN (CloudFront is global)
        cloudfront_distributions = discover_distributions(profile_name, region)

        # CI/CD
        codebuild_projects = discover_codebuild_projects(profile_name, region)
        codepipelines = discover_pipelines(profile_name, region)

        # Phase B: EC2 Instances
        ec2_instances = discover_ec2_instances(profile_name, region)

        # Phase B: IAM (global service)
        iam_roles = discover_iam_roles(profile_name, region)
        iam_policies = discover_iam_policies(profile_name, region)
        iam_users = discover_iam_users(profile_name, region)
        iam_groups = discover_iam_groups(profile_name, region)

        # Phase C: CloudWatch
        cloudwatch_log_groups = discover_log_groups(profile_name, region)
        cloudwatch_alarms = discover_alarms(profile_name, region)

        # Phase D: Load Balancers
        application_load_balancers = discover_application_load_balancers(profile_name, region)
        network_load_balancers = discover_network_load_balancers(profile_name, region)
        classic_load_balancers = discover_classic_load_balancers(profile_name, region)

        # Phase D: Auto Scaling
        auto_scaling_groups = discover_auto_scaling_groups(profile_name, region)

    return AccountInventory(
        account_id="",  # Set by caller
        account_alias=profile_name,
        discovered_at=datetime.utcnow(),
        region=region,
        vpcs=vpcs,
        elastic_ips=eips,
        s3_buckets=s3_buckets,
        sqs_queues=sqs_queues,
        sns_topics=sns_topics,
        ses_identities=ses_identities,
        lambda_functions=lambda_functions,
        rds_instances=rds_instances,
        rds_clusters=rds_clusters,
        dynamodb_tables=dynamodb_tables,
        route53_zones=route53_zones,
        route53_domains=route53_domains,
        state_machines=state_machines,
        sfn_activities=sfn_activities,
        ecs_clusters=ecs_clusters,
        ecs_services=ecs_services,
        ecs_task_definitions=ecs_task_definitions,
        eks_clusters=eks_clusters,
        eks_node_groups=eks_node_groups,
        eks_fargate_profiles=eks_fargate_profiles,
        acm_certificates=acm_certificates,
        secrets=secrets,
        cognito_user_pools=cognito_user_pools,
        cognito_identity_pools=cognito_identity_pools,
        api_gateway_rest_apis=api_gateway_rest_apis,
        api_gateway_v2_apis=api_gateway_v2_apis,
        cloudfront_distributions=cloudfront_distributions,
        codebuild_projects=codebuild_projects,
        codepipelines=codepipelines,
        # Phase B-D: New services
        ec2_instances=ec2_instances,
        iam_roles=iam_roles,
        iam_policies=iam_policies,
        iam_users=iam_users,
        iam_groups=iam_groups,
        cloudwatch_log_groups=cloudwatch_log_groups,
        cloudwatch_alarms=cloudwatch_alarms,
        application_load_balancers=application_load_balancers,
        network_load_balancers=network_load_balancers,
        classic_load_balancers=classic_load_balancers,
        auto_scaling_groups=auto_scaling_groups,
    )


def enrich_and_save_inventory(
    org_id: str,
    tree: dict[str, Any],
    profile_creator: Callable | None = None,
    max_workers: int = 8,
    skip_resources: bool = False,
) -> dict[str, dict[str, Any]]:
    """Discover inventory for all accounts and save to files.

    Args:
        org_id: Organization ID
        tree: Organization tree from discover_organization
        profile_creator: Function to create AWS CLI profiles
        max_workers: Max parallel discovery threads
        skip_resources: If True, skip S3/SQS/SNS/SES

    Returns:
        Dict of alias -> account config for accounts.yml
    """
    accounts = list(collect_all_accounts(tree))
    total = len(accounts)
    management_account_id = tree.get("management_account_id", "")

    if not accounts:
        return {}

    # Create profiles first (sequential)
    if profile_creator:
        logger.info(f"Creating {total} AWS CLI profiles...")
        for alias, account in accounts:
            profile_creator(
                profile_name=alias,
                account_id=account["id"],
                account_name=account.get("name"),
            )

    # Parallel inventory discovery
    resource_type = "VPCs only" if skip_resources else "full inventory"
    logger.info(f"Discovering {resource_type} for {total} accounts ({max_workers} workers)...")

    accounts_config: dict[str, dict[str, Any]] = {}
    completed = 0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(
                discover_account_inventory,
                alias,
                None,  # Use default region
                skip_resources,
            ): (alias, account)
            for alias, account in accounts
        }

        for future in as_completed(futures):
            alias, account = futures[future]
            completed += 1

            try:
                inventory = future.result()
                inventory.account_id = account["id"]
                inventory.account_alias = alias

                # Get OU path for directory structure
                ou_path = account.get("ou_path", "").replace("Root/", "").replace("Root", "")
                if not ou_path:
                    ou_path = "root"

                # Save inventory file
                save_inventory(org_id, ou_path, alias, inventory)

                # Build accounts.yml entry
                is_manager = account["id"] == management_account_id
                accounts_config[alias] = {
                    "id": account["id"],
                    "name": account.get("name", ""),
                    "ou_path": ou_path,
                    "sso_role": account.get("sso_role", "AdministratorAccess"),
                    "inventory_path": get_relative_inventory_path(ou_path, alias),
                }
                if is_manager:
                    accounts_config[alias]["is_manager"] = True

                # Log progress with expanded resource summary
                vpc_count = len(inventory.vpcs)
                resource_summary = f"{vpc_count} VPCs"
                if not skip_resources:
                    # Count all resources for summary
                    counts = {
                        "S3": len(inventory.s3_buckets),
                        "Lambda": len(inventory.lambda_functions),
                        "RDS": len(inventory.rds_instances) + len(inventory.rds_clusters),
                        "DynamoDB": len(inventory.dynamodb_tables),
                        "ECS": len(inventory.ecs_clusters),
                        "EKS": len(inventory.eks_clusters),
                    }
                    # Only show non-zero counts
                    non_zero = [f"{v} {k}" for k, v in counts.items() if v > 0]
                    if non_zero:
                        resource_summary += ", " + ", ".join(non_zero)

                logger.debug(f"  [{completed}/{total}] {alias}: {resource_summary}")

            except Exception as e:
                logger.warning(f"Discovery failed for {alias}: {e}")
                # Still add account to config even if discovery failed
                ou_path = account.get("ou_path", "root")
                is_manager = account["id"] == management_account_id
                accounts_config[alias] = {
                    "id": account["id"],
                    "name": account.get("name", ""),
                    "ou_path": ou_path,
                    "sso_role": account.get("sso_role", "AdministratorAccess"),
                    "inventory_path": None,  # No inventory on failure
                }
                if is_manager:
                    accounts_config[alias]["is_manager"] = True

    logger.info(f"Discovery complete for {total} accounts")
    return accounts_config
