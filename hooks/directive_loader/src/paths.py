import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any


def get_config() -> Dict[str, Any]:
    config_path = Path(__file__).parent.parent / "config.json"

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, 'r') as f:
        return json.load(f)


def get_workspace_root() -> Path:
    return Path(__file__).parent.parent.parent.parent.parent


def get_log_path(session_id: str, event_name: str) -> Path:
    config = get_config()
    workspace = get_workspace_root()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    log_base = workspace / config["log_base_path"]
    log_dir = log_base / session_id / event_name

    return log_dir / f"{timestamp}.json"


def get_error_log_path(session_id: str) -> Path:
    config = get_config()
    workspace = get_workspace_root()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    log_base = workspace / config["log_base_path"]
    log_dir = log_base / session_id / "errors"

    return log_dir / f"{timestamp}.json"


def get_directives_path() -> str:
    config = get_config()
    workspace = get_workspace_root()
    return str(workspace / config["directives_path"])
