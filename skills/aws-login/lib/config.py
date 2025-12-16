"""AWS SSO configuration from environment variables and .aws.yml (v3.0 schema)."""

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


def get_cache_path() -> Path:
    """Get path to accounts cache file."""
    return get_config_dir() / ".data" / "accounts_cache.json"


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
# Tree Flattening (v3.0 schema)
# =============================================================================


def flatten_tree(node: dict[str, Any], path: str = "Root") -> dict[str, dict[str, Any]]:
    """Recursively flatten organization tree into alias → account dict.

    Args:
        node: Organization tree node with accounts/children
        path: Current OU path (e.g., "Root/Workloads/Production")

    Returns:
        Flat dictionary of alias → account data with ou_path added
    """
    flat: dict[str, dict[str, Any]] = {}

    # Add accounts at this level
    for alias, account in node.get("accounts", {}).items():
        flat[alias] = {
            **account,
            "ou_path": path,
            "account_number": account.get("id", ""),  # Alias for compatibility
        }

    # Recurse into children
    for child_name, child_node in node.get("children", {}).items():
        child_path = f"{path}/{child_name}"
        flat.update(flatten_tree(child_node, child_path))

    return flat


# =============================================================================
# .aws.yml File Operations (v3.0 schema)
# =============================================================================


def load_config() -> dict[str, Any]:
    """Load .aws.yml configuration with generated flat index.

    Returns:
        Configuration with tree and generated accounts index

    Raises:
        FileNotFoundError: If config doesn't exist
    """
    config_path = get_config_path()

    if not config_path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")

    with open(config_path) as f:
        raw = yaml.safe_load(f) or {}

    tree = raw.get("organization", {})
    flat = flatten_tree(tree)

    return {
        "schema_version": raw.get("schema_version", "3.0"),
        "default_region": raw.get("default_region", get_default_region()),
        "organization": tree,
        "accounts": flat,  # Generated at load time
    }


def save_config(organization: dict[str, Any]) -> None:
    """Save organization tree to .aws.yml (v3.0 schema).

    Only saves the tree - flat index is generated at load time.

    Args:
        organization: Organization tree with accounts/children
    """
    config_path = get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)

    config = {
        "schema_version": "3.0",
        "default_region": get_default_region(),
        "organization": organization,
    }

    with open(config_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)


def load_accounts() -> dict[str, dict[str, Any]]:
    """Load flat accounts index from .aws.yml.

    Returns:
        Dictionary of account_alias -> account_data (generated from tree)
    """
    if not config_exists():
        return {}

    config = load_config()
    return config.get("accounts", {})


def get_account(alias: str) -> dict[str, Any]:
    """Get account by alias.

    Args:
        alias: Account alias (e.g., 'root', 'sandbox')

    Returns:
        Account data dictionary with ou_path

    Raises:
        ValueError: If account not found
    """
    accounts = load_accounts()

    if alias not in accounts:
        available = ", ".join(sorted(accounts.keys())) if accounts else "none"
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
        for alias, data in sorted(accounts.items())
    ]
