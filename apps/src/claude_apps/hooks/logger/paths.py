"""Path utilities for logger hook."""

from datetime import datetime
from pathlib import Path
from typing import Any

from claude_apps.shared.config_helper import get_hook_config, resolve_log_path


DEFAULT_CONFIG = {
    "log_base_path": ".data/logs/claude_hooks",
    "log_enabled": True,
    "log_level": "INFO",
}


def get_config() -> dict[str, Any]:
    """Load hook configuration from global config.yml."""
    config = DEFAULT_CONFIG.copy()
    config.update(get_hook_config("logger"))
    return config


def get_log_path(hook_event_name: str, session_id: str) -> Path:
    """Get path for log file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_base = resolve_log_path("logger")
    log_dir = log_base / session_id / hook_event_name
    return log_dir / f"{timestamp}.json"
