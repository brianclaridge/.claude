"""Read cloud provider configuration from config.yml."""

import sys
from pathlib import Path
from typing import Any

# Add shared module to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from shared.config import get_global_config


def load_cloud_providers() -> dict[str, Any]:
    """Load cloud_providers section from config.yml.

    Returns:
        Dictionary of provider configurations, empty dict if not found
    """
    config = get_global_config()
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
