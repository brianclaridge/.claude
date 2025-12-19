"""Boto3 session management."""

import os
from functools import lru_cache

import boto3
from loguru import logger


def get_default_region() -> str:
    """Get default AWS region from environment or config.

    Returns:
        Region name (defaults to us-east-1 if not configured)
    """
    return os.environ.get("AWS_DEFAULT_REGION", "us-east-1")


def create_session(
    profile_name: str | None = None,
    region_name: str | None = None,
) -> boto3.Session:
    """Create a boto3 session with optional profile and region.

    Args:
        profile_name: AWS CLI profile name (uses default if None)
        region_name: AWS region (uses default if None)

    Returns:
        Configured boto3 Session
    """
    region = region_name or get_default_region()

    kwargs = {"region_name": region}
    if profile_name:
        kwargs["profile_name"] = profile_name

    logger.debug(f"Creating boto3 session: profile={profile_name}, region={region}")
    return boto3.Session(**kwargs)


@lru_cache(maxsize=32)
def get_cached_session(
    profile_name: str | None = None,
    region_name: str | None = None,
) -> boto3.Session:
    """Get or create a cached boto3 session.

    Caches sessions to avoid repeated credential lookups.

    Args:
        profile_name: AWS CLI profile name
        region_name: AWS region

    Returns:
        Cached boto3 Session
    """
    return create_session(profile_name, region_name)


def clear_session_cache() -> None:
    """Clear the session cache."""
    get_cached_session.cache_clear()


def get_account_id(
    profile_name: str | None = None,
    region: str | None = None,
) -> str:
    """Get the AWS account ID for the current session.

    Args:
        profile_name: AWS CLI profile name
        region: AWS region (for session creation)

    Returns:
        AWS account ID string
    """
    session = create_session(profile_name, region)
    sts = session.client("sts")
    try:
        identity = sts.get_caller_identity()
        return identity["Account"]
    except Exception as e:
        logger.warning(f"Failed to get account ID: {e}")
        return "unknown"
