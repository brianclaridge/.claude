"""Centralized aws.yml reading and account lookup for AWS SSO.

Supports both v1.0 (flat) and v2.0 (nested OU hierarchy) schemas.
"""

import os
from pathlib import Path
from typing import Any
import yaml


def get_config_path() -> Path:
    """
    Get path to .aws.yml configuration file.

    Location: ${CLAUDE_DATA_PATH}/.aws.yml (user-specific, persistent across sessions)

    Returns:
        Path: Path to .aws.yml

    Raises:
        FileNotFoundError: If .aws.yml not found
    """
    # Use CLAUDE_DATA_PATH environment variable for persistent storage
    claude_data_path = os.environ.get("CLAUDE_DATA_PATH")

    if claude_data_path:
        config_path = Path(claude_data_path) / ".aws.yml"
    else:
        # Fallback to legacy location (.claude/.aws.yml)
        core_dir = Path(__file__).parent  # core/
        scripts_dir = core_dir.parent  # scripts/
        skill_dir = scripts_dir.parent  # aws-login/
        skills_dir = skill_dir.parent  # skills/
        claude_dir = skills_dir.parent  # .claude/
        config_path = claude_dir / ".aws.yml"

    if not config_path.exists():
        raise FileNotFoundError(
            f".aws.yml not found at {config_path}\n"
            "Run /auth-aws to set up AWS SSO configuration."
        )

    return config_path


def get_config_dir() -> Path:
    """
    Get directory where config should be stored.

    Returns:
        Path: Directory for config storage
    """
    claude_data_path = os.environ.get("CLAUDE_DATA_PATH")
    if claude_data_path:
        return Path(claude_data_path)

    # Fallback to legacy location
    core_dir = Path(__file__).parent
    scripts_dir = core_dir.parent
    skill_dir = scripts_dir.parent
    skills_dir = skill_dir.parent
    return skills_dir.parent  # .claude/


def config_exists() -> bool:
    """Check if .aws.yml configuration exists.

    Returns:
        True if config file exists
    """
    try:
        get_config_path()
        return True
    except FileNotFoundError:
        return False


def load_config() -> dict[str, Any]:
    """
    Load and parse aws.yml with version detection.

    Returns:
        dict: Parsed configuration with schema_version key
    """
    config_path = get_config_path()
    with open(config_path) as f:
        config = yaml.safe_load(f) or {}

    # Default to v1.0 for backward compatibility
    if "schema_version" not in config:
        config["schema_version"] = "1.0"

    return config


def is_v2_schema(config: dict[str, Any] | None = None) -> bool:
    """
    Check if config uses v2.0+ nested schema.

    Args:
        config: Optional config dict. If None, loads from file.

    Returns:
        bool: True if v2.0+ schema
    """
    if config is None:
        config = load_config()
    version = config.get("schema_version", "1.0")
    return version.startswith("2")


def get_account_by_alias(account_alias: str) -> dict[str, Any]:
    """
    Find account by alias (root, sandbox, etc.).

    Supports both v1.0 flat and v2.0 nested schemas.
    For v2.0, returns full metadata including ou_path and depth.

    Args:
        account_alias: Account alias (e.g., 'root', 'sandbox')

    Returns:
        dict: Account data with keys: account_name, account_number/account_id, etc.

        For v1.0: {'account_name': '...', 'account_number': '...'}
        For v2.0: {'account_name': '...', 'account_id': '...', 'ou_path': '/', ...}

    Raises:
        ValueError: If account not found
    """
    config = load_config()

    # Always use flat 'accounts' index (present in both v1 and v2)
    accounts = config.get("accounts", {})

    account = accounts.get(account_alias)
    if not account:
        raise ValueError(f"Account not found: {account_alias}")

    # Normalize key names for compatibility
    result = account.copy()

    # v1.0 uses 'account_number', v2.0 uses 'account_id'
    if "account_number" in result and "account_id" not in result:
        result["account_id"] = str(result["account_number"])
    elif "account_id" in result and "account_number" not in result:
        result["account_number"] = result["account_id"]

    return result


def get_default_region() -> str:
    """
    Get default AWS region from config.

    Returns:
        str: Default region (e.g., 'us-east-1')
    """
    config = load_config()
    return config.get('default_region', 'us-east-1')


def get_log_path() -> Path:
    """
    Get log directory path from config.

    Returns:
        Path: Absolute path to log directory
    """
    config = load_config()
    log_path = config.get('log_path', '.data/logs')

    # Resolve relative to aws.yml location
    config_dir = get_config_path().parent
    return (config_dir / log_path).resolve()


def get_account_region(account_alias: str) -> str:
    """
    Get AWS region for specific account.

    Returns account-specific region if set, otherwise falls back to default_region.

    Args:
        account_alias: Account alias (e.g., 'root', 'sandbox')

    Returns:
        str: AWS region for this account
    """
    account = get_account_by_alias(account_alias)
    if 'region' in account:
        return account['region']
    return get_default_region()


def get_sso_start_url() -> str:
    """
    Get AWS SSO start URL from config.

    Returns:
        str: SSO start URL
    """
    config = load_config()
    sso_config = config.get('sso_config', {})
    start_url = sso_config.get('start_url', '')

    # Ensure https:// prefix
    if start_url and not start_url.startswith('http'):
        start_url = f"https://{start_url}"

    return start_url


def get_sso_region() -> str:
    """
    Get AWS SSO region from config.

    Returns:
        str: SSO region (defaults to 'us-east-1')
    """
    config = load_config()
    sso_config = config.get('sso_config', {})
    return sso_config.get('region', 'us-east-1')


def get_sso_role_name(account_alias: str | None = None) -> str:
    """
    Get SSO role name for authentication.

    Supports per-account override via account's 'sso_role_name' field.

    Args:
        account_alias: Optional account alias for per-account override

    Returns:
        str: SSO role name (defaults to 'AdministratorAccess')
    """
    config = load_config()

    # Check per-account override first
    if account_alias:
        try:
            account = get_account_by_alias(account_alias)
            if 'sso_role_name' in account:
                return account['sso_role_name']
        except ValueError:
            pass

    # Fall back to global config
    sso_config = config.get('sso_config', {})
    return sso_config.get('role_name', 'AdministratorAccess')


def get_profile_name(account_alias: str) -> str:
    """
    Get AWS CLI profile name from account alias.

    Profile name is simply the account alias.

    Args:
        account_alias: Account alias (e.g., 'root', 'sandbox')

    Returns:
        str: Profile name (same as account alias)
    """
    # Validate account exists
    get_account_by_alias(account_alias)
    return account_alias


def list_all_accounts() -> list[dict[str, Any]]:
    """
    Get list of all accounts.

    Works with both v1.0 and v2.0 schemas.

    Returns:
        list: All accounts with metadata
    """
    config = load_config()
    accounts = config.get("accounts", {})
    all_accounts = []

    for alias, account_data in accounts.items():
        if isinstance(account_data, dict):
            acc_copy = account_data.copy()
            acc_copy["alias"] = alias

            # Normalize account_number/account_id
            if "account_number" in acc_copy:
                acc_copy["account_id"] = str(acc_copy["account_number"])
            elif "account_id" in acc_copy:
                acc_copy["account_number"] = acc_copy["account_id"]

            all_accounts.append(acc_copy)

    return all_accounts


# =============================================================================
# V2.0 Schema Functions (OU-aware)
# =============================================================================


def get_accounts_by_ou_path(ou_path: str) -> list[dict[str, Any]]:
    """
    Get all accounts under an OU path.

    Args:
        ou_path: OU path like '/Infrastructure' or '/Infrastructure/DevOps'

    Returns:
        list: Accounts under this OU (including nested OUs if path is prefix)

    Raises:
        NotImplementedError: If using v1.0 schema
    """
    config = load_config()

    if not is_v2_schema(config):
        raise NotImplementedError(
            "OU queries require aws.yml v2.0 schema. Run: task aws:sso:update"
        )

    accounts = config.get("accounts", {})
    return [
        {**acc, "alias": alias}
        for alias, acc in accounts.items()
        if acc.get("ou_path", "").startswith(ou_path)
    ]


def get_accounts_by_depth(depth: int) -> list[dict[str, Any]]:
    """
    Get accounts at a specific OU depth.

    Args:
        depth: Depth level (0=root, 1=first-level OU, etc.)

    Returns:
        list: Accounts at the specified depth

    Raises:
        NotImplementedError: If using v1.0 schema
    """
    config = load_config()

    if not is_v2_schema(config):
        raise NotImplementedError(
            "Depth queries require aws.yml v2.0 schema. Run: task aws:sso:update"
        )

    return [
        {**acc, "alias": alias}
        for alias, acc in config.get("accounts", {}).items()
        if acc.get("depth") == depth
    ]


def get_account_ou_path(account_alias: str) -> str:
    """
    Get the OU path for an account.

    Args:
        account_alias: Account alias (e.g., 'root', 'sandbox')

    Returns:
        str: OU path (e.g., '/Infrastructure/DevOps') or '/' for root
    """
    account = get_account_by_alias(account_alias)
    return account.get("ou_path", "/")


def get_ou_tree() -> dict[str, Any]:
    """
    Get the full OU tree structure.

    Returns:
        dict: Organization tree from aws.yml

    Raises:
        NotImplementedError: If using v1.0 schema
    """
    config = load_config()

    if not is_v2_schema(config):
        raise NotImplementedError(
            "OU tree requires aws.yml v2.0 schema. Run: task aws:sso:update"
        )

    return config.get("organization", {})


def find_ou_by_name(ou_name: str) -> dict[str, Any] | None:
    """
    Find an OU by name in the tree.

    Args:
        ou_name: OU name (e.g., 'DevOps', 'Infrastructure')

    Returns:
        dict: OU data with 'id', 'name', 'accounts', 'ous' keys, or None if not found
    """
    config = load_config()

    if not is_v2_schema(config):
        return None

    def search_tree(node: dict[str, Any], target: str) -> dict[str, Any] | None:
        for name, ou in node.get("ous", {}).items():
            if name == target:
                return ou
            found = search_tree(ou, target)
            if found:
                return found
        return None

    root = config.get("organization", {}).get("root", {})
    return search_tree(root, ou_name)
