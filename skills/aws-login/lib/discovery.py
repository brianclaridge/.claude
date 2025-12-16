"""AWS Organizations account discovery with OU hierarchy (v3.0 schema)."""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable

import boto3
from botocore.exceptions import ClientError
from loguru import logger

from .config import get_cache_path, get_default_region, get_root_account_id

# Cache configuration
CACHE_TTL_HOURS = 24

# Prefixes to strip when generating aliases
ALIAS_PREFIXES = ["provision-iam-", "client-"]


def generate_alias(account_id: str, account_name: str, root_account_id: str) -> str:
    """Generate account alias from name.

    Rules:
    - Root account → "root"
    - Strip "provision-iam-" prefix (e.g., provision-iam-sandbox → sandbox)
    - Strip "client-" prefix (e.g., client-acme → acme)
    - Fallback: sanitize name (lowercase, replace spaces/underscores with hyphens)

    Args:
        account_id: AWS account ID
        account_name: AWS account name
        root_account_id: Root/management account ID

    Returns:
        Generated alias string
    """
    if account_id == root_account_id:
        return "root"

    name = account_name.lower()

    for prefix in ALIAS_PREFIXES:
        if name.startswith(prefix):
            return name[len(prefix):]

    return name.replace(" ", "-").replace("_", "-")


def load_cache() -> dict[str, Any] | None:
    """Load cached organization data if valid.

    Returns:
        Organization data or None if cache expired/missing
    """
    cache_path = get_cache_path()

    if not cache_path.exists():
        return None

    try:
        with open(cache_path) as f:
            data = json.load(f)

        cached_at = datetime.fromisoformat(data.get("cached_at", ""))
        ttl = timedelta(hours=data.get("ttl_hours", CACHE_TTL_HOURS))

        if datetime.now() - cached_at > ttl:
            logger.debug("Cache expired")
            return None

        logger.debug("Using cached organization data")
        return data.get("organization")

    except (json.JSONDecodeError, ValueError, KeyError) as e:
        logger.debug(f"Cache invalid: {e}")
        return None


def save_cache(organization: dict[str, Any]) -> None:
    """Save organization data to cache.

    Args:
        organization: Organization tree
    """
    cache_path = get_cache_path()
    cache_path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "cached_at": datetime.now().isoformat(),
        "ttl_hours": CACHE_TTL_HOURS,
        "organization": organization,
    }

    with open(cache_path, "w") as f:
        json.dump(data, f, indent=2)

    logger.debug("Cached organization data")


def _traverse_ou(
    org_client,
    parent_id: str,
    root_account_id: str,
) -> dict[str, Any]:
    """Recursively traverse OU tree and build dict-based structure.

    Args:
        org_client: boto3 organizations client
        parent_id: Parent OU or root ID
        root_account_id: Root account ID for alias detection

    Returns:
        Node with accounts (dict) and children (dict)
    """
    node = {"accounts": {}, "children": {}}

    # Get child OUs
    try:
        ou_paginator = org_client.get_paginator("list_organizational_units_for_parent")
        for page in ou_paginator.paginate(ParentId=parent_id):
            for ou in page.get("OrganizationalUnits", []):
                ou_name = ou["Name"]
                child_node = _traverse_ou(org_client, ou["Id"], root_account_id)
                child_node["ou_id"] = ou["Id"]
                node["children"][ou_name] = child_node
    except Exception as e:
        logger.warning(f"Failed to list OUs for {parent_id}: {e}")

    # Get accounts in this OU/root
    try:
        acc_paginator = org_client.get_paginator("list_accounts_for_parent")
        for page in acc_paginator.paginate(ParentId=parent_id):
            for acc in page.get("Accounts", []):
                if acc["Status"] != "ACTIVE":
                    continue

                account_id = acc["Id"]
                account_name = acc["Name"]
                alias = generate_alias(account_id, account_name, root_account_id)

                node["accounts"][alias] = {
                    "id": account_id,
                    "name": account_name,
                    "sso_role": "AdministratorAccess",
                }
    except Exception as e:
        logger.warning(f"Failed to list accounts for {parent_id}: {e}")

    return node


def discover_organization(profile_name: str = "root") -> dict[str, Any]:
    """Discover organization with full OU hierarchy.

    Args:
        profile_name: AWS profile with Organizations access

    Returns:
        Organization tree with dict-based accounts/children

    Raises:
        RuntimeError: If Organizations API call fails
    """
    logger.info("Discovering organization hierarchy...")

    session = boto3.Session(profile_name=profile_name)
    org_client = session.client("organizations")
    root_account_id = get_root_account_id()

    # Get organization root
    roots = org_client.list_roots()["Roots"]
    if not roots:
        raise RuntimeError("No organization root found")

    root = roots[0]
    root_id = root["Id"]

    # Traverse hierarchy
    tree = _traverse_ou(org_client, root_id, root_account_id)
    tree["name"] = "Root"
    tree["ou_id"] = root_id

    # Count accounts
    def count_accounts(node: dict) -> int:
        total = len(node.get("accounts", {}))
        for child in node.get("children", {}).values():
            total += count_accounts(child)
        return total

    total = count_accounts(tree)
    logger.info(f"Discovered {total} accounts across organization")

    return tree


def discover_accounts(
    profile_name: str = "root",
    force_refresh: bool = False,
) -> dict[str, Any]:
    """Get organization tree with caching.

    Args:
        profile_name: AWS profile for Organizations access
        force_refresh: If True, bypass cache

    Returns:
        Organization tree
    """
    if not force_refresh:
        cached = load_cache()
        if cached:
            return cached

    tree = discover_organization(profile_name)
    save_cache(tree)
    return tree


def discover_account_vpc(profile_name: str, region: str | None = None) -> dict[str, Any]:
    """Discover default VPC for an account.

    Args:
        profile_name: AWS CLI profile name
        region: Region to query (defaults to AWS_DEFAULT_REGION)

    Returns:
        Dictionary with region, vpc_id, vpc_cidr
    """
    region = region or get_default_region()

    try:
        session = boto3.Session(profile_name=profile_name, region_name=region)
        ec2 = session.client("ec2")

        # Find default VPC
        vpcs = ec2.describe_vpcs(
            Filters=[{"Name": "is-default", "Values": ["true"]}]
        ).get("Vpcs", [])

        if vpcs:
            vpc = vpcs[0]
            return {
                "region": region,
                "vpc_id": vpc["VpcId"],
                "vpc_cidr": vpc.get("CidrBlock", ""),
            }

        # No default VPC, try to get any VPC
        vpcs = ec2.describe_vpcs().get("Vpcs", [])
        if vpcs:
            vpc = vpcs[0]
            return {
                "region": region,
                "vpc_id": vpc["VpcId"],
                "vpc_cidr": vpc.get("CidrBlock", ""),
            }

        return {"region": region, "vpc_id": None, "vpc_cidr": None}

    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "")
        if error_code in ("ExpiredToken", "UnauthorizedAccess", "AccessDenied"):
            logger.debug(f"No access to {profile_name}: {error_code}")
        else:
            logger.warning(f"VPC discovery failed for {profile_name}: {e}")
        return {"region": region, "vpc_id": None, "vpc_cidr": None}
    except Exception as e:
        logger.warning(f"VPC discovery error for {profile_name}: {e}")
        return {"region": region, "vpc_id": None, "vpc_cidr": None}


def enrich_tree_with_vpc(
    node: dict[str, Any],
    profile_creator: Callable | None = None,
) -> None:
    """Add VPC info to all accounts in tree (mutates in place).

    Args:
        node: Organization tree node
        profile_creator: Function to create AWS CLI profiles
    """
    # Enrich accounts at this level
    for alias, account in node.get("accounts", {}).items():
        if profile_creator:
            profile_creator(
                profile_name=alias,
                account_id=account["id"],
                account_name=account.get("name"),
            )

        vpc_info = discover_account_vpc(alias)
        account["region"] = vpc_info["region"]
        account["vpc_id"] = vpc_info["vpc_id"]
        account["vpc_cidr"] = vpc_info["vpc_cidr"]

        if vpc_info["vpc_id"]:
            logger.debug(f"  {alias}: {vpc_info['vpc_id']} ({vpc_info['region']})")

    # Recurse into children
    for child_node in node.get("children", {}).values():
        enrich_tree_with_vpc(child_node, profile_creator)
