"""State file management for submodule auto-updater."""

import json
import os
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

import structlog

from .updater import UpdateResult

log = structlog.get_logger()

WORKSPACE_PATH = os.environ.get("CLAUDE_WORKSPACE_PATH")
DATA_DIR = os.environ.get("CLAUDE_DATA_PATH")

CHECK_STATE_FILE = DATA_DIR / "submodule_check_state.json"
NOTIFY_STATE_FILE = DATA_DIR / "submodule_notify_state.json"

# Check interval in seconds (15 minutes)
CHECK_INTERVAL_SECONDS = 15 * 60


def ensure_data_dir() -> None:
    """Ensure the data directory exists."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def read_check_state() -> dict[str, Any]:
    """Read the check state file."""
    if not CHECK_STATE_FILE.exists():
        return {}
    try:
        return json.loads(CHECK_STATE_FILE.read_text())
    except Exception as e:
        log.warning("failed_to_read_check_state", error=str(e))
        return {}


def write_check_state(update_result: UpdateResult | None = None) -> None:
    """Write the check state file with current time and optional update result."""
    ensure_data_dir()

    state = read_check_state()
    state["last_check_time"] = time.time()
    state["last_check_iso"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")

    if update_result and update_result.updated:
        state["last_update_time"] = time.time()
        state["last_update_result"] = {
            "updated": update_result.updated,
            "old_commit": update_result.old_commit,
            "new_commit": update_result.new_commit,
            "commits_behind": update_result.commits_behind,
            "commits_pulled": update_result.commits_pulled or [],
        }

    try:
        CHECK_STATE_FILE.write_text(json.dumps(state, indent=2))
    except Exception as e:
        log.error("failed_to_write_check_state", error=str(e))


def should_check() -> bool:
    """Check if enough time has passed since last check."""
    state = read_check_state()
    last_check = state.get("last_check_time", 0)
    elapsed = time.time() - last_check

    should = elapsed >= CHECK_INTERVAL_SECONDS
    log.debug(
        "check_interval_evaluation",
        elapsed_seconds=int(elapsed),
        interval_seconds=CHECK_INTERVAL_SECONDS,
        should_check=should,
    )
    return should


def read_notify_state() -> dict[str, Any]:
    """Read the notification state file."""
    if not NOTIFY_STATE_FILE.exists():
        return {}
    try:
        return json.loads(NOTIFY_STATE_FILE.read_text())
    except Exception as e:
        log.warning("failed_to_read_notify_state", error=str(e))
        return {}


def should_notify(session_id: str) -> bool:
    """Check if we should notify for this session (throttling)."""
    state = read_notify_state()
    last_session = state.get("last_notified_session")

    # Don't re-notify in the same session
    if last_session == session_id:
        log.debug("skipping_notification", reason="same_session")
        return False

    return True


def mark_notified(session_id: str) -> None:
    """Record that we notified in this session."""
    ensure_data_dir()

    state = {
        "last_notified_session": session_id,
        "last_notified_time": time.time(),
        "last_notified_iso": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }

    try:
        NOTIFY_STATE_FILE.write_text(json.dumps(state, indent=2))
    except Exception as e:
        log.error("failed_to_write_notify_state", error=str(e))
