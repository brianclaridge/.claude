"""Configuration loading for session-context skill."""

from pathlib import Path
from typing import Any

import structlog
import yaml

log = structlog.get_logger()

DEFAULT_CONFIG = {
    "session_context": {
        "auto_invoke_agent": True,
        "session_behavior": {
            "startup": "full",
            "resume": "abbreviated",
            "clear": "full",
            "compact": "abbreviated",
        },
        "git": {
            "commit_history_limit": 5,
        },
        "plans": {
            "recent_limit": 3,
        },
    }
}

CONFIG_PATHS = [
    Path("/workspace/.claude/config.yml"),
    Path.home() / ".claude" / "config.yml",
]


def load_config() -> dict[str, Any]:
    """Load session_context config from config.yml, with defaults."""
    for config_path in CONFIG_PATHS:
        if config_path.exists():
            try:
                with open(config_path) as f:
                    full_config = yaml.safe_load(f) or {}
                    session_config = full_config.get("session_context", {})
                    merged = _deep_merge(DEFAULT_CONFIG["session_context"], session_config)
                    log.debug("config_loaded", path=str(config_path))
                    return merged
            except Exception as e:
                log.warning("config_load_failed", path=str(config_path), error=str(e))
                continue

    log.debug("using_default_config")
    return DEFAULT_CONFIG["session_context"]


def get_session_behavior(config: dict[str, Any], session_type: str) -> str:
    """Get behavior mode for session type."""
    behaviors = config.get("session_behavior", {})
    return behaviors.get(session_type, "full")


def get_git_config(config: dict[str, Any]) -> dict[str, Any]:
    """Get git-specific configuration."""
    return config.get("git", {"commit_history_limit": 5})


def get_plans_config(config: dict[str, Any]) -> dict[str, Any]:
    """Get plans-specific configuration."""
    return config.get("plans", {"recent_limit": 3})


def _deep_merge(base: dict, override: dict) -> dict:
    """Deep merge override into base dict."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result
