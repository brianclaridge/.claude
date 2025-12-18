#!/usr/bin/env python3
"""AWS SSO authentication entry point (v1.1 auto-discovery).

Usage:
    python -m lib [account_alias] [--force]
    ./scripts/aws-auth.ps1 [account_alias] [-Force]

Changes from v1.0:
- Management account auto-detected from Organizations API (MasterAccountId)
- No special "root" profile - all accounts use their alias
- AWS_ROOT_ACCOUNT_ID and AWS_ROOT_ACCOUNT_NAME env vars no longer required
"""

import argparse
import sys

from loguru import logger

from .config import (
    config_exists,
    get_account,
    get_manager_account,
    get_sso_start_url,
    list_accounts,
    save_config,
)
from .discovery import discover_organization, enrich_and_save_inventory
from .profiles import clear_aws_config, ensure_profile, set_default_profile
from .sso import check_credentials_valid, run_sso_login

# SSO discovery now comes from aws_utils library
import sys
from pathlib import Path

_lib_path = Path(__file__).parent.parent.parent.parent / "lib"
if str(_lib_path) not in sys.path:
    sys.path.insert(0, str(_lib_path))

from aws_utils.services.sso import poll_for_token, discover_sso_accounts


def setup_logging(verbose: bool = False) -> None:
    """Configure loguru logging."""
    logger.remove()
    level = "DEBUG" if verbose else "INFO"
    logger.add(
        sys.stderr,
        format="<level>{message}</level>",
        level=level,
        colorize=True,
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

    logger.success("SSO authentication successful")
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


def _try_organizations_query(account, sso_url: str) -> tuple[bool, dict | None, str | None, str | None]:
    """Try to query Organizations API using the given account.

    Args:
        account: DiscoveredAccount object
        sso_url: SSO start URL

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
        success, tree, org_id, last_error = _try_organizations_query(account, sso_url)
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
                success, tree, org_id, last_error = _try_organizations_query(remaining[0], sso_url)
            else:
                logger.info("")
                logger.info("Heuristic selection failed. Please select the management account.")
                selected = _ask_user_to_select_management_account(remaining)
                if selected:
                    success, tree, org_id, last_error = _try_organizations_query(selected, sso_url)

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
            from aws_utils.services.organizations import collect_all_accounts

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
            logger.success(f"Saved {len(accounts_config)} accounts (auth only)")

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
            logger.success(f"Saved {len(accounts_config)} accounts with inventory")

            # Set default profile to manager account
            manager_alias = _find_manager_account_alias(accounts_config, management_account_id)
            if manager_alias:
                set_default_profile(manager_alias)
                logger.info(f"Default profile: {manager_alias}")

        return True

    except Exception as e:
        logger.error(f"Setup failed: {e}")
        return False


def rebuild_config(skip_vpc: bool = False, skip_resources: bool = False) -> bool:
    """Rebuild config without forcing re-auth.

    Uses the manager account (is_manager=True) for organization discovery.

    Args:
        skip_vpc: If True, skip all resource discovery
        skip_resources: If True, skip S3/SQS/SNS/SES

    Returns:
        True if rebuild succeeded
    """
    logger.info("=== AWS Config Rebuild ===")
    logger.info("")

    # Find manager account to use for org discovery
    manager = get_manager_account()
    if not manager:
        # Fallback: try first account
        accounts = list_accounts()
        if not accounts:
            logger.error("No accounts configured. Run --setup first.")
            return False
        manager = accounts[0]
        logger.warning(f"No manager account flagged, using: {manager['alias']}")

    manager_alias = manager["alias"]
    manager_id = manager.get("id", "")
    manager_name = manager.get("name", manager_alias)

    # Ensure profile exists
    ensure_profile(
        profile_name=manager_alias,
        account_id=manager_id,
        account_name=manager_name,
        sso_role=manager.get("sso_role"),
    )

    # Check if credentials still valid
    if check_credentials_valid(manager_alias):
        logger.info(f"Credentials valid for {manager_alias}, skipping SSO login")
    else:
        logger.info(f"Credentials expired for {manager_alias}, running SSO login...")
        result = run_sso_login(manager_alias)
        if not result.success:
            logger.error("SSO login failed")
            return False
        logger.success(f"{manager_alias} authenticated")

    logger.info("")
    clear_aws_config()

    # Recreate manager profile
    ensure_profile(
        profile_name=manager_alias,
        account_id=manager_id,
        account_name=manager_name,
        sso_role=manager.get("sso_role"),
    )
    set_default_profile(manager_alias)

    # Discover and save
    try:
        org_id, tree = discover_organization(profile_name=manager_alias)
        management_account_id = tree.get("management_account_id", "")

        if skip_vpc:
            from aws_utils.services.organizations import collect_all_accounts

            accounts = list(collect_all_accounts(tree))
            accounts_config = {}

            for alias, account in accounts:
                ensure_profile(
                    profile_name=alias,
                    account_id=account["id"],
                    account_name=account.get("name"),
                )

                is_manager = account["id"] == management_account_id

                accounts_config[alias] = {
                    "id": account["id"],
                    "name": account.get("name", ""),
                    "ou_path": account.get("ou_path", "root"),
                    "sso_role": account.get("sso_role", "AdministratorAccess"),
                    "inventory_path": None,
                }

                if is_manager:
                    accounts_config[alias]["is_manager"] = True

            save_config(accounts_config, org_id, management_account_id)
            logger.success(f"Rebuilt {len(accounts_config)} accounts (auth only)")
        else:
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
            logger.success(f"Rebuilt {len(accounts_config)} accounts with inventory")

        return True

    except Exception as e:
        logger.error(f"Rebuild failed: {e}")
        return False


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
        logger.success(f"Credentials valid for: {alias}")
        return True

    logger.info("Initiating SSO login...")
    result = run_sso_login(alias)

    if result.success:
        logger.success("Login successful")
    else:
        logger.error("Login failed")

    return result.success


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="AWS SSO authentication (v1.1 auto-discovery)",
        epilog="Examples:\n  aws-auth sandbox\n  aws-auth --rebuild\n  aws-auth",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("account", nargs="?", help="Account alias")
    parser.add_argument("--force", "-f", action="store_true", help="Force re-login")
    parser.add_argument("--verbose", "-v", action="store_true", help="Debug logging")
    parser.add_argument("--setup", action="store_true", help="Run first-time setup")
    parser.add_argument("--skip-vpc", action="store_true", help="Skip all resource discovery")
    parser.add_argument("--skip-resources", action="store_true", help="Skip S3/SQS/SNS/SES (VPCs still discovered)")
    parser.add_argument("--rebuild", action="store_true", help="Rebuild config (re-auth if needed)")

    args = parser.parse_args()
    setup_logging(args.verbose)

    # Rebuild mode
    if args.rebuild:
        return 0 if rebuild_config(args.skip_vpc, args.skip_resources) else 1

    # First-run or setup
    if args.setup or not config_exists():
        if not config_exists():
            logger.info("No configuration found. Starting first-run setup...")
        return 0 if first_run_setup(args.skip_vpc, args.skip_resources) else 1

    # Account selection
    account = args.account
    if not account:
        account = select_account_interactive()
        if not account:
            logger.info("No account selected")
            return 0

    return 0 if login_to_account(account, args.force) else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(130)  # Standard exit code for SIGINT
