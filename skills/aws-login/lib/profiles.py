"""AWS CLI profile management."""

from configparser import ConfigParser
from pathlib import Path
from typing import Any

from loguru import logger

from .config import get_sso_start_url, get_default_region, get_sso_role_name


def get_aws_config_path() -> Path:
    """Get path to ~/.aws/config."""
    return Path.home() / ".aws" / "config"


def ensure_aws_directory() -> None:
    """Ensure ~/.aws directory exists."""
    aws_dir = Path.home() / ".aws"
    aws_dir.mkdir(parents=True, exist_ok=True)


def load_aws_config() -> ConfigParser:
    """Load existing AWS config file.

    Returns:
        ConfigParser with existing config or empty
    """
    config = ConfigParser()
    config_path = get_aws_config_path()

    if config_path.exists():
        config.read(config_path)

    return config


def save_aws_config(config: ConfigParser) -> None:
    """Save AWS config to file.

    Args:
        config: ConfigParser to save
    """
    ensure_aws_directory()

    with open(get_aws_config_path(), "w") as f:
        config.write(f)


def ensure_profile(
    profile_name: str,
    account_id: str,
    account_name: str | None = None,
    region: str | None = None,
    sso_url: str | None = None,
    sso_role: str | None = None,
) -> bool:
    """Ensure AWS SSO profile exists.

    Args:
        profile_name: Profile name (alias, e.g., 'root', 'sandbox')
        account_id: 12-digit AWS account ID
        account_name: Human-readable account name (for logging)
        region: AWS region (defaults to env var or us-east-1)
        sso_url: SSO start URL (defaults to env var)
        sso_role: SSO role name (defaults to env var or AdministratorAccess)

    Returns:
        True if profile was created, False if already existed
    """
    section_name = f"profile {profile_name}"
    config = load_aws_config()

    if config.has_section(section_name):
        logger.debug(f"Profile exists: {profile_name}")
        return False

    # Get values from env vars if not provided
    sso_url = sso_url or get_sso_start_url()
    region = region or get_default_region()
    sso_role = sso_role or get_sso_role_name()

    # Ensure https prefix
    if not sso_url.startswith("http"):
        sso_url = f"https://{sso_url}"

    config.add_section(section_name)
    config.set(section_name, "sso_start_url", sso_url)
    config.set(section_name, "sso_region", region)
    config.set(section_name, "sso_account_id", str(account_id))
    config.set(section_name, "sso_role_name", sso_role)
    config.set(section_name, "region", region)

    save_aws_config(config)

    logger.info(f"Created profile: {profile_name}")
    if account_name:
        logger.debug(f"  Account: {account_name} ({account_id})")

    return True


def set_default_profile(alias: str) -> None:
    """Set the default AWS profile to point to a named profile.

    Copies all settings from the named profile (by alias) to the default section.

    Args:
        alias: Profile alias to set as default (e.g., 'root', 'sandbox')
    """
    config = load_aws_config()
    source_section = f"profile {alias}"

    if not config.has_section(source_section):
        logger.warning(f"Profile not found: {alias}")
        return

    # Ensure default section exists
    if not config.has_section("default"):
        config.add_section("default")

    # Copy all settings from named profile to default
    for key, value in config.items(source_section):
        config.set("default", key, value)

    save_aws_config(config)
    logger.debug(f"Default profile set to: {alias}")
