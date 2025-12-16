"""Configuration loading for session_context_injector hook."""

import sys
from pathlib import Path
from typing import Any

# Add shared module to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from shared.config import get_hook_config


DEFAULT_CONFIG = {
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


def load_session_config() -> dict[str, Any]:
    """Load session_context config from hooks.session_context in config.yml."""
    hook_config = get_hook_config("session_context")
    return _merge_defaults(hook_config)


def _merge_defaults(config: dict) -> dict:
    """Merge config with defaults."""
    result = DEFAULT_CONFIG.copy()
    result.update(config)
    # Deep merge nested dicts
    if "session_behavior" in config:
        result["session_behavior"] = {
            **DEFAULT_CONFIG["session_behavior"],
            **config["session_behavior"],
        }
    if "git" in config:
        result["git"] = {
            **DEFAULT_CONFIG["git"],
            **config["git"],
        }
    if "plans" in config:
        result["plans"] = {
            **DEFAULT_CONFIG["plans"],
            **config["plans"],
        }
    return result
