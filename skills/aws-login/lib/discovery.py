"""AWS Organizations account discovery."""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import boto3
from loguru import logger

from .config import get_config_dir, get_root_account_id

# Cache configuration
CACHE_TTL_HOURS = 24


def get_cache_path() -> Path:
    """Get path to accounts cache file."""
    return get_config_dir() / ".data" / "accounts_cache.json"


def load_cache() -> list[dict[str, Any]] | None:
    """Load cached accounts if valid.

    Returns:
        List of accounts or None if cache expired/missing
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

        logger.debug(f"Using cache ({len(data.get('accounts', []))} accounts)")
        return data["accounts"]

    except (json.JSONDecodeError, ValueError, KeyError) as e:
        logger.debug(f"Cache invalid: {e}")
        return None


def save_cache(accounts: list[dict[str, Any]]) -> None:
    """Save accounts to cache.

    Args:
        accounts: List of account dictionaries
    """
    cache_path = get_cache_path()
    cache_path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "cached_at": datetime.now().isoformat(),
        "ttl_hours": CACHE_TTL_HOURS,
        "accounts": accounts,
    }

    with open(cache_path, "w") as f:
        json.dump(data, f, indent=2)

    logger.debug(f"Cached {len(accounts)} accounts")


def discover_from_organizations(profile_name: str = "root") -> list[dict[str, Any]]:
    """Discover accounts from AWS Organizations API.

    Args:
        profile_name: AWS profile with Organizations access

    Returns:
        List of account dictionaries with Id, Name, Email, Status

    Raises:
        Exception: If Organizations API call fails
    """
    logger.info("Discovering accounts from AWS Organizations...")

    session = boto3.Session(profile_name=profile_name)
    org_client = session.client("organizations")

    accounts = []
    paginator = org_client.get_paginator("list_accounts")

    for page in paginator.paginate():
        for account in page["Accounts"]:
            if account["Status"] == "ACTIVE":
                accounts.append({
                    "Id": account["Id"],
                    "Name": account["Name"],
                    "Email": account.get("Email", ""),
                    "Status": account["Status"],
                })

    logger.info(f"Discovered {len(accounts)} active accounts")
    return accounts


def discover_accounts(
    profile_name: str = "root",
    force_refresh: bool = False,
) -> list[dict[str, Any]]:
    """Get organization accounts with caching.

    Args:
        profile_name: AWS profile for Organizations access
        force_refresh: If True, bypass cache

    Returns:
        List of account dictionaries
    """
    if not force_refresh:
        cached = load_cache()
        if cached:
            return cached

    accounts = discover_from_organizations(profile_name)
    save_cache(accounts)
    return accounts


def accounts_to_config(accounts: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Convert discovered accounts to config format.

    Args:
        accounts: List from discover_accounts()

    Returns:
        Dictionary suitable for .aws.yml accounts section
    """
    root_account_id = get_root_account_id()
    config_accounts = {}

    for acc in accounts:
        # Generate alias from name
        alias = acc["Name"].lower().replace(" ", "-").replace("_", "-")

        # Special handling for root/management account
        if acc["Id"] == root_account_id:
            alias = "root"

        config_accounts[alias] = {
            "account_name": acc["Name"],
            "account_number": acc["Id"],
            "sso_role_name": "AdministratorAccess",
        }

    return config_accounts
