#!/usr/bin/env python3
"""GCP authentication entry point.

Universal entry point for both Claude agent and human CLI usage.

Usage:
    # Via Python module
    python -m lib [--force]

    # Via PowerShell wrapper
    ./scripts/gcp-auth.ps1 [-Force]

    # Via Claude agent
    /auth-gcp
"""

import argparse
import os
import sys

from loguru import logger

from .auth import (
    check_gcloud_installed,
    get_current_account,
    get_current_project,
    run_auth,
    set_project,
    set_quota_project,
)


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


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="GCP authentication",
        epilog="Examples:\n  gcp-auth\n  gcp-auth --force",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Force re-login even if already authenticated",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable debug logging",
    )

    args = parser.parse_args()
    setup_logging(args.verbose)

    # Check gcloud installed
    if not check_gcloud_installed():
        logger.error("gcloud CLI not found. Please install Google Cloud SDK.")
        return 1

    # Check current status
    account = get_current_account()
    project = get_current_project()

    if account:
        logger.info(f"Current account: {account}")
        if not args.force:
            logger.success("Already authenticated")
            if project:
                logger.info(f"Project: {project}")
            return 0
    else:
        logger.info("No active account")

    if project:
        logger.info(f"Current project: {project}")

    # Set project from environment if available
    env_project = os.environ.get("GOOGLE_CLOUD_PROJECT")
    if env_project:
        logger.info(f"Setting project from environment: {env_project}")
        set_project(env_project)
        set_quota_project(env_project)

    # Run authentication
    logger.info("Starting authentication...")
    result = run_auth()

    if result.success:
        logger.success("Authentication successful")

        # Verify
        new_account = get_current_account()
        new_project = get_current_project()
        logger.info(f"Authenticated as: {new_account}")
        if new_project:
            logger.info(f"Project: {new_project}")
        return 0
    else:
        logger.error("Authentication failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
