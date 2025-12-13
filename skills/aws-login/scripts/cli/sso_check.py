#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "boto3",
#     "pyyaml",
#     "loguru",
#     "requests",
# ]
# ///
"""
Check AWS SSO credential status with first-run setup support.

Combines sso_check (verbose) and sso_ensure (silent) functionality.
Triggers setup wizard if no .aws.yml configuration exists.

Exit codes:
    0 - Credentials valid
    1 - Credentials invalid/expired
    2 - Configuration missing (quiet mode only)
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Add parent directories to path for imports
aws_dir = Path(__file__).parent.parent
if str(aws_dir) not in sys.path:
    sys.path.insert(0, str(aws_dir))

from loguru import logger

from core.logging_config import setup_logging
from core.config_reader import get_account_by_alias, get_profile_name, config_exists
from core.auth_helper import should_skip_sso_check, is_codebuild_environment
from core.aws_cli import get_caller_identity
from config.setup_wizard import run_setup_wizard


def check_credentials(account_alias: str, verbose: bool = True) -> bool:
    """Check if credentials are valid for an account.

    Args:
        account_alias: Account alias to check (e.g., 'root', 'sandbox')
        verbose: Show detailed output

    Returns:
        True if credentials valid, False otherwise
    """
    # Bypass SSO check if using environment credentials
    if should_skip_sso_check():
        if verbose:
            logger.debug("Using environment credentials - skipping SSO check")
            if is_codebuild_environment():
                logger.debug(f"  Environment: AWS CodeBuild")

        identity = get_caller_identity()
        if identity:
            if verbose:
                logger.success("Environment credentials valid")
            return True
        else:
            logger.error("Environment credentials invalid")
            return False

    # Profile-based SSO check
    try:
        account = get_account_by_alias(account_alias)
        profile_name = get_profile_name(account_alias)
    except ValueError as e:
        logger.error(str(e))
        return False

    if verbose:
        logger.info("Checking SSO credentials")
        logger.info(f"  Account: {account_alias}")
        logger.info(f"  Name: {account.get('account_name', account_alias)}")
        logger.info(f"  Number: {account['account_number']}")
        logger.info(f"  Profile: {profile_name}")
        logger.info("")

    identity = get_caller_identity(profile=profile_name)

    if identity:
        if verbose:
            logger.success("SSO credentials valid")
            logger.info(f"  Account: {identity['Account']}")
            logger.info(f"  UserId: {identity['UserId']}")
            logger.info(f"  ARN: {identity['Arn']}")
        else:
            logger.debug(f"Credentials valid for {account_alias}")
        return True
    else:
        if verbose:
            logger.warning("SSO credentials expired or invalid")
            logger.info(f"To login, run: uv run .claude/aws/cli/sso_login.py {account_alias}")
        else:
            logger.error(f"SSO credentials expired for: {account_alias}")
            logger.error(f"   Profile: {profile_name}")
            logger.error(f"   Run: uv run .claude/aws/cli/sso_login.py {account_alias}")
        return False


def main() -> int:
    """Main entry point.

    Returns:
        Exit code: 0=valid, 1=invalid, 2=config missing (quiet mode)
    """
    parser = argparse.ArgumentParser(
        description="Check AWS SSO credential status",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exit codes:
  0 - Credentials valid
  1 - Credentials invalid/expired
  2 - Configuration missing (quiet mode only)

Examples:
  %(prog)s root              # Check credentials for 'root' account
  %(prog)s sandbox --quiet   # Silent check for automation
  %(prog)s                   # Run setup wizard if no config
""",
    )
    parser.add_argument(
        "account",
        nargs="?",
        default="root",
        help="Account alias to check (default: root)",
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Silent mode for automation (minimal output, exit codes only)",
    )
    args = parser.parse_args()

    # Setup logging based on verbosity
    if args.quiet:
        setup_logging("sso_check", level="ERROR")
    else:
        setup_logging("sso_check")

    # Check if configuration exists
    if not config_exists():
        if args.quiet:
            return 2  # Config missing
        # Run setup wizard for first-time setup
        logger.info("No AWS configuration found. Starting setup wizard...")
        run_setup_wizard()

    try:
        valid = check_credentials(args.account, verbose=not args.quiet)
        return 0 if valid else 1
    except FileNotFoundError as e:
        logger.error(f"Configuration file not found: {e}")
        return 2 if args.quiet else 1
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
