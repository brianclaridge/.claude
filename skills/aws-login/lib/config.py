"""AWS SSO configuration - v1.0 split architecture.

Structure:
- .data/aws/accounts.yml - Auth-only data
- .data/aws/{org-id}/{ou-path}/{alias}.yml - Per-account inventory
"""

import os
import sys
from pathlib import Path
from typing import Any

import yaml
from loguru import logger

# Add aws_utils to path
_lib_path = Path(__file__).parent.parent.parent.parent / "lib"
if str(_lib_path) not in sys.path:
    sys.path.insert(0, str(_lib_path))


def get_claude_path() -> Path:
    """Get the .claude directory path."""
    claude_path = os.environ.get("CLAUDE_PATH")
    if claude_path:
        return Path(claude_path)
    # Fallback: relative to this file
    return Path(__file__).parent.parent.parent.parent


def get_global_config() -> dict[str, Any]:
    """Load global config.yml from .claude directory."""
    config_path = get_claude_path() / "config.yml"
    if config_path.exists():
        with open(config_path) as f:
            return yaml.safe_load(f) or {}
    return {}


def get_aws_data_path() -> Path:
    """Get path to .data/aws directory from config.yml."""
    config = get_global_config()
    # Get path from config.yml, default to .data/aws
    data_path = config.get("cloud_providers", {}).get("aws", {}).get("data_path", ".data/aws")
    return get_claude_path() / data_path


def get_accounts_path() -> Path:
    """Get path to accounts.yml."""
    return get_aws_data_path() / "accounts.yml"


def config_exists() -> bool:
    """Check if accounts.yml exists."""
    return get_accounts_path().exists()


# =============================================================================
# Environment Variables
# =============================================================================


def get_sso_start_url() -> str:
    """Get AWS SSO start URL from environment."""
    url = os.environ.get("AWS_SSO_START_URL", "")
    if not url:
        raise ValueError(
            "AWS_SSO_START_URL not set.\n"
            "Add to .env: AWS_SSO_START_URL=\"https://your-org.awsapps.com/start\""
        )
    if not url.startswith("http"):
        url = f"https://{url}"
    return url


def get_root_account_id() -> str | None:
    """Get root/management account ID from environment (deprecated).

    DEPRECATED: Use get_manager_account() instead. The management account
    is now auto-detected from AWS Organizations API.

    Returns:
        Account ID if set, None otherwise
    """
    return os.environ.get("AWS_ROOT_ACCOUNT_ID") or None


def get_root_account_name() -> str | None:
    """Get root/management account name from environment (deprecated).

    DEPRECATED: Use get_manager_account() instead. The management account
    is now auto-detected from AWS Organizations API.

    Returns:
        Account name if set, None otherwise
    """
    return os.environ.get("AWS_ROOT_ACCOUNT_NAME") or None


def get_default_region() -> str:
    """Get default AWS region."""
    return os.environ.get("AWS_DEFAULT_REGION", "us-east-1")


def get_sso_role_name() -> str:
    """Get default SSO role name."""
    return os.environ.get("AWS_SSO_ROLE_NAME", "AdministratorAccess")


# =============================================================================
# Config I/O
# =============================================================================


def load_config() -> dict[str, Any]:
    """Load accounts.yml configuration."""
    config_path = get_accounts_path()
    if not config_path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")

    with open(config_path) as f:
        return yaml.safe_load(f) or {}


def save_config(
    accounts: dict[str, dict[str, Any]],
    organization_id: str,
    management_account_id: str | None = None,
) -> None:
    """Save accounts.yml.

    Args:
        accounts: Dict of alias -> account config
        organization_id: AWS Organization ID (o-xxx)
        management_account_id: Management account ID (auto-detected)
    """
    config_path = get_accounts_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)

    config = {
        "schema_version": "1.0",
        "organization_id": organization_id,
        "default_region": get_default_region(),
        "sso_start_url": get_sso_start_url(),
        "accounts": accounts,
    }

    # Add management_account_id if provided
    if management_account_id:
        config["management_account_id"] = management_account_id

    with open(config_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    logger.debug(f"Saved accounts config to {config_path}")


def load_accounts() -> dict[str, dict[str, Any]]:
    """Load accounts from config."""
    if not config_exists():
        return {}
    config = load_config()
    return config.get("accounts", {})


def get_account(alias: str) -> dict[str, Any]:
    """Get account by alias."""
    accounts = load_accounts()
    if alias not in accounts:
        available = ", ".join(sorted(accounts.keys())) if accounts else "none"
        raise ValueError(f"Account '{alias}' not found. Available: {available}")
    return accounts[alias]


def list_accounts() -> list[dict[str, Any]]:
    """List all configured accounts."""
    accounts = load_accounts()
    return [
        {**data, "alias": alias}
        for alias, data in sorted(accounts.items())
    ]


def get_management_account_id() -> str | None:
    """Get management account ID from accounts.yml.

    Returns:
        Management account ID if stored, None otherwise
    """
    if not config_exists():
        return None
    config = load_config()
    return config.get("management_account_id")


def get_manager_account() -> dict[str, Any] | None:
    """Get the management account from accounts.yml.

    Finds the account with is_manager=True flag.

    Returns:
        Account dict with alias key, or None if not found
    """
    accounts = load_accounts()
    for alias, data in accounts.items():
        if data.get("is_manager"):
            return {**data, "alias": alias}

    # Fallback: Check if management_account_id is stored
    management_id = get_management_account_id()
    if management_id:
        for alias, data in accounts.items():
            if data.get("id") == management_id:
                return {**data, "alias": alias}

    return None
