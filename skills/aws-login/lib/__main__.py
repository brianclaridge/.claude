#!/usr/bin/env python3
"""AWS SSO authentication entry point (v3.0 schema).

Universal entry point for both Claude agent and human CLI usage.

Usage:
    # Via Python module
    python -m lib [account_alias] [--force]

    # Via PowerShell wrapper
    ./scripts/aws-auth.ps1 [account_alias] [-Force]

    # Via Claude agent
    /auth-aws
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
from .discovery import collect_all_accounts, discover_accounts, enrich_tree_with_vpc
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


def count_accounts(node: dict) -> int:
    """Count total accounts in tree."""
    total = len(node.get("accounts", {}))
    for child in node.get("children", {}).values():
        total += count_accounts(child)
    return total


def create_profiles_from_tree(tree: dict) -> None:
    """Create AWS CLI profiles for all accounts in tree (no VPC discovery).

    Args:
        tree: Organization tree with accounts
    """
    accounts = collect_all_accounts(tree)
    logger.info(f"Creating {len(accounts)} AWS CLI profiles...")

    for alias, account in accounts:
        ensure_profile(
            profile_name=alias,
            account_id=account["id"],
            account_name=account.get("name"),
        )


def first_run_setup(skip_vpc: bool = False) -> bool:
    """Run first-time setup flow.

    1. Clear existing ~/.aws/config
    2. Use env vars for root account
    3. Create root profile
    4. SSO login for root
    5. Discover accounts from Organizations (with OU hierarchy)
    6. Enrich with VPC info (unless skip_vpc)
    7. Save .aws.yml

    Args:
        skip_vpc: If True, skip VPC discovery for faster setup

    Returns:
        True if setup succeeded
    """
    logger.info("=== AWS SSO First-Run Setup ===")
    logger.info("")

    # Clear existing config for full replacement
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

    # Create root profile
    ensure_profile(
        profile_name="root",
        account_id=root_id,
        account_name=root_name,
    )
    set_default_profile("root")

    # SSO login for root
    logger.info("Authenticating to root account...")
    result = run_sso_login("root")

    if not result.success:
        logger.error("SSO login failed")
        return False

    logger.success("Root account authenticated")
    logger.info("")

    # Discover organization with OU hierarchy
    try:
        logger.info("Discovering organization hierarchy...")
        tree = discover_accounts(profile_name="root", force_refresh=True)

        if skip_vpc:
            logger.info("Skipping VPC discovery (--skip-vpc)")
            create_profiles_from_tree(tree)
        else:
            # Enrich with VPC info (creates profiles for each account)
            logger.info("")
            enrich_tree_with_vpc(tree, profile_creator=ensure_profile)

        # Save tree to .aws.yml (v3.0 schema)
        save_config(tree)

        total = count_accounts(tree)
        logger.success(f"Saved {total} accounts to .aws.yml")
        return True

    except Exception as e:
        logger.error(f"Account discovery failed: {e}")
        return False


def rebuild_config(skip_vpc: bool = False) -> bool:
    """Rebuild .aws.yml and profiles without forcing re-auth.

    Checks if root credentials are still valid. If so, skips SSO login.
    If expired, runs SSO login first.

    Args:
        skip_vpc: If True, skip VPC discovery for faster rebuild

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

    # Clear existing config for full replacement
    clear_aws_config()

    # Recreate root profile first
    try:
        root_id = get_root_account_id()
        root_name = get_root_account_name()
        ensure_profile(profile_name="root", account_id=root_id, account_name=root_name)
        set_default_profile("root")
    except ValueError as e:
        logger.error(str(e))
        return False

    # Discover organization
    try:
        logger.info("Discovering organization hierarchy...")
        tree = discover_accounts(profile_name="root", force_refresh=True)

        if skip_vpc:
            logger.info("Skipping VPC discovery (--skip-vpc)")
            create_profiles_from_tree(tree)
        else:
            logger.info("")
            enrich_tree_with_vpc(tree, profile_creator=ensure_profile)

        save_config(tree)

        total = count_accounts(tree)
        logger.success(f"Rebuilt {total} accounts in .aws.yml")
        return True

    except Exception as e:
        logger.error(f"Rebuild failed: {e}")
        return False


def select_account_interactive() -> str | None:
    """Show interactive account selection menu.

    Returns:
        Selected account alias or None if cancelled
    """
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
    table.add_column("VPCs", style="green")

    for acc in accounts:
        vpcs = acc.get("vpcs", [])
        vpc_count = str(len(vpcs)) if vpcs else "-"
        table.add_row(
            acc["alias"],
            acc.get("name", "-"),
            acc.get("ou_path", "-"),
            vpc_count,
        )

    console.print(table)
    console.print()

    # Selection prompt
    choices = [
        {"name": f"{acc['alias']} - {acc.get('name', acc.get('id', ''))}", "value": acc["alias"]}
        for acc in accounts
    ]

    try:
        return inquirer.select(
            message="Select AWS Account:",
            choices=choices,
        ).execute()
    except KeyboardInterrupt:
        return None


def login_to_account(alias: str, force: bool = False) -> bool:
    """Login to specified account.

    Args:
        alias: Account alias
        force: If True, force re-login even if credentials valid

    Returns:
        True if login succeeded
    """
    try:
        account = get_account(alias)
    except ValueError as e:
        logger.error(str(e))
        return False

    account_name = account.get("name", alias)
    account_id = account.get("id") or account.get("account_number", "")

    logger.info(f"Account: {account_name} ({account_id})")
    if account.get("ou_path"):
        logger.info(f"OU Path: {account['ou_path']}")

    # Ensure profile exists
    ensure_profile(
        profile_name=alias,
        account_id=account_id,
        account_name=account_name,
        sso_role=account.get("sso_role"),
    )
    set_default_profile(alias)

    # Check existing credentials
    if not force and check_credentials_valid(alias):
        logger.success(f"Credentials valid for: {alias}")
        return True

    # Run SSO login
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
        epilog="Examples:\n  aws-auth root\n  aws-auth --force\n  aws-auth",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "account",
        nargs="?",
        help="Account alias (interactive menu if omitted)",
    )
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Force re-login even if credentials valid",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable debug logging",
    )
    parser.add_argument(
        "--setup",
        action="store_true",
        help="Run first-time setup (discover accounts)",
    )
    parser.add_argument(
        "--skip-vpc",
        action="store_true",
        help="Skip VPC discovery for faster setup/rebuild",
    )
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Rebuild .aws.yml and profiles (re-auth only if needed)",
    )

    args = parser.parse_args()
    setup_logging(args.verbose)

    # Rebuild mode (smart re-auth)
    if args.rebuild:
        return 0 if rebuild_config(skip_vpc=args.skip_vpc) else 1

    # First-run detection
    if args.setup or not config_exists():
        if not config_exists():
            logger.info("No configuration found. Starting first-run setup...")
        return 0 if first_run_setup(skip_vpc=args.skip_vpc) else 1

    # Account selection
    account = args.account
    if not account:
        account = select_account_interactive()
        if not account:
            logger.info("No account selected")
            return 0

    # Login
    return 0 if login_to_account(account, force=args.force) else 1


if __name__ == "__main__":
    sys.exit(main())
