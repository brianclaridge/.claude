#!/usr/bin/env python3
"""AWS SSO authentication entry point (v1.3 single-account discovery).

Usage:
    aws-auth {alias}                        Quick auth only (no discovery)
    aws-auth {alias} --inspect              Quick auth + discovery for that account
    aws-auth {alias} --inspect --background Quick auth + background discovery
    aws-auth --login                        Re-auth current default profile
    aws-auth --inspect                      Full org discovery (foreground)
    aws-auth --inspect --background         Full org discovery (background)
    aws-auth                                Interactive account selection

Changes from v1.2:
- Single-account discovery: `aws-auth {alias} --inspect` discovers only that account
- Background flag restored: `--background` runs discovery in detached subprocess
- Internal `--discover-account` argument for background subprocess

Changes from v1.1:
- Quick auth: `aws-auth {alias}` authenticates immediately (single SSO flow)
- Discovery only on --inspect: no automatic background discovery
- Token reuse: GetRoleCredentials API avoids second device code flow

Changes from v1.0:
- Management account auto-detected from Organizations API (MasterAccountId)
- No special "root" profile - all accounts use their alias
- AWS_ROOT_ACCOUNT_ID and AWS_ROOT_ACCOUNT_NAME env vars no longer required
"""

import argparse
import os
import sys

import structlog

logger = structlog.get_logger()

from .config import (
    clear_aws_data,
    config_exists,
    get_account,
    get_manager_account,
    get_sso_start_url,
    inventory_exists,
    list_accounts,
    save_config,
)
from .discovery import discover_organization, enrich_and_save_inventory
from .profiles import clear_aws_config, ensure_profile, set_default_profile
from .sso import check_credentials_valid, run_sso_login

# SSO discovery now comes from aws_utils library
from pathlib import Path

# Use CLAUDE_PATH env var for reliable path resolution (avoid fragile relative paths)

from claude_apps.shared.aws_utils.services.sso import (
    poll_for_token,
    discover_sso_accounts,
    discover_account_roles,
    get_role_credentials,
)


def setup_logging(verbose: bool = False) -> None:
    """Configure structlog logging."""
    log_level = 10 if verbose else 20  # DEBUG=10, INFO=20
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
    )


def _find_manager_account_alias(
    accounts_config: dict,
    management_account_id: str,
) -> str | None:
    """Find the alias of the management account.

    Args:
        accounts_config: Dict of alias -> account config
        management_account_id: The MasterAccountId from Organizations API

    Returns:
        Alias of the management account, or None if not found
    """
    for alias, data in accounts_config.items():
        if data.get("id") == management_account_id:
            return alias
    return None


def _bootstrap_initial_profile(sso_url: str) -> str | None:
    """Bootstrap authentication via SSO device flow.

    This is used when no profiles exist yet. We authenticate via device
    code flow and discover available accounts.

    Args:
        sso_url: AWS SSO start URL

    Returns:
        Access token if successful, None otherwise
    """
    logger.info("Starting SSO device authorization...")
    logger.info("")

    result = poll_for_token(sso_url)

    if not result.success:
        logger.error(f"SSO authentication failed: {result.error}")
        return None

    logger.info("SSO authentication successful")
    return result.access_token


# Management account naming patterns (priority order)
MANAGEMENT_PATTERNS = ["root", "main", "manager", "management"]


def _sort_accounts_by_management_pattern(accounts: list) -> list:
    """Sort accounts so management-like names appear first.

    Args:
        accounts: List of DiscoveredAccount objects

    Returns:
        Sorted list with management candidates first
    """
    def score(account) -> int:
        name = account.account_name.lower()
        for i, pattern in enumerate(MANAGEMENT_PATTERNS):
            if pattern in name:
                return i
        return len(MANAGEMENT_PATTERNS)  # No match, put at end

    return sorted(accounts, key=score)


def _generate_alias(account_name: str) -> str:
    """Generate profile alias from account name."""
    alias = account_name.lower().replace(" ", "-")
    for prefix in ["provision-iam-"]:
        if alias.startswith(prefix):
            alias = alias[len(prefix):]
    return alias


def _try_organizations_query(
    account,
    sso_url: str,
    access_token: str | None = None,
) -> tuple[bool, dict | None, str | None, str | None]:
    """Try to query Organizations API using the given account.

    Args:
        account: DiscoveredAccount object
        sso_url: SSO start URL
        access_token: Existing SSO access token to reuse (avoids second device flow)

    Returns:
        Tuple of (success, tree_or_none, org_id_or_none, error_type_or_none)
        error_type: "sso_login_failed", "access_denied", "api_error", or None
    """
    alias = _generate_alias(account.account_name)

    logger.info(f"Trying account {account.account_name} for Organizations query...")

    ensure_profile(
        profile_name=alias,
        account_id=account.account_id,
        account_name=account.account_name,
    )

    # If we have an access token, use GetRoleCredentials to avoid second device flow
    if access_token:
        roles = discover_account_roles(
            access_token=access_token,
            account_id=account.account_id,
        )

        if not roles:
            logger.warning(f"No roles available for {alias}")
            return False, None, None, "sso_login_failed"

        role_name = "AdministratorAccess" if "AdministratorAccess" in roles else roles[0]
        creds = get_role_credentials(
            access_token=access_token,
            account_id=account.account_id,
            role_name=role_name,
        )

        if not creds:
            logger.warning(f"Failed to get credentials for {alias}")
            return False, None, None, "sso_login_failed"

        # Cache credentials so discover_organization can use them
        _cache_credentials_for_cli(alias, creds)
    else:
        # Fallback: use run_sso_login (spawns new device flow)
        result = run_sso_login(alias)
        if not result.success:
            logger.warning(f"SSO login failed for {alias}")
            return False, None, None, "sso_login_failed"

    try:
        org_id, tree = discover_organization(profile_name=alias)
        return True, tree, org_id, None
    except Exception as e:
        error_str = str(e)
        if "AccessDeniedException" in error_str:
            logger.warning(f"Account {alias} lacks Organizations permissions")
            return False, None, None, "access_denied"
        else:
            logger.warning(f"Organizations query failed: {e}")
            return False, None, None, "api_error"


def _ask_user_to_select_management_account(accounts: list):
    """Ask user to select the management account interactively.

    Args:
        accounts: List of DiscoveredAccount objects

    Returns:
        Selected DiscoveredAccount
    """
    try:
        from InquirerPy import inquirer
    except ImportError:
        logger.error("Interactive selection requires: pip install InquirerPy")
        return accounts[0]  # Fallback to first account

    if not sys.stdin.isatty():
        logger.warning("Non-interactive mode, using first account")
        return accounts[0]

    choices = [
        {"name": f"{acc.account_name} ({acc.account_id})", "value": acc}
        for acc in accounts
    ]

    logger.info("")
    logger.info("Please select the management account (has Organizations permissions):")

    try:
        return inquirer.fuzzy(
            message="Management account:",
            choices=choices,
            instruction="(type to filter)",
        ).execute()
    except KeyboardInterrupt:
        return None


def spawn_background_discovery(args_list: list[str]) -> None:
    """Spawn detached subprocess for full discovery.

    Args:
        args_list: Arguments to pass to aws-login module (e.g., ["--login"])
    """
    import subprocess

    claude_path = os.environ.get("CLAUDE_PATH", "")
    data_path = os.environ.get("CLAUDE_DATA_PATH", "")

    if not claude_path:
        logger.error("CLAUDE_PATH not set, cannot spawn background discovery")
        return

    # Ensure log directory exists
    log_dir = Path(data_path) / "logs" if data_path else Path.home() / ".claude" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / "aws-discovery.log"
    pid_file = log_dir / "aws-discovery.pid"

    # Build command
    cmd = [
        "uv", "run", "--directory", claude_path,
        "python", "-m", "claude_apps.skills.aws_login",
        *args_list,
    ]

    logger.info(f"Spawning background discovery: {' '.join(cmd)}")
    logger.info(f"Log file: {log_file}")

    try:
        with open(log_file, "w") as log_fh:
            # Spawn detached process
            proc = subprocess.Popen(
                cmd,
                stdout=log_fh,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )

            # Write PID for tracking
            pid_file.write_text(str(proc.pid))
            logger.info(f"Background process started (PID: {proc.pid})")

    except Exception as e:
        logger.error(f"Failed to spawn background discovery: {e}")


def quick_auth_for_account(account_alias: str, force: bool = False) -> bool:
    """Minimal auth to enable immediate use of specified account.

    This performs only what's needed to start using AWS:
    1. Check if credentials are still valid (skip auth if so)
    2. SSO device auth to get access token
    3. Discover accounts from SSO
    4. Find matching account by alias
    5. Get credentials via GetRoleCredentials (reusing token)
    6. Create single profile and set as default

    Args:
        account_alias: Account alias to authenticate
        force: If True, force re-auth even if credentials valid

    Returns:
        True if quick auth succeeded
    """
    # Check if credentials are already valid (unless force is set)
    if not force and check_credentials_valid(account_alias):
        logger.info(f"Credentials valid for: {account_alias}")
        set_default_profile(account_alias)
        return True

    try:
        sso_url = get_sso_start_url()
    except ValueError as e:
        logger.error(str(e))
        return False

    logger.info("=== Quick AWS Auth ===")
    logger.info(f"Target account: {account_alias}")
    logger.info("")

    # Step 1: SSO device auth
    access_token = _bootstrap_initial_profile(sso_url)
    if not access_token:
        return False

    # Step 2: Discover accounts
    logger.info("Discovering accounts...")
    sso_accounts = discover_sso_accounts(access_token)

    if not sso_accounts:
        logger.error("No accounts available via SSO")
        return False

    # Step 3: Find matching account
    target_account = None
    for acc in sso_accounts:
        alias = _generate_alias(acc.account_name)
        if alias == account_alias:
            target_account = acc
            break

    if not target_account:
        logger.error(f"Account '{account_alias}' not found. Available accounts:")
        for acc in sso_accounts:
            logger.error(f"  - {_generate_alias(acc.account_name)} ({acc.account_name})")
        return False

    logger.info(f"Found: {target_account.account_name} ({target_account.account_id})")

    # Step 4: Discover roles and get credentials using existing token
    roles = discover_account_roles(
        access_token=access_token,
        account_id=target_account.account_id,
    )

    if not roles:
        logger.error(f"No roles available for {account_alias}")
        return False

    # Prefer AdministratorAccess, fallback to first available
    role_name = "AdministratorAccess" if "AdministratorAccess" in roles else roles[0]
    logger.info(f"Using role: {role_name}")

    creds = get_role_credentials(
        access_token=access_token,
        account_id=target_account.account_id,
        role_name=role_name,
    )

    if not creds:
        logger.error("Failed to get credentials via token")
        return False

    # Step 5: Create profile and set as default
    ensure_profile(
        profile_name=account_alias,
        account_id=target_account.account_id,
        account_name=target_account.account_name,
        sso_role=role_name,
    )
    set_default_profile(account_alias)

    # Cache credentials for AWS CLI use
    _cache_credentials_for_cli(account_alias, creds)

    logger.info("")
    logger.info(f"Profile '{account_alias}' ready")
    logger.info("You can now use: aws sts get-caller-identity")

    return True


def _cache_credentials_for_cli(profile_name: str, creds) -> None:
    """Cache credentials in AWS CLI format for immediate use.

    AWS CLI caches SSO credentials in ~/.aws/cli/cache/ as JSON files.
    We write compatible format so `aws` commands work immediately.

    Args:
        profile_name: AWS profile name
        creds: RoleCredentials from get_role_credentials()
    """
    import json
    from datetime import datetime, timezone

    cache_dir = Path.home() / ".aws" / "cli" / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)

    # Generate cache key (AWS uses hash, we use profile name for simplicity)
    cache_file = cache_dir / f"{profile_name}.json"

    # Convert millisecond timestamp to ISO format
    expiration = datetime.fromtimestamp(creds.expiration / 1000, tz=timezone.utc)

    cache_data = {
        "Credentials": {
            "AccessKeyId": creds.access_key_id,
            "SecretAccessKey": creds.secret_access_key,
            "SessionToken": creds.session_token,
            "Expiration": expiration.isoformat(),
        }
    }

    cache_file.write_text(json.dumps(cache_data, indent=2))
    logger.debug(f"Cached credentials to {cache_file}")


def discover_single_account(
    account_alias: str,
    skip_vpc: bool = False,
    skip_resources: bool = False,
) -> bool:
    """Discover inventory for a single account.

    Used when user runs `aws-auth {alias} --inspect` to discover
    resources for just that account, not the entire organization.

    Args:
        account_alias: Account alias to discover
        skip_vpc: If True, skip all resource discovery
        skip_resources: If True, skip S3/SQS/SNS/SES

    Returns:
        True if discovery succeeded
    """
    from .config import get_account, load_config, save_config, get_mgmt_account_id
    from .discovery import discover_account_inventory
    from claude_apps.shared.aws_utils.inventory.writer import (
        save_inventory,
        get_relative_inventory_path,
    )

    try:
        account = get_account(account_alias)
    except ValueError as e:
        logger.error(str(e))
        return False

    account_id = account.get("id", "")
    account_name = account.get("name", account_alias)
    ou_path = account.get("ou_path", "root")

    # Check if this is the management account (for org-level resource discovery)
    mgmt_account_id = get_mgmt_account_id()
    is_mgmt_account = mgmt_account_id and account_id == mgmt_account_id

    logger.info(f"=== Discovering: {account_name} ===")
    logger.info(f"Account ID: {account_id}")
    logger.info(f"OU Path: {ou_path}")
    if is_mgmt_account:
        logger.info("Role: Management Account (includes org-level resources)")
    logger.info("")

    if skip_vpc:
        logger.info("Skip mode: auth only (no resource discovery)")
        return True

    try:
        # Load org_id from existing config
        config = load_config()
        org_id = config.get("organization_id", "unknown")

        # Discover inventory for this account
        resource_mode = "VPCs only" if skip_resources else "full inventory"
        logger.info(f"Discovering {resource_mode}...")

        inventory = discover_account_inventory(
            profile_name=account_alias,
            region=None,  # Use default
            skip_resources=skip_resources,
            is_mgmt_account=is_mgmt_account,
        )
        inventory.account_id = account_id
        inventory.account_alias = account_alias

        # Normalize OU path for directory structure
        clean_ou_path = ou_path.replace("Root/", "").replace("Root", "")
        if not clean_ou_path:
            clean_ou_path = "root"

        # Save inventory file
        save_inventory(org_id, clean_ou_path, account_alias, inventory)
        inventory_path = get_relative_inventory_path(clean_ou_path, account_alias)

        # Update accounts.yml with new inventory path
        accounts = config.get("accounts", {})
        if account_alias in accounts:
            accounts[account_alias]["inventory_path"] = inventory_path
            save_config(
                accounts,
                org_id,
                config.get("management_account_id", ""),
            )

        # Log summary
        vpc_count = len(inventory.vpcs)
        logger.info(f"Discovered {vpc_count} VPCs")
        if not skip_resources:
            counts = {
                "S3": len(inventory.s3_buckets),
                "Lambda": len(inventory.lambda_functions),
                "RDS": len(inventory.rds_instances) + len(inventory.rds_clusters),
                "DynamoDB": len(inventory.dynamodb_tables),
                "ECS": len(inventory.ecs_clusters),
                "EKS": len(inventory.eks_clusters),
            }
            non_zero = [f"{v} {k}" for k, v in counts.items() if v > 0]
            if non_zero:
                logger.info(f"Resources: {', '.join(non_zero)}")

        logger.info("")
        logger.info(f"Inventory saved: {inventory_path}")
        return True

    except Exception as e:
        logger.error(f"Discovery failed: {e}")
        return False


def first_run_setup(skip_vpc: bool = False, skip_resources: bool = False) -> bool:
    """Run first-time setup flow.

    1. Clear existing ~/.aws/config
    2. Authenticate via SSO device flow
    3. Discover available accounts via SSO
    4. Pick any account to query Organizations API
    5. Auto-detect management account from MasterAccountId
    6. Discover org hierarchy and save config

    Args:
        skip_vpc: If True, skip all resource discovery (auth only)
        skip_resources: If True, skip S3/SQS/SNS/SES (VPCs still discovered)

    Returns:
        True if setup succeeded
    """
    logger.info("=== AWS SSO First-Run Setup ===")
    logger.info("")

    clear_aws_config()

    try:
        sso_url = get_sso_start_url()
    except ValueError as e:
        logger.error(str(e))
        return False

    logger.info(f"SSO URL: {sso_url}")
    logger.info("")

    # Bootstrap via device auth flow
    access_token = _bootstrap_initial_profile(sso_url)
    if not access_token:
        return False

    # Discover available accounts via SSO
    logger.info("")
    logger.info("Discovering available accounts...")
    sso_accounts = discover_sso_accounts(access_token)

    if not sso_accounts:
        logger.error("No accounts available. Check SSO permissions.")
        return False

    logger.info(f"Found {len(sso_accounts)} accounts via SSO")

    # Sort accounts by management pattern (root, main, manager, management)
    sorted_accounts = _sort_accounts_by_management_pattern(sso_accounts)

    # Try heuristic-sorted accounts first
    org_id = None
    tree = None
    tried_accounts = set()
    last_error = None

    for account in sorted_accounts:
        # Only try accounts that match heuristic patterns
        name_lower = account.account_name.lower()
        if not any(p in name_lower for p in MANAGEMENT_PATTERNS):
            break  # No more heuristic matches, move to user selection

        tried_accounts.add(account.account_id)
        success, tree, org_id, last_error = _try_organizations_query(
            account, sso_url, access_token
        )
        if success:
            break

    # Fallback: ask user to select if heuristics failed
    if not tree:
        remaining = [a for a in sso_accounts if a.account_id not in tried_accounts]

        if remaining:
            # Single account org - use it directly without prompting
            if len(remaining) == 1 and len(sso_accounts) == 1:
                logger.info("")
                logger.info("Single-account organization detected. Using it as management account.")
                success, tree, org_id, last_error = _try_organizations_query(
                    remaining[0], sso_url, access_token
                )
            else:
                logger.info("")
                logger.info("Heuristic selection failed. Please select the management account.")
                selected = _ask_user_to_select_management_account(remaining)
                if selected:
                    success, tree, org_id, last_error = _try_organizations_query(
                        selected, sso_url, access_token
                    )

    if not tree:
        # Provide specific error based on failure type
        if last_error == "sso_login_failed":
            logger.error("SSO login failed. Check AWS_SSO_REGION matches your Identity Center region.")
        elif last_error == "access_denied":
            logger.error("Account lacks Organizations permissions. Only the management account can query Organizations.")
        else:
            logger.error("Failed to query Organizations API.")
        return False

    management_account_id = tree.get("management_account_id", "")

    if management_account_id:
        logger.info(f"Management account detected: {management_account_id}")

    try:
        if skip_vpc:
            # Auth only - just create profiles, no inventory
            logger.info("Skipping resource discovery (--skip-vpc)")
            from claude_apps.shared.aws_utils.services.organizations import collect_all_accounts

            accounts = list(collect_all_accounts(tree))
            accounts_config = {}

            for alias, account in accounts:
                ensure_profile(
                    profile_name=alias,
                    account_id=account["id"],
                    account_name=account.get("name"),
                )
                ou_path = account.get("ou_path", "root")

                # Flag the management account
                is_manager = account["id"] == management_account_id

                accounts_config[alias] = {
                    "id": account["id"],
                    "name": account.get("name", ""),
                    "ou_path": ou_path,
                    "sso_role": account.get("sso_role", "AdministratorAccess"),
                    "inventory_path": None,
                }

                if is_manager:
                    accounts_config[alias]["is_manager"] = True

            save_config(accounts_config, org_id, management_account_id)
            logger.info(f"Saved {len(accounts_config)} accounts (auth only)")

            # Set default profile to manager account
            manager_alias = _find_manager_account_alias(accounts_config, management_account_id)
            if manager_alias:
                set_default_profile(manager_alias)
                logger.info(f"Default profile: {manager_alias}")
        else:
            # Full discovery with inventory
            accounts_config = enrich_and_save_inventory(
                org_id=org_id,
                tree=tree,
                profile_creator=ensure_profile,
                skip_resources=skip_resources,
            )

            # Add is_manager flag
            for alias, data in accounts_config.items():
                if data.get("id") == management_account_id:
                    data["is_manager"] = True

            save_config(accounts_config, org_id, management_account_id)
            logger.info(f"Saved {len(accounts_config)} accounts with inventory")

            # Set default profile to manager account
            manager_alias = _find_manager_account_alias(accounts_config, management_account_id)
            if manager_alias:
                set_default_profile(manager_alias)
                logger.info(f"Default profile: {manager_alias}")

        return True

    except Exception as e:
        logger.error(f"Setup failed: {e}")
        return False


def inspect_config(skip_vpc: bool = False, skip_resources: bool = False) -> bool:
    """Inspect and rebuild config with fresh data.

    Workflow:
    1. Delete .data/aws folder (clear all cached data)
    2. Run first_run_setup() which handles auth automatically

    Args:
        skip_vpc: If True, skip all resource discovery
        skip_resources: If True, skip S3/SQS/SNS/SES

    Returns:
        True if inspect succeeded
    """
    logger.info("=== AWS Config Inspect ===")
    logger.info("")

    # Step 1: Clear cached data
    if clear_aws_data():
        logger.info("Cleared cached AWS data")
    else:
        logger.info("No cached AWS data to clear")

    logger.info("")

    # Step 2: Run first_run_setup which handles:
    # - SSO device auth flow
    # - Organization discovery
    # - Account/inventory creation
    return first_run_setup(skip_vpc, skip_resources)


def build_searchable_choice(acc: dict) -> dict:
    """Build choice with searchable text for fuzzy selection."""
    alias = acc["alias"]
    name = acc.get("name", "")
    ou_path = acc.get("ou_path", "")
    is_manager = acc.get("is_manager", False)

    parts = [f"{alias} - {name}"]
    if is_manager:
        parts.append("(manager)")
    if ou_path:
        parts.append(f"OU:{ou_path}")

    return {"name": " | ".join(parts), "value": alias}


def select_account_interactive() -> str | None:
    """Show interactive account selection with fuzzy search."""
    try:
        from InquirerPy import inquirer
        from rich.console import Console
        from rich.table import Table
    except ImportError:
        logger.error("Interactive mode requires: pip install InquirerPy rich")
        return None

    if not sys.stdin.isatty():
        logger.error("Interactive mode requires a terminal")
        return None

    accounts = list_accounts()
    if not accounts:
        logger.error("No accounts configured")
        return None

    # Display table
    console = Console()
    table = Table(title="AWS Accounts")
    table.add_column("Alias", style="cyan")
    table.add_column("Name", style="magenta")
    table.add_column("OU Path", style="dim")
    table.add_column("Manager", style="green")

    for acc in accounts:
        manager_flag = "yes" if acc.get("is_manager") else ""
        table.add_row(
            acc["alias"],
            acc.get("name", "-"),
            acc.get("ou_path", "-"),
            manager_flag,
        )

    console.print(table)
    console.print()

    # Fuzzy selection
    choices = [build_searchable_choice(acc) for acc in accounts]

    try:
        return inquirer.fuzzy(
            message="Select AWS Account:",
            choices=choices,
            instruction="(type to filter by alias, name, or OU)",
            border=True,
        ).execute()
    except KeyboardInterrupt:
        return None


def login_to_account(alias: str, force: bool = False) -> bool:
    """Login to specified account."""
    try:
        account = get_account(alias)
    except ValueError as e:
        logger.error(str(e))
        return False

    account_name = account.get("name", alias)
    account_id = account.get("id", "")

    logger.info(f"Account: {account_name} ({account_id})")
    if account.get("ou_path"):
        logger.info(f"OU Path: {account['ou_path']}")
    if account.get("is_manager"):
        logger.info("Role: Management Account")

    ensure_profile(
        profile_name=alias,
        account_id=account_id,
        account_name=account_name,
        sso_role=account.get("sso_role"),
    )
    set_default_profile(alias)

    if not force and check_credentials_valid(alias):
        logger.info(f"Credentials valid for: {alias}")
        return True

    logger.info("Initiating SSO login...")
    result = run_sso_login(alias)

    if result.success:
        logger.info("Login successful")
    else:
        logger.error("Login failed")

    return result.success


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="AWS SSO authentication (v1.1 auto-discovery)",
        epilog="Examples:\n  aws-auth sandbox\n  aws-auth --inspect\n  aws-auth",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("account", nargs="?", help="Account alias")
    parser.add_argument("--force", "-f", action="store_true", help="Force re-login")
    parser.add_argument("--verbose", "-v", action="store_true", help="Debug logging")
    parser.add_argument("--login", action="store_true", help="Re-auth current default profile")
    parser.add_argument("--skip-vpc", action="store_true", help="Skip all resource discovery (--inspect only)")
    parser.add_argument("--skip-resources", action="store_true", help="Skip S3/SQS/SNS/SES (--inspect only)")
    parser.add_argument("--inspect", action="store_true", help="Run full discovery")
    parser.add_argument("--background", "-b", action="store_true", help="Run discovery in background (with --inspect)")
    parser.add_argument("--discover-account", help="Internal: discover single account (used by background)")

    args = parser.parse_args()
    setup_logging(args.verbose)

    # Internal: background process for single-account discovery
    # Called by spawn_background_discovery() after quick_auth_for_account()
    if args.discover_account:
        logger.info(f"Background discovery for: {args.discover_account}")
        return 0 if discover_single_account(
            args.discover_account,
            args.skip_vpc,
            args.skip_resources,
        ) else 1

    # Account + inspect: quick auth + discovery for that account only
    if args.inspect and args.account:
        # --login forces re-auth even if creds valid
        if args.login:
            logger.info(f"Force re-auth: {args.account}")

        if quick_auth_for_account(args.account, force=args.login):
            if args.background:
                logger.info("")
                logger.info(f"Discovery for {args.account} running in background...")
                bg_args = ["--discover-account", args.account]
                if args.skip_vpc:
                    bg_args.append("--skip-vpc")
                if args.skip_resources:
                    bg_args.append("--skip-resources")
                spawn_background_discovery(bg_args)
                return 0
            else:
                logger.info("")
                logger.info(f"Running discovery for {args.account} (foreground)...")
                return 0 if discover_single_account(args.account, args.skip_vpc, args.skip_resources) else 1
        return 1

    # Inspect without account: full org discovery
    if args.inspect:
        if args.background:
            logger.info("Full org discovery running in background...")
            bg_args = ["--login"]
            if args.skip_vpc:
                bg_args.append("--skip-vpc")
            if args.skip_resources:
                bg_args.append("--skip-resources")
            spawn_background_discovery(bg_args)
            return 0
        return 0 if inspect_config(args.skip_vpc, args.skip_resources) else 1

    # Login with account: force re-auth that account
    if args.login and args.account:
        logger.info(f"Force re-auth: {args.account}")
        return 0 if quick_auth_for_account(args.account, force=True) else 1

    # Login without account: re-auth current default profile (or menu if no default)
    if args.login:
        if config_exists():
            # Try to get manager account as default
            try:
                manager = get_manager_account()
                if manager:
                    logger.info(f"Re-authenticating default profile: {manager['alias']}")
                    return 0 if quick_auth_for_account(manager["alias"], force=True) else 1
            except Exception:
                pass
            # No default, show menu
            account = select_account_interactive()
            if account:
                return 0 if quick_auth_for_account(account, force=True) else 1
            return 0
        else:
            logger.info("No configuration found. Starting first-run setup...")
            return 0 if first_run_setup(args.skip_vpc, args.skip_resources) else 1

    # First-run: no config exists yet
    if not config_exists():
        logger.info("No configuration found. Starting first-run setup...")
        return 0 if first_run_setup(args.skip_vpc, args.skip_resources) else 1

    # Account selection (interactive if not specified)
    account = args.account
    if not account:
        account = select_account_interactive()
        if not account:
            logger.info("No account selected")
            return 0

    # Quick auth for specified account (no discovery)
    if quick_auth_for_account(account, force=args.force):
        return 0
    return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(130)  # Standard exit code for SIGINT
