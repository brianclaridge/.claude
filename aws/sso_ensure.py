#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "boto3",
#     "pyyaml",
#     "loguru",
# ]
# ///
"""
Ensure valid SSO credentials exist (silent check for automation).

This is a lightweight credential validator used by automation scripts.
Returns exit code 0 if valid, 1 if invalid (with error message).
"""

import sys
from pathlib import Path
import subprocess
import os

# Add scripts directory to path
scripts_dir = Path(__file__).parent
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

from logging_config import setup_logging
from config_reader import get_profile_name
from auth_helper import should_skip_sso_check, is_codebuild_environment
from loguru import logger


def main() -> int:
    """
    Check if credentials are valid.

    Supports dual-mode:
    - Environment credentials (CodeBuild): Bypass SSO check, verify env credentials
    - Profile credentials (local dev): Check SSO profile validity

    Returns:
        int: Exit code (0 for valid, 1 for invalid)
    """
    if len(sys.argv) < 2:
        return 1

    setup_logging("sso_ensure")
    account_alias = sys.argv[1]

    try:
        # Bypass SSO check if using environment credentials
        if should_skip_sso_check():
            logger.debug("Using environment credentials - skipping SSO check")
            if is_codebuild_environment():
                logger.debug(f"  Environment: AWS CodeBuild (Build ID: {os.environ.get('CODEBUILD_BUILD_ID')})")

            # Verify environment credentials are valid
            result = subprocess.run(
                ['aws', 'sts', 'get-caller-identity'],
                capture_output=True,
                check=False
            )

            if result.returncode == 0:
                logger.debug("Environment credentials valid")
                return 0
            else:
                logger.error("Environment credentials invalid")
                return 1

        # Profile-based SSO check (local development)
        profile_name = get_profile_name(account_alias)

        # Silent check
        result = subprocess.run(
            ['aws', 'sts', 'get-caller-identity', '--profile', profile_name],
            capture_output=True,
            check=False
        )

        if result.returncode == 0:
            logger.debug(f"Credentials valid for {account_alias}")
            return 0
        else:
            logger.error(f"SSO credentials expired for: {account_alias}")
            logger.error(f"   Profile: {profile_name}")
            logger.error(f"   Run: uv run scripts/sso_login.py {account_alias}")
            return 1

    except Exception as e:
        logger.error(f"Error checking credentials: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
