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
        skip_resources: If True, skip S3/SQS/SNS/SES discovery

    Returns:
        AccountInventory with all discovered resources
    """
    region = region or get_default_region()

    # Always discover VPCs (core networking)
    vpcs = discover_vpcs(profile_name, region)
    eips = discover_elastic_ips(profile_name, region)

    # Extended resources (optional)
    s3_buckets = []
    sqs_queues = []
    sns_topics = []
    ses_identities = []

    if not skip_resources:
        s3_buckets = discover_s3_buckets(profile_name, region)
        sqs_queues = discover_sqs_queues(profile_name, region)
        sns_topics = discover_sns_topics(profile_name, region)
        ses_identities = discover_ses_identities(profile_name, region)

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

                # Log progress
                vpc_count = len(inventory.vpcs)
                resource_summary = f"{vpc_count} VPCs"
                if not skip_resources:
                    resource_summary += f", {len(inventory.s3_buckets)} S3, {len(inventory.sqs_queues)} SQS"

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
