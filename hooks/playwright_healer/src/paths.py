import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any


def get_config() -> Dict[str, Any]:
    """Load configuration from config.json."""
    config_path = Path(__file__).parent.parent / "config.json"

    default_config = {
        "log_base_path": "/workspace/.claude/.data/logs/playwright_healer",
        "log_enabled": True,
        "log_level": "INFO",
        "max_recovery_attempts": 3,
        "recovery_cooldown_seconds": 5,
        "error_patterns": [
            "Browser is already in use",
            "browser context is closed",
            "Target page, context or browser has been closed"
        ]
    }

    try:
        if config_path.exists():
            with open(config_path, 'r') as f:
                loaded = json.load(f)
                default_config.update(loaded)
    except Exception:
        pass

    return default_config


def get_log_base() -> Path:
    """Get the log base directory."""
    config = get_config()
    return Path(config["log_base_path"])


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
