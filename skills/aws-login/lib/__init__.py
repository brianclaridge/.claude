"""AWS Login skill library (v3.0 schema)."""

from .config import (
    config_exists,
    flatten_tree,
    get_account,
    get_cache_path,
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
    collect_all_accounts,
    discover_accounts,
    discover_account_vpc,
    discover_organization,
    enrich_tree_with_vpc,
    generate_alias,
)
from .profiles import clear_aws_config, ensure_profile, set_default_profile
from .sso import check_credentials_valid, run_sso_login

__all__ = [
    # Config
    "config_exists",
    "flatten_tree",
    "get_account",
    "get_cache_path",
    "get_default_region",
    "get_root_account_id",
    "get_root_account_name",
    "get_sso_start_url",
    "list_accounts",
    "load_accounts",
    "load_config",
    "save_config",
    # Discovery
    "collect_all_accounts",
    "discover_accounts",
    "discover_account_vpc",
    "discover_organization",
    "enrich_tree_with_vpc",
    "generate_alias",
    # Profiles
    "clear_aws_config",
    "ensure_profile",
    "set_default_profile",
    # SSO
    "check_credentials_valid",
    "run_sso_login",
]
