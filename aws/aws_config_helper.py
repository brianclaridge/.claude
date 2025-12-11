#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pyyaml",
#     "loguru",
# ]
# ///
"""
AWS config file helper.

Ensures AWS SSO profiles exist in ~/.aws/config based on config.yml.
"""

import sys
from pathlib import Path
from configparser import ConfigParser

# Add scripts directory to path
scripts_dir = Path(__file__).parent
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

from config_reader import (
    get_sso_start_url,
    get_sso_region,
    get_sso_role_name,
    get_account_region,
    get_account_by_alias,
)
from loguru import logger


def get_aws_config_path() -> Path:
    """
    Get path to AWS config file.

    Returns:
        Path: Path to ~/.aws/config
    """
    return Path.home() / ".aws" / "config"


def ensure_aws_directory() -> None:
    """Ensure ~/.aws directory exists."""
    aws_dir = Path.home() / ".aws"
    if not aws_dir.exists():
        aws_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Created directory: {aws_dir}")


def load_aws_config() -> ConfigParser:
    """
    Load existing AWS config file or create new ConfigParser.

    Returns:
        ConfigParser: AWS config parser
    """
    config = ConfigParser()
    config_path = get_aws_config_path()

    if config_path.exists():
        config.read(config_path)
        logger.debug(f"Loaded existing AWS config from {config_path}")
    else:
        logger.debug("No existing AWS config found, will create new")

    return config


def save_aws_config(config: ConfigParser) -> None:
    """
    Save AWS config to file.

    Args:
        config: ConfigParser to save
    """
    ensure_aws_directory()
    config_path = get_aws_config_path()

    with open(config_path, 'w') as f:
        config.write(f)

    logger.debug(f"Saved AWS config to {config_path}")


def ensure_profile_exists(account_alias: str, account: dict, region: str, sso_url: str) -> bool:
    """
    Ensure AWS SSO profile exists for given account.

    Args:
        account_alias: Account alias (root, sandbox, etc.)
        account: Account dictionary from config.yml or dynamic account
        region: AWS region for this account
        sso_url: SSO start URL

    Returns:
        bool: True if profile was created, False if already existed
    """
    # Use alias directly as profile name (don't validate via get_profile_name
    # to support dynamic accounts not in aws.yml)
    profile_name = account_alias
    section_name = f"profile {profile_name}"

    config = load_aws_config()

    # Check if profile already exists
    if config.has_section(section_name):
        logger.debug(f"Profile already exists: {profile_name}")
        return False

    # Create new profile section
    # Ensure URL has https:// prefix
    if not sso_url.startswith('http://') and not sso_url.startswith('https://'):
        sso_url = f"https://{sso_url}"

    # Get configurable SSO settings
    sso_region = get_sso_region()
    sso_role_name = get_sso_role_name(account_alias)

    config.add_section(section_name)
    config.set(section_name, 'sso_start_url', sso_url)
    config.set(section_name, 'sso_region', sso_region)
    config.set(section_name, 'sso_account_id', str(account['account_number']))
    config.set(section_name, 'sso_role_name', sso_role_name)
    config.set(section_name, 'region', region)

    # Save updated config
    save_aws_config(config)

    logger.info(f"Created AWS profile: {profile_name}")
    logger.debug(f"  Account: {account.get('account_name', account_alias)}")
    logger.debug(f"  Number: {account['account_number']}")
    logger.debug(f"  Region: {region}")
    logger.debug(f"  SSO Region: {sso_region}")
    logger.debug(f"  SSO Role: {sso_role_name}")

    return True


def set_default_profile(account_alias: str, account: dict, region: str, sso_url: str) -> None:
    """
    Set the default AWS profile to use specified account's SSO settings.

    Args:
        account_alias: Account alias (root, sandbox, etc.)
        account: Account dictionary from config.yml
        region: AWS region for this account
        sso_url: SSO start URL
    """
    config = load_aws_config()

    # Ensure URL has https:// prefix
    if not sso_url.startswith('http://') and not sso_url.startswith('https://'):
        sso_url = f"https://{sso_url}"

    # Get configurable SSO settings
    sso_region = get_sso_region()
    sso_role_name = get_sso_role_name(account_alias)

    # Create or update default section
    if not config.has_section('default'):
        config.add_section('default')

    config.set('default', 'sso_start_url', sso_url)
    config.set('default', 'sso_region', sso_region)
    config.set('default', 'sso_account_id', str(account['account_number']))
    config.set('default', 'sso_role_name', sso_role_name)
    config.set('default', 'region', region)

    save_aws_config(config)

    logger.info(f"Set default profile to: {account_alias}")
    logger.debug(f"  Account: {account.get('account_name', account_alias)}")
    logger.debug(f"  Number: {account['account_number']}")


def ensure_profile_for_account(account_alias: str) -> None:
    """
    Ensure AWS profile exists for specified account alias and set as default.

    Args:
        account_alias: Account alias from config.yml (root, sandbox, etc.)

    Raises:
        ValueError: If account alias not found in config.yml
    """
    account = get_account_by_alias(account_alias)
    region = get_account_region(account_alias)
    sso_url = get_sso_start_url()

    if not sso_url:
        raise ValueError("SSO start URL not configured in config.yml (sso_config.start_url)")

    ensure_profile_exists(account_alias, account, region, sso_url)
    set_default_profile(account_alias, account, region, sso_url)


if __name__ == "__main__":
    from logging_config import setup_logging
    setup_logging("aws_config_helper")

    if len(sys.argv) < 2:
        logger.error("Usage: aws_config_helper.py <account-alias>")
        sys.exit(1)

    try:
        ensure_profile_for_account(sys.argv[1])
        logger.success("Profile check complete")
    except Exception as e:
        logger.exception(f"Failed: {e}")
        sys.exit(1)
