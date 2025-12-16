"""AWS SSO configuration from environment variables and .aws.yml."""

import os
from pathlib import Path
from typing import Any

import yaml


def get_config_dir() -> Path:
    """Get directory for config storage.

    Returns:
        Path to ${CLAUDE_DATA_PATH} or fallback
    """
    claude_data_path = os.environ.get("CLAUDE_DATA_PATH")
    if claude_data_path:
        return Path(claude_data_path)
    return Path.home() / ".claude"


def get_config_path() -> Path:
    """Get path to .aws.yml configuration file."""
    return get_config_dir() / ".aws.yml"


def config_exists() -> bool:
    """Check if .aws.yml configuration exists."""
    return get_config_path().exists()


# =============================================================================
# Environment Variables (required for first-run)
# =============================================================================


def get_sso_start_url() -> str:
    """Get AWS SSO start URL from environment.

    Environment variable: AWS_SSO_START_URL

    Returns:
        SSO start URL with https:// prefix

    Raises:
        ValueError: If not set
    """
    url = os.environ.get("AWS_SSO_START_URL", "")

    if not url:
        raise ValueError(
            "AWS_SSO_START_URL not set.\n"
            "Add to .env: AWS_SSO_START_URL=\"https://your-org.awsapps.com/start\""
        )

    if not url.startswith("http"):
        url = f"https://{url}"

    return url


def get_root_account_id() -> str:
    """Get root/management account ID from environment.

    Environment variable: AWS_ROOT_ACCOUNT_ID

    Returns:
        12-digit AWS account ID

    Raises:
        ValueError: If not set
    """
    account_id = os.environ.get("AWS_ROOT_ACCOUNT_ID", "")

    if not account_id:
        raise ValueError(
            "AWS_ROOT_ACCOUNT_ID not set.\n"
            "Add to .env: AWS_ROOT_ACCOUNT_ID=\"123456789012\""
        )

    return account_id


def get_root_account_name() -> str:
    """Get root/management account name from environment.

    Environment variable: AWS_ROOT_ACCOUNT_NAME

    Returns:
        Account name/alias

    Raises:
        ValueError: If not set
    """
    name = os.environ.get("AWS_ROOT_ACCOUNT_NAME", "")

    if not name:
        raise ValueError(
            "AWS_ROOT_ACCOUNT_NAME not set.\n"
            "Add to .env: AWS_ROOT_ACCOUNT_NAME=\"your-org\""
        )

    return name


def get_default_region() -> str:
    """Get default AWS region.

    Environment variable: AWS_DEFAULT_REGION (optional)

    Returns:
        AWS region string
    """
    return os.environ.get("AWS_DEFAULT_REGION", "us-east-1")


def get_sso_role_name() -> str:
    """Get default SSO role name.

    Environment variable: AWS_SSO_ROLE_NAME (optional)

    Returns:
        IAM role name for SSO
    """
    return os.environ.get("AWS_SSO_ROLE_NAME", "AdministratorAccess")


# =============================================================================
# .aws.yml File Operations
# =============================================================================


def load_config() -> dict[str, Any]:
    """Load .aws.yml configuration.

    Returns:
        Configuration dictionary

    Raises:
        FileNotFoundError: If config doesn't exist
    """
    config_path = get_config_path()

    if not config_path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")

    with open(config_path) as f:
        return yaml.safe_load(f) or {}


def save_config(config: dict[str, Any]) -> None:
    """Save configuration to .aws.yml.

    Args:
        config: Configuration dictionary
    """
    config_path = get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)

    with open(config_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)


def load_accounts() -> dict[str, dict[str, Any]]:
    """Load accounts from .aws.yml.

    Returns:
        Dictionary of account_alias -> account_data
    """
    if not config_exists():
        return {}

    config = load_config()
    return config.get("accounts", {})


def save_accounts(accounts: dict[str, dict[str, Any]]) -> None:
    """Save accounts to .aws.yml.

    Creates new config if none exists.

    Args:
        accounts: Dictionary of account_alias -> account_data
    """
    if config_exists():
        config = load_config()
    else:
        config = {
            "schema_version": "1.0",
            "default_region": get_default_region(),
        }

    config["accounts"] = accounts
    save_config(config)


def get_account(alias: str) -> dict[str, Any]:
    """Get account by alias.

    Args:
        alias: Account alias (e.g., 'root', 'sandbox')

    Returns:
        Account data dictionary

    Raises:
        ValueError: If account not found
    """
    accounts = load_accounts()

    if alias not in accounts:
        available = ", ".join(accounts.keys()) if accounts else "none"
        raise ValueError(f"Account '{alias}' not found. Available: {available}")

    return accounts[alias]


def list_accounts() -> list[dict[str, Any]]:
    """List all configured accounts.

    Returns:
        List of account dictionaries with 'alias' key added
    """
    accounts = load_accounts()
    return [
        {**data, "alias": alias}
        for alias, data in accounts.items()
    ]
