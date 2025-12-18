"""Path utilities for rules_loader hook."""

import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "lib"))
from config_helper import get_hook_config, get_claude_root, resolve_log_path


DEFAULT_CONFIG = {
    "log_base_path": ".data/logs/rules_loader",
    "rules_path": "rules/",
    "log_enabled": True,
    "log_level": "INFO",
    "reinforcement_enabled": False,
    "rules": {},
}


def get_config() -> dict[str, Any]:
    """Load hook configuration from global config.yml."""
    config = DEFAULT_CONFIG.copy()
    config.update(get_hook_config("rules_loader"))
    return config


def get_log_path(session_id: str, event_name: str) -> Path:
    """Get the path for a log file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_base = resolve_log_path("rules_loader")
    log_dir = log_base / session_id / event_name
    return log_dir / f"{timestamp}.json"


def get_error_log_path(session_id: str) -> Path:
    """Get the path for an error log file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_base = resolve_log_path("rules_loader")
    log_dir = log_base / session_id / "errors"
    return log_dir / f"{timestamp}.json"


def get_rules_path() -> str:
    """Get the path to the rules directory."""
    config = get_config()
    rules_path = config.get("rules_path", "rules/")
    return str(get_claude_root() / rules_path)
