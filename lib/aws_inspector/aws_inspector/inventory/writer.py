"""Inventory file writer."""

import os
from pathlib import Path

import yaml
from loguru import logger

from aws_inspector.core.schemas import AccountInventory, AccountsConfig


def get_aws_data_path() -> Path:
    """Get the base AWS data directory path.

    Returns:
        Path to .data/aws/ directory
    """
    claude_path = os.environ.get("CLAUDE_PATH", str(Path.home() / ".claude"))
    return Path(claude_path) / ".data" / "aws"


def get_inventory_path(org_id: str, ou_path: str, alias: str) -> Path:
    """Get full path to inventory file.

    Args:
        org_id: Organization ID (o-xxx)
        ou_path: OU path (e.g., "piam-dev-accounts")
        alias: Account alias

    Returns:
        Full path to inventory file
    """
    return get_aws_data_path() / org_id / ou_path / f"{alias}.yml"


def ensure_directory(path: Path) -> None:
    """Ensure directory exists.

    Args:
        path: Path to file (parent directory will be created)
    """
    path.parent.mkdir(parents=True, exist_ok=True)


def save_accounts_config(config: AccountsConfig) -> bool:
    """Save accounts.yml configuration.

    Args:
        config: AccountsConfig object

    Returns:
        True if saved successfully
    """
    config_path = get_aws_data_path() / "accounts.yml"
    ensure_directory(config_path)

    try:
        # Convert to dict for YAML
        data = {
            "schema_version": config.schema_version,
            "organization_id": config.organization_id,
            "default_region": config.default_region,
            "sso_start_url": config.sso_start_url,
            "accounts": {},
        }

        for alias, acc in config.accounts.items():
            data["accounts"][alias] = {
                "id": acc.id,
                "name": acc.name,
                "ou_path": acc.ou_path,
                "sso_role": acc.sso_role,
                "inventory_path": acc.inventory_path,
            }

        with open(config_path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

        logger.debug(f"Saved accounts config to {config_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to save accounts config: {e}")
        return False


def save_inventory(
    org_id: str,
    ou_path: str,
    alias: str,
    inventory: AccountInventory,
) -> bool:
    """Save inventory file for an account.

    Creates the directory structure based on OU hierarchy.

    Args:
        org_id: Organization ID (o-xxx)
        ou_path: OU path (e.g., "piam-dev-accounts")
        alias: Account alias
        inventory: AccountInventory object

    Returns:
        True if saved successfully
    """
    inventory_path = get_inventory_path(org_id, ou_path, alias)
    ensure_directory(inventory_path)

    try:
        data = inventory.to_dict()

        with open(inventory_path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

        logger.debug(f"Saved inventory for {alias} to {inventory_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to save inventory for {alias}: {e}")
        return False


def get_relative_inventory_path(ou_path: str, alias: str) -> str:
    """Get relative inventory path for accounts.yml reference.

    Args:
        ou_path: OU path (e.g., "piam-dev-accounts")
        alias: Account alias

    Returns:
        Relative path string (e.g., "piam-dev-accounts/sandbox.yml")
    """
    return f"{ou_path}/{alias}.yml"
