#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pyyaml",
#     "loguru",
# ]
# ///
"""
Check AWS SSO credential status.

Verifies that valid SSO credentials exist for specified account.
"""

import sys
from pathlib import Path
import subprocess
import json

# Add scripts directory to path
scripts_dir = Path(__file__).parent
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

from logging_config import setup_logging
from config_reader import get_account_by_alias, get_profile_name
from loguru import logger


def main() -> int:
    """
    Main execution function.

    Returns:
        int: Exit code (0 for valid credentials, 1 for invalid)
    """
    setup_logging("sso_check")

    if len(sys.argv) < 2:
        logger.error("Usage: sso_check.py <account-alias>")
        logger.error("  account-alias: root, sandbox, etc.")
        return 1

    account_alias = sys.argv[1]

    try:
        # Lookup account
        account = get_account_by_alias(account_alias)
        profile_name = get_profile_name(account_alias)

        logger.info("Checking SSO credentials")
        logger.info(f"  Account: {account_alias}")
        logger.info(f"  Name: {account.get('account_name', account_alias)}")
        logger.info(f"  Number: {account['account_number']}")
        logger.info(f"  Profile: {profile_name}")
        logger.info("")

        # Check credentials by calling STS GetCallerIdentity
        result = subprocess.run(
            ['aws', 'sts', 'get-caller-identity', '--profile', profile_name],
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode == 0:
            # Parse identity information
            identity = json.loads(result.stdout)
            logger.success("SSO credentials valid")
            logger.info(f"  Account: {identity['Account']}")
            logger.info(f"  UserId: {identity['UserId']}")
            logger.info(f"  ARN: {identity['Arn']}")
            return 0
        else:
            logger.warning("SSO credentials expired or invalid")
            logger.info(f"To login, run: uv run scripts/sso_login.py {account_alias}")
            return 1

    except ValueError as e:
        logger.error(str(e))
        return 1
    except FileNotFoundError as e:
        logger.error(f"Configuration file not found: {e}")
        return 1
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse AWS response: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
