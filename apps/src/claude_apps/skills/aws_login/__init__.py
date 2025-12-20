"""AWS Login skill library (v1.0 split architecture)."""

from .config import (
    config_exists,
    get_account,
    get_aws_data_path,
    get_default_region,
    get_root_account_id,
    get_root_account_name,
    get_sso_start_url,
    list_accounts,
    load_accounts,
    load_config,
    save_config,
)
from .discovery import (
    discover_organization,
    discover_account_inventory,
    enrich_and_save_inventory,
)
from .profiles import clear_aws_config, ensure_profile, set_default_profile
from .sso import check_credentials_valid, run_sso_login

__all__ = [
    # Config
    "config_exists",
    "get_account",
    "get_aws_data_path",
    "get_default_region",
    "get_root_account_id",
    "get_root_account_name",
    "get_sso_start_url",
    "list_accounts",
    "load_accounts",
    "load_config",
    "save_config",
    # Discovery
    "discover_organization",
    "discover_account_inventory",
    "enrich_and_save_inventory",
    # Profiles
    "clear_aws_config",
    "ensure_profile",
    "set_default_profile",
    # SSO
    "check_credentials_valid",
    "run_sso_login",
]
