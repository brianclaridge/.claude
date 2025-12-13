"""AWS CLI subprocess wrapper for centralized command execution."""

import json
import subprocess
from typing import Any

from loguru import logger


def run_aws_command(
    args: list[str],
    profile: str | None = None,
    capture_output: bool = True,
    check: bool = False,
    **kwargs: Any,
) -> subprocess.CompletedProcess:
    """Execute AWS CLI command with standard error handling.

    Args:
        args: AWS CLI arguments (without 'aws' prefix)
        profile: AWS profile to use (adds --profile flag)
        capture_output: Capture stdout/stderr
        check: Raise on non-zero exit
        **kwargs: Additional subprocess.run arguments

    Returns:
        CompletedProcess with stdout, stderr, returncode
    """
    cmd = ["aws"] + args

    if profile:
        cmd.extend(["--profile", profile])

    logger.debug(f"Running AWS command: {' '.join(cmd)}")

    result = subprocess.run(
        cmd,
        capture_output=capture_output,
        text=True,
        check=check,
        **kwargs,
    )

    if result.returncode != 0:
        logger.debug(f"AWS command failed (exit {result.returncode}): {result.stderr}")

    return result


def get_caller_identity(profile: str | None = None) -> dict | None:
    """Get STS caller identity to validate credentials.

    Args:
        profile: AWS profile to use

    Returns:
        Dict with Account, UserId, Arn or None if failed
    """
    result = run_aws_command(
        ["sts", "get-caller-identity", "--output", "json"],
        profile=profile,
    )

    if result.returncode != 0:
        return None

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        logger.error(f"Failed to parse caller identity: {result.stdout}")
        return None


def sso_login(profile: str, no_browser: bool = True) -> bool:
    """Initiate SSO login for a profile.

    Args:
        profile: AWS profile to login with
        no_browser: Use --no-browser flag (default True for headless)

    Returns:
        True if login succeeded, False otherwise
    """
    args = ["sso", "login", "--profile", profile]

    if no_browser:
        args.append("--no-browser")

    result = subprocess.run(
        ["aws"] + args,
        capture_output=False,  # Allow interactive output
        text=True,
    )

    return result.returncode == 0


def configure_sso(
    profile: str,
    start_url: str,
    region: str,
    account_id: str,
    role_name: str,
) -> bool:
    """Configure SSO for a profile using aws configure sso.

    Args:
        profile: Profile name to configure
        start_url: SSO start URL
        region: SSO region
        account_id: AWS account ID
        role_name: IAM role name

    Returns:
        True if configuration succeeded
    """
    # Use aws configure set for each SSO parameter
    configs = [
        ("sso_start_url", start_url),
        ("sso_region", region),
        ("sso_account_id", account_id),
        ("sso_role_name", role_name),
        ("region", region),
    ]

    for key, value in configs:
        result = run_aws_command(
            ["configure", "set", key, value, "--profile", profile]
        )
        if result.returncode != 0:
            logger.error(f"Failed to set {key} for profile {profile}")
            return False

    return True
