"""Configuration for submodule_auto_updater hook."""

from pathlib import Path
from typing import Any

from claude_apps.shared.config_helper import get_hook_config, resolve_log_path


DEFAULT_CONFIG = {
    "log_base_path": ".data/logs/submodule_auto_updater",
    "log_enabled": True,
    "log_level": "INFO",
    "check_interval_minutes": 15,
}


def get_config() -> dict[str, Any]:
    """Load hook configuration from global config.yml."""
    config = DEFAULT_CONFIG.copy()
    config.update(get_hook_config("submodule_auto_updater"))
    return config


def get_log_path() -> Path:
    """Get the log directory path."""
    return resolve_log_path("submodule_auto_updater")


def get_check_interval_seconds() -> int:
    """Get the check interval in seconds."""
    config = get_config()
    return config.get("check_interval_minutes", 15) * 60
