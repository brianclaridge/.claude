#!/usr/bin/env python3
"""AWS SSO authentication entry point (v1.0 split architecture).

Usage:
    python -m lib [account_alias] [--force]
    ./scripts/aws-auth.ps1 [account_alias] [-Force]
"""

import argparse
import sys

from loguru import logger

from .config import (
    config_exists,
    get_account,
    get_root_account_id,
    get_root_account_name,
    get_sso_start_url,
    list_accounts,
    save_config,
)
from .discovery import discover_organization, enrich_and_save_inventory
from .profiles import clear_aws_config, ensure_profile, set_default_profile
from .sso import check_credentials_valid, run_sso_login


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


def first_run_setup(skip_vpc: bool = False, skip_resources: bool = False) -> bool:
    """Run first-time setup flow.

    1. Clear existing ~/.aws/config
    2. Create root profile and SSO login
    3. Discover organization hierarchy
    4. Discover inventory for all accounts
    5. Save accounts.yml and inventory files

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
        root_id = get_root_account_id()
        root_name = get_root_account_name()
    except ValueError as e:
        logger.error(str(e))
        return False

    logger.info(f"SSO URL: {sso_url}")
    logger.info(f"Root Account: {root_name} ({root_id})")
    logger.info("")

    # Create root profile and login
    ensure_profile(profile_name="root", account_id=root_id, account_name=root_name)
    set_default_profile("root")

    logger.info("Authenticating to root account...")
    result = run_sso_login("root")

    if not result.success:
        logger.error("SSO login failed")
        return False

    logger.success("Root account authenticated")
    logger.info("")

    # Discover organization
    try:
        org_id, tree = discover_organization(profile_name="root")

        if skip_vpc:
            # Auth only - just create profiles, no inventory
            logger.info("Skipping resource discovery (--skip-vpc)")
            from aws_inspector.services.organizations import collect_all_accounts

            accounts = list(collect_all_accounts(tree))
            accounts_config = {}

            for alias, account in accounts:
                ensure_profile(
                    profile_name=alias,
                    account_id=account["id"],
                    account_name=account.get("name"),
                )
                ou_path = account.get("ou_path", "root")
                accounts_config[alias] = {
                    "id": account["id"],
                    "name": account.get("name", ""),
                    "ou_path": ou_path,
                    "sso_role": account.get("sso_role", "AdministratorAccess"),
                    "inventory_path": None,
                }

            save_config(accounts_config, org_id)
            logger.success(f"Saved {len(accounts_config)} accounts (auth only)")
        else:
            # Full discovery with inventory
            accounts_config = enrich_and_save_inventory(
                org_id=org_id,
                tree=tree,
                profile_creator=ensure_profile,
                skip_resources=skip_resources,
            )
            save_config(accounts_config, org_id)
            logger.success(f"Saved {len(accounts_config)} accounts with inventory")

        return True

    except Exception as e:
        logger.error(f"Setup failed: {e}")
        return False


def rebuild_config(skip_vpc: bool = False, skip_resources: bool = False) -> bool:
    """Rebuild config without forcing re-auth.

    Args:
        skip_vpc: If True, skip all resource discovery
        skip_resources: If True, skip S3/SQS/SNS/SES

    Returns:
        True if rebuild succeeded
    """
    logger.info("=== AWS Config Rebuild ===")
    logger.info("")

    # Check if root credentials still valid
    if check_credentials_valid("root"):
        logger.info("Root credentials valid, skipping SSO login")
    else:
        logger.info("Root credentials expired, running SSO login...")
        result = run_sso_login("root")
        if not result.success:
            logger.error("SSO login failed")
            return False
        logger.success("Root account authenticated")

    logger.info("")
    clear_aws_config()

    # Recreate root profile
    try:
        root_id = get_root_account_id()
        root_name = get_root_account_name()
        ensure_profile(profile_name="root", account_id=root_id, account_name=root_name)
        set_default_profile("root")
    except ValueError as e:
        logger.error(str(e))
        return False

    # Discover and save
    try:
        org_id, tree = discover_organization(profile_name="root")

        if skip_vpc:
            from aws_inspector.services.organizations import collect_all_accounts

            accounts = list(collect_all_accounts(tree))
            accounts_config = {}

            for alias, account in accounts:
                ensure_profile(
                    profile_name=alias,
                    account_id=account["id"],
                    account_name=account.get("name"),
                )
                accounts_config[alias] = {
                    "id": account["id"],
                    "name": account.get("name", ""),
                    "ou_path": account.get("ou_path", "root"),
                    "sso_role": account.get("sso_role", "AdministratorAccess"),
                    "inventory_path": None,
                }

            save_config(accounts_config, org_id)
            logger.success(f"Rebuilt {len(accounts_config)} accounts (auth only)")
        else:
            accounts_config = enrich_and_save_inventory(
                org_id=org_id,
                tree=tree,
                profile_creator=ensure_profile,
                skip_resources=skip_resources,
            )
            save_config(accounts_config, org_id)
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

    parts = [f"{alias} - {name}"]
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

    for acc in accounts:
        table.add_row(acc["alias"], acc.get("name", "-"), acc.get("ou_path", "-"))

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
        description="AWS SSO authentication",
        epilog="Examples:\n  aws-auth root\n  aws-auth --rebuild\n  aws-auth",
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
    sys.exit(main())
