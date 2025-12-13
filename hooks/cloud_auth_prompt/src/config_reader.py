"""Read cloud provider configuration from config.yml."""

from pathlib import Path
from typing import Any

import yaml


def get_config_path() -> Path:
    """Get path to config.yml.

    Returns:
        Path to .claude/config.yml
    """
    # Hook runs from .claude directory
    return Path(__file__).parent.parent.parent.parent / "config.yml"


def load_cloud_providers() -> dict[str, Any]:
    """Load cloud_providers section from config.yml.

    Returns:
        Dictionary of provider configurations, empty dict if not found
    """
    config_path = get_config_path()

    if not config_path.exists():
        return {}

    with open(config_path) as f:
        config = yaml.safe_load(f) or {}

    return config.get("cloud_providers", {})


def get_enabled_providers() -> list[dict[str, Any]]:
    """Get list of enabled cloud providers.

    Returns:
        List of provider configs with 'name' key added
    """
    providers = load_cloud_providers()
    enabled = []

    for name, config in providers.items():
        if config.get("enabled", False) and config.get("prompt_at_start", False):
            enabled.append({
                "name": name,
                "display_name": config.get("display_name", name.upper()),
                "description": config.get("description", f"Login to {name.upper()}"),
            })

    return enabled
