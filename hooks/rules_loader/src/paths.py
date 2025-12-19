"""Path utilities for rules_loader hook."""

import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "lib"))
from config_helper import get_hook_config, get_claude_root, resolve_log_path

from .schemas import RulesLoaderConfig


def get_config() -> dict[str, Any]:
    """Load and validate hook configuration from global config.yml."""
    loaded = get_hook_config("rules_loader")
    validated = RulesLoaderConfig(**loaded)
    return validated.model_dump()


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
