import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any


def get_config() -> Dict[str, Any]:
    config_path = Path(__file__).parent.parent / "config.json"

    default_config = {
        "log_base_path": "/workspace/.claude/.data/claude_logs"
    }

    try:
        if config_path.exists():
            with open(config_path, 'r') as f:
                return json.load(f)
    except Exception:
        pass

    return default_config


def get_workspace_root() -> Path:
    return Path(__file__).parent.parent.parent.parent.parent


def get_log_path(hook_event_name: str, session_id: str) -> Path:
    config = get_config()
    workspace = get_workspace_root()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    log_base = workspace / config["log_base_path"]
    log_dir = log_base / session_id / hook_event_name

    return log_dir / f"{timestamp}.json"
