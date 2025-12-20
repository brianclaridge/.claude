"""Load Claude API pricing from config file."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import yaml

# Default pricing (fallback if config not found)
DEFAULT_PRICING = {
    "opus": {"input_rate": 15.0, "output_rate": 75.0},
    "sonnet": {"input_rate": 3.0, "output_rate": 15.0},
    "haiku": {"input_rate": 0.80, "output_rate": 4.0},
}
DEFAULT_CACHE = {"read_discount": 0.10, "write_premium": 1.25}
DEFAULT_MODEL = "sonnet"

_pricing_cache: Optional[dict] = None


def _find_config_path() -> Optional[Path]:
    """Find pricing.yml in config directory."""
    claude_path = os.environ.get("CLAUDE_PATH")
    if claude_path:
        return Path(claude_path) / "config" / "pricing.yml"
    # Fallback to relative path from this file
    return Path(__file__).parent.parent.parent.parent / "config" / "pricing.yml"


def get_pricing_config() -> dict:
    """Load pricing config from YAML file with caching.

    Returns:
        Pricing configuration dict with claude_api section.
    """
    global _pricing_cache
    if _pricing_cache is not None:
        return _pricing_cache

    config_path = _find_config_path()
    if config_path and config_path.exists():
        with open(config_path) as f:
            _pricing_cache = yaml.safe_load(f)
    else:
        # Use defaults if config not found
        _pricing_cache = {
            "claude_api": {
                "models": DEFAULT_PRICING,
                "cache": DEFAULT_CACHE,
                "default_model": DEFAULT_MODEL,
            }
        }
    return _pricing_cache


def get_model_rates(model_name: str) -> tuple[float, float]:
    """Get input/output rates for a model.

    Args:
        model_name: Model name string (e.g., "claude-opus-4-5-20251101")

    Returns:
        Tuple of (input_rate, output_rate) per token (not per million).
    """
    config = get_pricing_config()
    api_config = config.get("claude_api", {})
    models = api_config.get("models", DEFAULT_PRICING)
    default = api_config.get("default_model", DEFAULT_MODEL)

    model_lower = model_name.lower()

    # Match model family
    for key in ["opus", "sonnet", "haiku"]:
        if key in model_lower:
            rates = models.get(key, DEFAULT_PRICING[key])
            return rates["input_rate"] / 1_000_000, rates["output_rate"] / 1_000_000

    # Use default model pricing for unknown models
    rates = models.get(default, DEFAULT_PRICING[DEFAULT_MODEL])
    return rates["input_rate"] / 1_000_000, rates["output_rate"] / 1_000_000


def get_cache_multipliers() -> tuple[float, float]:
    """Get cache read discount and write premium multipliers.

    Returns:
        Tuple of (read_discount, write_premium) multipliers.
        - read_discount: 0.10 means pay 10% of input rate
        - write_premium: 1.25 means pay 125% of input rate
    """
    config = get_pricing_config()
    cache = config.get("claude_api", {}).get("cache", DEFAULT_CACHE)
    return cache.get("read_discount", 0.10), cache.get("write_premium", 1.25)
