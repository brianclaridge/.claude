#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "boto3",
#     "pyyaml",
#     "loguru",
#     "InquirerPy>=0.3.4",
#     "rich>=13.0.0",
# ]
# ///
"""
AWS Organizations account discovery with caching and interactive menu.

Discovers accounts from AWS Organizations API using root account credentials.
Caches results locally with configurable TTL.
Displays interactive menu for account selection using Rich + InquirerPy.
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Any

from loguru import logger

# Add scripts directory to path
scripts_dir = Path(__file__).parent
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

# Cache configuration
CACHE_TTL_HOURS = 24


def get_cache_path() -> Path:
    """
    Get path to accounts cache file.

    Returns:
        Path: Path to .data/accounts_cache.json relative to aws.yml location
    """
    from config_reader import get_config_path

    config_dir = get_config_path().parent
    return config_dir / ".data" / "accounts_cache.json"


def load_cache() -> dict[str, Any] | None:
    """
    Load cached accounts if valid.

    Returns:
        dict: Cached data with 'accounts' and 'cached_at' keys, or None if expired/missing
    """
    cache_path = get_cache_path()

    if not cache_path.exists():
        logger.debug("No cache file found")
        return None

    try:
        with open(cache_path) as f:
            data = json.load(f)

        cached_at = datetime.fromisoformat(data.get('cached_at', ''))
        ttl = timedelta(hours=data.get('ttl_hours', CACHE_TTL_HOURS))

        if datetime.now() - cached_at > ttl:
            logger.debug(f"Cache expired (cached at {cached_at})")
            return None

        logger.debug(f"Cache valid ({len(data.get('accounts', []))} accounts, cached at {cached_at})")
        return data

    except (json.JSONDecodeError, ValueError, KeyError) as e:
        logger.debug(f"Cache invalid: {e}")
        return None


def save_cache(accounts: list[dict[str, Any]]) -> None:
    """
    Save accounts to cache file.

    Args:
        accounts: List of account dictionaries from Organizations API
    """
    cache_path = get_cache_path()
    cache_path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        'cached_at': datetime.now().isoformat(),
        'ttl_hours': CACHE_TTL_HOURS,
        'accounts': accounts
    }

    with open(cache_path, 'w') as f:
        json.dump(data, f, indent=2)

    logger.debug(f"Cached {len(accounts)} accounts to {cache_path}")


def discover_accounts_from_org(profile_name: str = "root") -> list[dict[str, Any]]:
    """
    Discover accounts from AWS Organizations API.

    Args:
        profile_name: AWS profile with Organizations access (typically root)

    Returns:
        list: Account dictionaries with 'Id', 'Name', 'Email', 'Status' keys

    Raises:
        Exception: If Organizations API call fails
    """

    from auth_helper import get_aws_session

    logger.info("Discovering accounts from AWS Organizations...")

    session = get_aws_session(profile_name=profile_name)
    org_client = session.client('organizations')

    accounts = []
    paginator = org_client.get_paginator('list_accounts')

    for page in paginator.paginate():
        for account in page['Accounts']:
            if account['Status'] == 'ACTIVE':
                accounts.append({
                    'Id': account['Id'],
                    'Name': account['Name'],
                    'Email': account.get('Email', ''),
                    'Status': account['Status']
                })

    logger.info(f"Discovered {len(accounts)} active accounts")
    return accounts


def get_org_accounts(force_refresh: bool = False) -> list[dict[str, Any]]:
    """
    Get organization accounts with caching.

    Args:
        force_refresh: If True, bypass cache and fetch fresh data

    Returns:
        list: Account dictionaries with 'Id', 'Name', 'Email', 'Status' keys
    """
    if not force_refresh:
        cached = load_cache()
        if cached:
            logger.debug("Using cached accounts")
            return cached['accounts']

    accounts = discover_accounts_from_org()
    save_cache(accounts)
    return accounts


def enrich_accounts_with_aliases(accounts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Enrich discovered accounts with aliases from aws.yml config.

    Args:
        accounts: List of account dictionaries from Organizations API

    Returns:
        list: Accounts with 'alias' field added where configured
    """
    from config_reader import list_all_accounts

    configured = {str(acc['account_number']): acc['alias'] for acc in list_all_accounts()}

    for account in accounts:
        account['alias'] = configured.get(account['Id'])

    return accounts


def show_account_menu(accounts: list[dict[str, Any]]) -> dict[str, Any] | None:
    """
    Display interactive account selection menu.

    Uses Rich for table display and InquirerPy for selection.

    Args:
        accounts: List of account dictionaries

    Returns:
        dict: Selected account, or None if cancelled
    """
    from rich.console import Console
    from rich.table import Table
    from InquirerPy import inquirer

    # Check if running in interactive terminal
    if not sys.stdin.isatty():
        logger.error("Interactive mode requires a terminal")
        logger.error("Use: task sso:login ACCOUNT=<alias>")
        return None

    # Enrich with aliases
    accounts = enrich_accounts_with_aliases(accounts)

    # Display Rich table
    console = Console()
    table = Table(title="AWS Organization Accounts")

    table.add_column("Alias", style="cyan", no_wrap=True)
    table.add_column("Account Name", style="magenta")
    table.add_column("Account ID", style="dim")

    for acc in accounts:
        alias = acc.get('alias') or "-"
        table.add_row(alias, acc['Name'], acc['Id'])

    console.print(table)
    console.print()

    # Build choices for InquirerPy
    choices = []
    for acc in accounts:
        alias = acc.get('alias')
        if alias:
            label = f"{alias} - {acc['Name']} ({acc['Id']})"
        else:
            label = f"{acc['Name']} ({acc['Id']})"
        choices.append({"name": label, "value": acc})

    # Show selection prompt
    try:
        selected = inquirer.select(
            message="Select AWS Account:",
            choices=choices,
            default=None,
        ).execute()

        return selected

    except KeyboardInterrupt:
        logger.info("Selection cancelled")
        return None


if __name__ == "__main__":
    from logging_config import setup_logging

    setup_logging("account_discovery")

    # Test discovery and menu
    try:
        accounts = get_org_accounts()
        selected = show_account_menu(accounts)

        if selected:
            logger.success(f"Selected: {selected['Name']} ({selected['Id']})")
        else:
            logger.info("No account selected")

    except Exception as e:
        logger.exception(f"Failed: {e}")
        sys.exit(1)
