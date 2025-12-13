"""Configuration loading for session_context_injector hook."""

from pathlib import Path
from typing import Any

import yaml

CONFIG_PATHS = [
    Path("/workspace/.claude/config.yml"),
    Path.home() / ".claude" / "config.yml",
]

DEFAULT_CONFIG = {
    "auto_invoke_agent": True,
    "session_behavior": {
        "startup": "full",
        "resume": "abbreviated",
        "clear": "full",
        "compact": "abbreviated",
    },
}


def load_session_config() -> dict[str, Any]:
    """Load session_context config from config.yml."""
    for config_path in CONFIG_PATHS:
        if config_path.exists():
            try:
                with open(config_path) as f:
                    full_config = yaml.safe_load(f) or {}
                    session_config = full_config.get("session_context", {})
                    return _merge_defaults(session_config)
            except Exception:
                continue
    return DEFAULT_CONFIG


def _merge_defaults(config: dict) -> dict:
    """Merge config with defaults."""
    result = DEFAULT_CONFIG.copy()
    result.update(config)
    if "session_behavior" in config:
        result["session_behavior"] = {
            **DEFAULT_CONFIG["session_behavior"],
            **config["session_behavior"],
        }
    return result
