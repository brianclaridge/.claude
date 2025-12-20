import subprocess
import time
import os
import json
import glob
from typing import Dict, Any
from pathlib import Path
from .paths import get_config, get_state_path
from .logger import log_healing_event


def get_recovery_state(session_id: str) -> Dict[str, Any]:
    """Get current recovery state for session."""
    state_path = get_state_path(session_id)

    if state_path.exists():
        try:
            return json.loads(state_path.read_text())
        except Exception:
            pass

    return {
        "attempt_count": 0,
        "last_attempt_time": 0,
        "last_error_type": None
    }


def save_recovery_state(session_id: str, state: Dict[str, Any]) -> None:
    """Save recovery state for session."""
    state_path = get_state_path(session_id)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state, indent=2))


def should_attempt_recovery(session_id: str, error_type: str) -> bool:
    """Check if recovery should be attempted based on cooldown and max attempts."""
    config = get_config()
    state = get_recovery_state(session_id)

    max_attempts = config.get("max_recovery_attempts", 3)
    cooldown = config.get("recovery_cooldown_seconds", 5)

    if state["last_error_type"] != error_type:
        return True

    if state["attempt_count"] >= max_attempts:
        return False

    time_since_last = time.time() - state["last_attempt_time"]
    if time_since_last < cooldown:
        return False

    return True


def kill_stale_browser_processes() -> Dict[str, Any]:
    """Kill any stale chromium processes that may be holding locks."""
    try:
        result = subprocess.run(
            ["pkill", "-f", "mcp-chromium"],
            capture_output=True,
            timeout=10
        )

        return {
            "success": True,
            "action": "kill_stale_processes",
            "message": "Killed stale chromium processes"
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "action": "kill_stale_processes",
            "error": "Timeout killing processes"
        }
    except Exception as e:
        return {
            "success": False,
            "action": "kill_stale_processes",
            "error": str(e)
        }


def remove_browser_lock_files() -> Dict[str, Any]:
    """Remove browser lock files that may be causing conflicts."""
    lock_patterns = [
        "/usr/local/share/playwright/mcp-chromium-*/SingletonLock",
        "/tmp/.org.chromium.Chromium.*/SingletonLock",
    ]

    removed = []

    try:
        for lock_pattern in lock_patterns:
            for lock_file in glob.glob(lock_pattern):
                try:
                    os.remove(lock_file)
                    removed.append(lock_file)
                except Exception:
                    pass

        return {
            "success": True,
            "action": "remove_lock_files",
            "message": f"Removed {len(removed)} lock files",
            "files_removed": removed
        }
    except Exception as e:
        return {
            "success": False,
            "action": "remove_lock_files",
            "error": str(e)
        }


def attempt_recovery(session_id: str, tool_name: str, error_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Attempt to recover from browser error.

    Recovery strategies based on error type:
    1. browser_lock: Kill stale processes, remove lock files
    2. browser_closed: Signal to reinitialize browser
    3. connection_lost: Kill processes and clean up
    """
    error_type = error_info.get("error_type", "unknown")

    if not should_attempt_recovery(session_id, error_type):
        return {
            "success": False,
            "action": "skipped",
            "error": "Max recovery attempts reached or cooldown active"
        }

    state = get_recovery_state(session_id)
    state["attempt_count"] += 1
    state["last_attempt_time"] = time.time()
    state["last_error_type"] = error_type
    save_recovery_state(session_id, state)

    if error_type == "browser_lock":
        lock_result = remove_browser_lock_files()
        kill_result = kill_stale_browser_processes()

        if lock_result["success"] or kill_result["success"]:
            return {
                "success": True,
                "action": "browser_lock_recovery",
                "message": f"Lock files: {lock_result.get('message', 'N/A')}, Processes: {kill_result.get('message', 'N/A')}"
            }
        else:
            return {
                "success": False,
                "action": "browser_lock_recovery",
                "error": f"Lock removal: {lock_result.get('error', 'N/A')}, Process kill: {kill_result.get('error', 'N/A')}"
            }

    elif error_type == "browser_closed":
        return {
            "success": True,
            "action": "browser_closed_recovery",
            "message": "Browser was closed. Retry will reinitialize."
        }

    elif error_type == "connection_lost":
        kill_result = kill_stale_browser_processes()

        return {
            "success": True,
            "action": "connection_recovery",
            "message": f"Connection recovery attempted. {kill_result.get('message', '')}"
        }

    else:
        return {
            "success": False,
            "action": "unknown",
            "error": f"No recovery strategy for error type: {error_type}"
        }
