"""Inventory file reader."""

from pathlib import Path

import yaml
from loguru import logger

from aws_utils.core.schemas import AccountConfig, AccountInventory, AccountsConfig
from aws_utils.inventory.writer import get_aws_data_path


def get_data_path() -> Path:
    """Get the base data directory path.

    Returns:
        Path to .data/aws/ directory
    """
    return get_aws_data_path()


def load_accounts_config() -> AccountsConfig | None:
    """Load accounts.yml configuration.

    Returns:
        AccountsConfig object or None if not found
    """
    config_path = get_data_path() / "accounts.yml"

    if not config_path.exists():
        logger.debug(f"No accounts config found at {config_path}")
        return None

    try:
        with open(config_path) as f:
            data = yaml.safe_load(f) or {}

        # Convert accounts dict to AccountConfig objects
        accounts = {}
        for alias, acc_data in data.get("accounts", {}).items():
            accounts[alias] = AccountConfig(
                id=acc_data.get("id", ""),
                name=acc_data.get("name", ""),
                ou_path=acc_data.get("ou_path", ""),
                sso_role=acc_data.get("sso_role", "AdministratorAccess"),
                inventory_path=acc_data.get("inventory_path"),
            )

        return AccountsConfig(
            schema_version=data.get("schema_version", "4.0"),
            organization_id=data.get("organization_id", ""),
            default_region=data.get("default_region", "us-east-1"),
            sso_start_url=data.get("sso_start_url", ""),
            accounts=accounts,
        )
    except Exception as e:
        logger.error(f"Failed to load accounts config: {e}")
        return None


def load_inventory(
    org_id: str,
    ou_path: str,
    alias: str,
) -> AccountInventory | None:
    """Load inventory file for an account.

    Args:
        org_id: Organization ID (o-xxx)
        ou_path: OU path (e.g., "piam-dev-accounts")
        alias: Account alias

    Returns:
        AccountInventory object or None if not found
    """
    inventory_path = get_data_path() / org_id / ou_path / f"{alias}.yml"

    if not inventory_path.exists():
        logger.debug(f"No inventory found at {inventory_path}")
        return None

    try:
        with open(inventory_path) as f:
            data = yaml.safe_load(f) or {}

        return AccountInventory(**data)
    except Exception as e:
        logger.error(f"Failed to load inventory for {alias}: {e}")
        return None


def load_inventory_by_alias(alias: str) -> AccountInventory | None:
    """Load inventory file by alias (uses accounts.yml to find path).

    Args:
        alias: Account alias

    Returns:
        AccountInventory object or None if not found
    """
    config = load_accounts_config()
    if not config:
        logger.debug("No accounts config found")
        return None

    account = config.accounts.get(alias)
    if not account:
        logger.debug(f"Account {alias} not found in config")
        return None

    if not account.inventory_path:
        logger.debug(f"No inventory path for {alias}")
        return None

    # Parse inventory path to get components
    # Format: "{ou_path}/{alias}.yml"
    inventory_path = get_data_path() / config.organization_id / account.inventory_path

    if not inventory_path.exists():
        logger.debug(f"No inventory found at {inventory_path}")
        return None

    try:
        with open(inventory_path) as f:
            data = yaml.safe_load(f) or {}

        return AccountInventory(**data)
    except Exception as e:
        logger.error(f"Failed to load inventory for {alias}: {e}")
        return None


def list_accounts() -> list[dict]:
    """List all accounts from accounts.yml.

    Returns:
        List of account dicts with alias, id, name, ou_path
    """
    config = load_accounts_config()
    if not config:
        return []

    accounts = []
    for alias, acc in config.accounts.items():
        accounts.append({
            "alias": alias,
            "id": acc.id,
            "name": acc.name,
            "ou_path": acc.ou_path,
            "sso_role": acc.sso_role,
            "inventory_path": acc.inventory_path,
        })

    return accounts


def get_account(alias: str) -> dict | None:
    """Get account by alias.

    Args:
        alias: Account alias

    Returns:
        Account dict or None
    """
    config = load_accounts_config()
    if not config:
        return None

    acc = config.accounts.get(alias)
    if not acc:
        return None

    return {
        "alias": alias,
        "id": acc.id,
        "name": acc.name,
        "ou_path": acc.ou_path,
        "sso_role": acc.sso_role,
        "inventory_path": acc.inventory_path,
    }
