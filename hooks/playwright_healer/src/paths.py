"""Path utilities for playwright_healer hook."""

import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "lib"))
from config_helper import get_hook_config, resolve_log_path

from .schemas import PlaywrightHealerConfig


def get_config() -> dict[str, Any]:
    """Load and validate hook configuration from global config.yml."""
    loaded = get_hook_config("playwright_healer")
    validated = PlaywrightHealerConfig(**loaded)
    return validated.model_dump()


def get_log_base() -> Path:
    """Get the log base directory."""
    return resolve_log_path("playwright_healer")


def get_log_path(session_id: str, event_type: str) -> Path:
    """Get path for log file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = get_log_base() / session_id / event_type
    return log_dir / f"{timestamp}.json"


def get_error_log_path(session_id: str) -> Path:
    """Get path for error log file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = get_log_base() / session_id / "errors"
    return log_dir / f"{timestamp}.json"


def get_state_path(session_id: str) -> Path:
    """Get path for recovery state file."""
    state_dir = get_log_base() / session_id / "state"
    return state_dir / "recovery_state.json"
