"""Path resolution utilities for Claude Code."""

import os
from pathlib import Path
from typing import Optional


def get_data_path(subpath: Optional[str] = None) -> Path:
    """Get the data directory path.

    Args:
        subpath: Optional subdirectory within data path

    Returns:
        Absolute path to data directory or subdirectory
    """
    data_path = os.environ.get("CLAUDE_DATA_PATH")
    if data_path:
        base = Path(data_path)
    else:
        # Fallback to .claude/.data relative to config
        from .config import get_claude_root
        base = get_claude_root() / ".data"

    if subpath:
        return base / subpath
    return base


def get_logs_path(subpath: Optional[str] = None) -> Path:
    """Get the logs directory path.

    Args:
        subpath: Optional subdirectory within logs path

    Returns:
        Absolute path to logs directory or subdirectory
    """
    logs_path = os.environ.get("CLAUDE_LOGS_PATH")
    if logs_path:
        base = Path(logs_path)
    else:
        base = get_data_path("logs")

    if subpath:
        return base / subpath
    return base


def ensure_directory(path: Path, mode: int = 0o755) -> Path:
    """Ensure a directory exists, creating it if necessary.

    Args:
        path: Directory path to ensure exists
        mode: Permission mode for created directories

    Returns:
        The path that was ensured
    """
    path.mkdir(parents=True, exist_ok=True, mode=mode)
    return path
