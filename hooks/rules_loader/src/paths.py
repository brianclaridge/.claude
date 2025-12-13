import json
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, Any


def get_hook_config() -> Dict[str, Any]:
    """Load the hook's local config.json."""
    config_path = Path(__file__).parent.parent / "config.json"

    if not config_path.exists():
        raise FileNotFoundError(f"Hook config file not found: {config_path}")

    with open(config_path, 'r') as f:
        return json.load(f)


def get_workspace_root() -> Path:
    """Get the workspace root (parent of .claude/)."""
    return Path(__file__).parent.parent.parent.parent.parent


def get_claude_root() -> Path:
    """Get the .claude/ directory root."""
    return Path(__file__).parent.parent.parent.parent


def get_global_config() -> Dict[str, Any]:
    """Load the global config.yml from .claude/ root."""
    config_path = get_claude_root() / "config.yml"

    if not config_path.exists():
        # Return empty config if file doesn't exist
        return {}

    with open(config_path, 'r') as f:
        return yaml.safe_load(f) or {}


def get_log_path(session_id: str, event_name: str) -> Path:
    """Get the path for a log file."""
    config = get_hook_config()
    workspace = get_workspace_root()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    log_base = workspace / config["log_base_path"]
    log_dir = log_base / session_id / event_name

    return log_dir / f"{timestamp}.json"


def get_error_log_path(session_id: str) -> Path:
    """Get the path for an error log file."""
    config = get_hook_config()
    workspace = get_workspace_root()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    log_base = workspace / config["log_base_path"]
    log_dir = log_base / session_id / "errors"

    return log_dir / f"{timestamp}.json"


def get_rules_path() -> str:
    """Get the path to the rules directory."""
    config = get_hook_config()
    workspace = get_workspace_root()
    return str(workspace / config["rules_path"])
