#!/usr/bin/env python3
"""AWS SSO authentication entry point.

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
    save_accounts,
)
from .discovery import accounts_to_config, discover_accounts
from .profiles import ensure_profile, set_default_profile
from .sso import check_credentials_valid, format_sso_prompt, run_sso_login


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


def first_run_setup() -> bool:
    """Run first-time setup flow.

    1. Use env vars for root account
    2. Create root profile
    3. SSO login for root
    4. Discover accounts from Organizations
    5. Save .aws.yml

    Returns:
        True if setup succeeded
    """
    logger.info("=== AWS SSO First-Run Setup ===")
    logger.info("")

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
    set_default_profile(account_id=root_id)

    # SSO login for root
    logger.info("Authenticating to root account...")
    result = run_sso_login("root")

    if result.sso_url:
        logger.info(format_sso_prompt(result))

    if not result.success:
        logger.error("SSO login failed")
        return False

    logger.success("Root account authenticated")
    logger.info("")

    # Discover and save accounts
    try:
        logger.info("Discovering accounts from Organizations...")
        accounts = discover_accounts(profile_name="root")
        config_accounts = accounts_to_config(accounts)
        save_accounts(config_accounts)
        logger.success(f"Saved {len(config_accounts)} accounts to .aws.yml")
        return True

    except Exception as e:
        logger.error(f"Account discovery failed: {e}")
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
    table.add_column("ID", style="dim")

    for acc in accounts:
        table.add_row(acc["alias"], acc.get("account_name", "-"), acc["account_number"])

    console.print(table)
    console.print()

    # Selection prompt
    choices = [
        {"name": f"{acc['alias']} - {acc.get('account_name', acc['account_number'])}", "value": acc["alias"]}
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

    account_name = account.get("account_name", alias)
    account_id = account["account_number"]

    logger.info(f"Account: {account_name} ({account_id})")

    # Ensure profile exists
    ensure_profile(
        profile_name=alias,
        account_id=account_id,
        account_name=account_name,
        sso_role=account.get("sso_role_name"),
    )
    set_default_profile(account_id=account_id)

    # Check existing credentials
    if not force and check_credentials_valid(alias):
        logger.success(f"Credentials valid for: {alias}")
        return True

    # Run SSO login
    logger.info("Initiating SSO login...")
    result = run_sso_login(alias)

    if result.sso_url:
        logger.info(format_sso_prompt(result))

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

    args = parser.parse_args()
    setup_logging(args.verbose)

    # First-run detection
    if args.setup or not config_exists():
        if not config_exists():
            logger.info("No configuration found. Starting first-run setup...")
        return 0 if first_run_setup() else 1

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
