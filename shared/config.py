"""Shared configuration loading for Claude Code hooks."""

import os
from pathlib import Path
from typing import Any

import yaml


def get_config_path() -> Path:
    """Get the config.yml path from CONFIG_YML_PATH environment variable.

    This is a required environment variable with no fallback.
    """
    config_path = os.environ.get("CONFIG_YML_PATH")
    if not config_path:
        raise EnvironmentError("CONFIG_YML_PATH environment variable is required")
    return Path(config_path)


def get_claude_root() -> Path:
    """Get the .claude/ directory root (parent of config.yml)."""
    return get_config_path().parent


def get_workspace_root() -> Path:
    """Get the workspace root (parent of .claude/)."""
    return get_claude_root().parent


def get_global_config() -> dict[str, Any]:
    """Load the global config.yml."""
    config_path = get_config_path()

    if not config_path.exists():
        return {}

    with open(config_path) as f:
        return yaml.safe_load(f) or {}


def get_hook_config(hook_name: str) -> dict[str, Any]:
    """Load configuration for a specific hook from global config.

    Args:
        hook_name: Name of the hook (e.g., 'logger', 'playwright_healer')

    Returns:
        Hook configuration dictionary, empty if not found
    """
    global_config = get_global_config()
    hooks_config = global_config.get("hooks", {})
    return hooks_config.get(hook_name, {})


def resolve_log_path(hook_name: str) -> Path:
    """Resolve the absolute log path for a hook.

    Args:
        hook_name: Name of the hook

    Returns:
        Absolute path to log directory
    """
    config = get_hook_config(hook_name)
    relative_path = config.get("log_base_path", f".data/logs/{hook_name}")
    return get_claude_root() / relative_path
