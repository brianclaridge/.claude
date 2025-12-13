#!/usr/bin/env python3
"""
Shared authentication logic for AWS SDK operations.

Supports dual-mode authentication:
- Local Development: AWS SSO profiles (interactive)
- CI/CD Pipeline: Environment variables (CodeBuild, GitHub Actions, etc.)
"""

import os
import boto3
from loguru import logger


def is_using_env_credentials() -> bool:
    """
    Check if AWS credentials are available via environment variables.

    Returns:
        bool: True if using environment credentials, False otherwise
    """
    return bool(os.environ.get('AWS_ACCESS_KEY_ID'))


def is_codebuild_environment() -> bool:
    """
    Check if running in AWS CodeBuild environment.

    Returns:
        bool: True if running in CodeBuild, False otherwise
    """
    return bool(os.environ.get('CODEBUILD_BUILD_ID'))


def get_aws_session(
    profile_name: str | None = None,
    aws_access_key_id: str | None = None,
    aws_secret_access_key: str | None = None,
    aws_session_token: str | None = None
) -> boto3.Session:
    """
    Create AWS session with automatic auth mode detection.

    Modes:
    - Explicit credentials (role assumption): Uses provided access key, secret key, session token
    - Environment credentials (CodeBuild): Uses AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN
    - Profile credentials (local dev): Uses ~/.aws/config profiles

    Args:
        profile_name: AWS CLI profile name (ignored if env credentials present)
        aws_access_key_id: AWS access key ID (for assumed role credentials)
        aws_secret_access_key: AWS secret access key (for assumed role credentials)
        aws_session_token: AWS session token (for assumed role credentials)

    Returns:
        boto3.Session: Configured session

    Examples:
        >>> # In local development (SSO)
        >>> session = get_aws_session('sandbox')
        >>> # In CodeBuild (environment variables)
        >>> session = get_aws_session()  # profile_name ignored
        >>> # With assumed role credentials
        >>> session = get_aws_session(
        ...     aws_access_key_id='ASIA...',
        ...     aws_secret_access_key='...',
        ...     aws_session_token='...'
        ... )
    """
    # Priority 1: Explicit credentials (for role assumption chains)
    if aws_access_key_id and aws_secret_access_key:
        logger.debug("Authentication mode: Explicit credentials (assumed role)")
        return boto3.Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            aws_session_token=aws_session_token
        )

    # Priority 2: Environment credentials (CodeBuild)
    if is_using_env_credentials():
        logger.debug("Authentication mode: Environment variables (CI/CD pipeline)")
        if is_codebuild_environment():
            logger.debug(f"  Environment: AWS CodeBuild (Build ID: {os.environ.get('CODEBUILD_BUILD_ID')})")
        return boto3.Session()

    # Priority 3: Profile credentials (local development)
    if not profile_name:
        raise ValueError("profile_name required when not using environment or explicit credentials")
    logger.debug(f"Authentication mode: AWS CLI profile ({profile_name})")
    return boto3.Session(profile_name=profile_name)


def should_skip_sso_check() -> bool:
    """
    Determine if SSO credential check should be bypassed.

    Returns:
        bool: True if SSO check should be skipped (e.g., in CodeBuild)
    """
    return is_using_env_credentials()
