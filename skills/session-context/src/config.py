"""Configuration loading for session-context skill."""

import sys
from pathlib import Path
from typing import Any

import structlog

# Add shared module to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from shared.config import get_hook_config

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


def load_config() -> dict[str, Any]:
    """Load session_context config from config.yml via shared module."""
    try:
        hook_config = get_hook_config("session_context")
        merged = _deep_merge(DEFAULT_CONFIG["session_context"], hook_config)
        log.debug("config_loaded_via_shared_module")
        return merged
    except EnvironmentError:
        log.warning("CLAUDE_CONFIG_YML_PATH not set, using defaults")
        return DEFAULT_CONFIG["session_context"]
    except Exception as e:
        log.warning("config_load_failed", error=str(e))
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
