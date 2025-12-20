"""Configuration loading for session_context_injector hook."""

from typing import Any

from claude_apps.shared.config_helper import get_hook_config

from .schemas import SessionContextConfig


def load_session_config() -> dict[str, Any]:
    """Load and validate session_context config from hooks.session_context in config.yml."""
    hook_config = get_hook_config("session_context")
    validated = SessionContextConfig(**hook_config)
    return validated.model_dump()
