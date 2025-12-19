"""AWS Organizations and resource discovery using aws_utils library.

Implements parallel service discovery for improved performance:
- Phase 1: Independent services run in parallel (10 workers)
- Phase 2: Dependent services (ECS/EKS per-cluster) run after Phase 1
"""

import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from loguru import logger

# Add aws_utils to path using CLAUDE_PATH env var for reliable resolution
_claude_path = os.environ.get("CLAUDE_PATH", str(Path(__file__).parent.parent.parent.parent))
_lib_path = Path(_claude_path) / "lib" / "aws_utils"
if str(_lib_path) not in sys.path:
    sys.path.insert(0, str(_lib_path))

from aws_utils.core.schemas import AccountInventory
from aws_utils.services.ec2 import (
    discover_vpcs,
    discover_elastic_ips,
    discover_ec2_instances,
    discover_internet_gateways_all,
    discover_nat_gateways_all,
    discover_subnets_all,
)
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

# Service imports
from aws_utils.services.lambda_svc import discover_lambda_functions
from aws_utils.services.rds import discover_rds_instances, discover_rds_clusters
from aws_utils.services.dynamodb import discover_dynamodb_tables
from aws_utils.services.route53 import (
    discover_route53_zones,
    discover_route53_domains,
    discover_all_route53_records,
)
from aws_utils.services.ecs import (
    discover_ecs_clusters,
    discover_ecs_services,
    discover_ecs_task_definitions,
)
from aws_utils.services.eks import (
    discover_eks_clusters,
    discover_eks_node_groups,
    discover_eks_fargate_profiles,
)
from aws_utils.services.stepfunctions import discover_state_machines, discover_sfn_activities
from aws_utils.services.acm import discover_acm_certificates
from aws_utils.services.secrets_manager import discover_secrets
from aws_utils.services.cognito import discover_user_pools, discover_identity_pools
from aws_utils.services.api_gateway import discover_rest_apis, discover_v2_apis
from aws_utils.services.cloudfront import discover_distributions
from aws_utils.services.codebuild import discover_codebuild_projects
from aws_utils.services.codepipeline import discover_pipelines
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
from aws_utils.services.sso import discover_sso_instances

from .config import get_default_region


# =============================================================================
# Parallel Discovery Infrastructure
# =============================================================================


@dataclass
class ServiceTask:
    """Definition of a service discovery task."""

    name: str
    discover_fn: Callable[[str, str], list[Any]]
    result_key: str


@dataclass
class DiscoveryResult:
    """Result from a service discovery task."""

    task_name: str
    result_key: str
    data: list[Any]
    error: Exception | None = None
    duration_ms: float = 0.0


@dataclass
class DiscoveryContext:
    """Shared context for discovery execution."""

    profile_name: str
    region: str
    results: dict[str, list[Any]] = field(default_factory=dict)
    errors: dict[str, Exception] = field(default_factory=dict)
    lock: threading.Lock = field(default_factory=threading.Lock)


# Registry of independent services that can run in parallel
INDEPENDENT_TASKS = [
    # Network
    ServiceTask("vpcs", discover_vpcs, "vpcs"),
    ServiceTask("elastic_ips", discover_elastic_ips, "elastic_ips"),
    ServiceTask("internet_gateways", discover_internet_gateways_all, "internet_gateways"),
    ServiceTask("nat_gateways", discover_nat_gateways_all, "nat_gateways"),
    ServiceTask("subnets", discover_subnets_all, "subnets"),
    ServiceTask("albs", discover_application_load_balancers, "application_load_balancers"),
    ServiceTask("nlbs", discover_network_load_balancers, "network_load_balancers"),
    ServiceTask("classic_lbs", discover_classic_load_balancers, "classic_load_balancers"),
    ServiceTask("route53_zones", discover_route53_zones, "route53_zones"),
    ServiceTask("route53_domains", discover_route53_domains, "route53_domains"),
    ServiceTask("route53_records", discover_all_route53_records, "route53_records"),
    # Compute
    ServiceTask("ec2_instances", discover_ec2_instances, "ec2_instances"),
    ServiceTask("lambda_functions", discover_lambda_functions, "lambda_functions"),
    ServiceTask("auto_scaling_groups", discover_auto_scaling_groups, "auto_scaling_groups"),
    # Database
    ServiceTask("rds_instances", discover_rds_instances, "rds_instances"),
    ServiceTask("rds_clusters", discover_rds_clusters, "rds_clusters"),
    ServiceTask("dynamodb_tables", discover_dynamodb_tables, "dynamodb_tables"),
    # Storage
    ServiceTask("s3_buckets", discover_s3_buckets, "s3_buckets"),
    # Security
    ServiceTask("iam_roles", discover_iam_roles, "iam_roles"),
    ServiceTask("iam_policies", discover_iam_policies, "iam_policies"),
    ServiceTask("iam_users", discover_iam_users, "iam_users"),
    ServiceTask("iam_groups", discover_iam_groups, "iam_groups"),
    ServiceTask("acm_certificates", discover_acm_certificates, "acm_certificates"),
    ServiceTask("secrets", discover_secrets, "secrets"),
    ServiceTask("cognito_user_pools", discover_user_pools, "cognito_user_pools"),
    ServiceTask("cognito_identity_pools", discover_identity_pools, "cognito_identity_pools"),
    # Application
    ServiceTask("api_gateway_rest_apis", discover_rest_apis, "api_gateway_rest_apis"),
    ServiceTask("api_gateway_v2_apis", discover_v2_apis, "api_gateway_v2_apis"),
    ServiceTask("cloudfront_distributions", discover_distributions, "cloudfront_distributions"),
    ServiceTask("codebuild_projects", discover_codebuild_projects, "codebuild_projects"),
    ServiceTask("codepipelines", discover_pipelines, "codepipelines"),
    # Messaging
    ServiceTask("sqs_queues", discover_sqs_queues, "sqs_queues"),
    ServiceTask("sns_topics", discover_sns_topics, "sns_topics"),
    ServiceTask("ses_identities", discover_ses_identities, "ses_identities"),
    # Orchestration (parent resources only - children discovered in Phase 2)
    ServiceTask("state_machines", discover_state_machines, "state_machines"),
    ServiceTask("sfn_activities", discover_sfn_activities, "sfn_activities"),
    ServiceTask("ecs_clusters", discover_ecs_clusters, "ecs_clusters"),
    ServiceTask("ecs_task_definitions", discover_ecs_task_definitions, "ecs_task_definitions"),
    ServiceTask("eks_clusters", discover_eks_clusters, "eks_clusters"),
    # Monitoring
    ServiceTask("cloudwatch_log_groups", discover_log_groups, "cloudwatch_log_groups"),
    ServiceTask("cloudwatch_alarms", discover_alarms, "cloudwatch_alarms"),
    # SSO (requires sso-admin permissions, gracefully returns empty if unavailable)
    ServiceTask("sso_instances", discover_sso_instances, "sso_instances"),
]


def _execute_task(
    task: ServiceTask,
    ctx: DiscoveryContext,
) -> DiscoveryResult:
    """Execute a single discovery task with error isolation.

    Args:
        task: Service task definition
        ctx: Shared discovery context

    Returns:
        DiscoveryResult with data or error
    """
    start = time.monotonic()

    try:
        data = task.discover_fn(ctx.profile_name, ctx.region)
        duration = (time.monotonic() - start) * 1000

        with ctx.lock:
            ctx.results[task.result_key] = data

        return DiscoveryResult(
            task_name=task.name,
            result_key=task.result_key,
            data=data,
            duration_ms=duration,
        )
    except Exception as e:
        duration = (time.monotonic() - start) * 1000
        logger.debug(f"Discovery failed for {task.name}: {e}")

        with ctx.lock:
            ctx.results[task.result_key] = []
            ctx.errors[task.name] = e

        return DiscoveryResult(
            task_name=task.name,
            result_key=task.result_key,
            data=[],
            error=e,
            duration_ms=duration,
        )


def _discover_phase1_parallel(
    profile_name: str,
    region: str,
    max_workers: int = 10,
) -> DiscoveryContext:
    """Execute Phase 1: All independent services in parallel.

    Args:
        profile_name: AWS CLI profile name
        region: AWS region
        max_workers: Maximum parallel workers

    Returns:
        DiscoveryContext with all results
    """
    ctx = DiscoveryContext(profile_name=profile_name, region=region)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(_execute_task, task, ctx): task
            for task in INDEPENDENT_TASKS
        }

        for future in as_completed(futures):
            task = futures[future]
            result = future.result()
            if result.error:
                logger.debug(
                    f"  {result.task_name}: FAILED ({result.duration_ms:.0f}ms)"
                )
            else:
                logger.debug(
                    f"  {result.task_name}: {len(result.data)} items ({result.duration_ms:.0f}ms)"
                )

    return ctx


def _discover_phase2_parallel(
    profile_name: str,
    region: str,
    ctx: DiscoveryContext,
    max_workers: int = 5,
) -> None:
    """Execute Phase 2: Dependent services using parent data from Phase 1.

    Discovers ECS services, EKS node groups, and EKS Fargate profiles
    for each cluster found in Phase 1.

    Args:
        profile_name: AWS CLI profile name
        region: AWS region
        ctx: Discovery context with Phase 1 results
        max_workers: Maximum parallel workers
    """
    # Get parent resources from Phase 1
    ecs_clusters = ctx.results.get("ecs_clusters", [])
    eks_clusters = ctx.results.get("eks_clusters", [])

    # Build list of dependent tasks
    dependent_tasks: list[tuple[str, str, Callable]] = []

    # ECS services - one task per cluster
    for cluster in ecs_clusters:
        cluster_arn = cluster.cluster_arn
        dependent_tasks.append(("ecs_services", cluster_arn, discover_ecs_services))

    # EKS node groups and fargate profiles - one task per cluster
    for cluster in eks_clusters:
        cluster_name = cluster.cluster_name
        dependent_tasks.append(("eks_node_groups", cluster_name, discover_eks_node_groups))
        dependent_tasks.append(
            ("eks_fargate_profiles", cluster_name, discover_eks_fargate_profiles)
        )

    if not dependent_tasks:
        # No clusters found, nothing to do in Phase 2
        ctx.results["ecs_services"] = []
        ctx.results["eks_node_groups"] = []
        ctx.results["eks_fargate_profiles"] = []
        return

    # Execute dependent tasks in parallel
    ecs_services: list[Any] = []
    eks_node_groups: list[Any] = []
    eks_fargate_profiles: list[Any] = []

    def execute_dependent(
        task_type: str, parent_id: str, discover_fn: Callable
    ) -> tuple[str, list[Any]]:
        try:
            return task_type, discover_fn(profile_name, region, parent_id)
        except Exception as e:
            logger.debug(f"Discovery failed for {task_type} ({parent_id}): {e}")
            return task_type, []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(execute_dependent, task_type, parent_id, fn)
            for task_type, parent_id, fn in dependent_tasks
        ]

        for future in as_completed(futures):
            task_type, results = future.result()
            if task_type == "ecs_services":
                ecs_services.extend(results)
            elif task_type == "eks_node_groups":
                eks_node_groups.extend(results)
            elif task_type == "eks_fargate_profiles":
                eks_fargate_profiles.extend(results)

    # Update context with Phase 2 results
    with ctx.lock:
        ctx.results["ecs_services"] = ecs_services
        ctx.results["eks_node_groups"] = eks_node_groups
        ctx.results["eks_fargate_profiles"] = eks_fargate_profiles


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
    max_workers_phase1: int = 10,
    max_workers_phase2: int = 5,
) -> AccountInventory:
    """Discover full inventory for an account with parallel execution.

    Uses two-phase parallel discovery for ~4x speedup:
    - Phase 1: Independent services run in parallel (10 workers)
    - Phase 2: Dependent services (ECS/EKS per-cluster) run after Phase 1

    Args:
        profile_name: AWS CLI profile name
        region: AWS region
        skip_resources: If True, skip extended resource discovery (only VPCs/EIPs)
        max_workers_phase1: Max threads for independent service discovery
        max_workers_phase2: Max threads for dependent service discovery

    Returns:
        AccountInventory with all discovered resources
    """
    region = region or get_default_region()

    if skip_resources:
        # Minimal discovery - VPCs and EIPs only (sequential is fine)
        vpcs = discover_vpcs(profile_name, region)
        eips = discover_elastic_ips(profile_name, region)
        return AccountInventory(
            account_id="",
            account_alias=profile_name,
            discovered_at=datetime.utcnow(),
            region=region,
            vpcs=vpcs,
            elastic_ips=eips,
        )

    # Phase 1: Parallel discovery of independent services
    logger.debug(f"Phase 1: Discovering independent services ({max_workers_phase1} workers)")
    ctx = _discover_phase1_parallel(profile_name, region, max_workers_phase1)

    # Phase 2: Parallel discovery of dependent services
    logger.debug(f"Phase 2: Discovering dependent services ({max_workers_phase2} workers)")
    _discover_phase2_parallel(profile_name, region, ctx, max_workers_phase2)

    # Build inventory from results
    inventory = AccountInventory(
        account_id="",  # Set by caller
        account_alias=profile_name,
        discovered_at=datetime.utcnow(),
        region=region,
        # Network
        vpcs=ctx.results.get("vpcs", []),
        elastic_ips=ctx.results.get("elastic_ips", []),
        internet_gateways=ctx.results.get("internet_gateways", []),
        nat_gateways=ctx.results.get("nat_gateways", []),
        subnets=ctx.results.get("subnets", []),
        application_load_balancers=ctx.results.get("application_load_balancers", []),
        network_load_balancers=ctx.results.get("network_load_balancers", []),
        classic_load_balancers=ctx.results.get("classic_load_balancers", []),
        route53_zones=ctx.results.get("route53_zones", []),
        route53_domains=ctx.results.get("route53_domains", []),
        route53_records=ctx.results.get("route53_records", []),
        # Compute
        ec2_instances=ctx.results.get("ec2_instances", []),
        lambda_functions=ctx.results.get("lambda_functions", []),
        auto_scaling_groups=ctx.results.get("auto_scaling_groups", []),
        # Database
        rds_instances=ctx.results.get("rds_instances", []),
        rds_clusters=ctx.results.get("rds_clusters", []),
        dynamodb_tables=ctx.results.get("dynamodb_tables", []),
        # Storage
        s3_buckets=ctx.results.get("s3_buckets", []),
        # Security
        iam_roles=ctx.results.get("iam_roles", []),
        iam_policies=ctx.results.get("iam_policies", []),
        iam_users=ctx.results.get("iam_users", []),
        iam_groups=ctx.results.get("iam_groups", []),
        acm_certificates=ctx.results.get("acm_certificates", []),
        secrets=ctx.results.get("secrets", []),
        cognito_user_pools=ctx.results.get("cognito_user_pools", []),
        cognito_identity_pools=ctx.results.get("cognito_identity_pools", []),
        # Application
        api_gateway_rest_apis=ctx.results.get("api_gateway_rest_apis", []),
        api_gateway_v2_apis=ctx.results.get("api_gateway_v2_apis", []),
        cloudfront_distributions=ctx.results.get("cloudfront_distributions", []),
        codebuild_projects=ctx.results.get("codebuild_projects", []),
        codepipelines=ctx.results.get("codepipelines", []),
        # Messaging
        sqs_queues=ctx.results.get("sqs_queues", []),
        sns_topics=ctx.results.get("sns_topics", []),
        ses_identities=ctx.results.get("ses_identities", []),
        # Orchestration
        state_machines=ctx.results.get("state_machines", []),
        sfn_activities=ctx.results.get("sfn_activities", []),
        ecs_clusters=ctx.results.get("ecs_clusters", []),
        ecs_services=ctx.results.get("ecs_services", []),
        ecs_task_definitions=ctx.results.get("ecs_task_definitions", []),
        eks_clusters=ctx.results.get("eks_clusters", []),
        eks_node_groups=ctx.results.get("eks_node_groups", []),
        eks_fargate_profiles=ctx.results.get("eks_fargate_profiles", []),
        # Monitoring
        cloudwatch_log_groups=ctx.results.get("cloudwatch_log_groups", []),
        cloudwatch_alarms=ctx.results.get("cloudwatch_alarms", []),
        # SSO
        sso_instances=ctx.results.get("sso_instances", []),
    )

    # Build relationship graph from discovered resources
    logger.debug("Building relationship graph")
    inventory.build_relationships()

    return inventory


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
