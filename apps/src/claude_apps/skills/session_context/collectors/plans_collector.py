"""Recent plans collector."""

import re
from pathlib import Path
from typing import Any

import structlog

log = structlog.get_logger()

PLANS_DIRS = [
    Path("/workspace/.claude/plans"),
    Path.cwd() / "plans",
    Path.cwd() / ".claude" / "plans",
]

PLAN_FILENAME_PATTERN = re.compile(r"^(\d{8})_(\d{6})_(.+)\.md$")


def gather_recent_plans(limit: int = 3, plans_dir: Path | None = None) -> list[dict[str, Any]]:
    """Gather recent plan files.

    Args:
        limit: Maximum number of plans to return
        plans_dir: Specific plans directory to search (default: search common locations)

    Returns:
        List of plan metadata dicts
    """
    if plans_dir and plans_dir.exists():
        search_dirs = [plans_dir]
    else:
        search_dirs = [d for d in PLANS_DIRS if d.exists()]

    if not search_dirs:
        log.debug("no_plans_directory_found")
        return []

    all_plans = []
    for dir_path in search_dirs:
        plans = _scan_plans_directory(dir_path)
        all_plans.extend(plans)

    # Sort by date (newest first) and limit
    all_plans.sort(key=lambda p: p.get("sort_key", ""), reverse=True)
    return all_plans[:limit]


def _scan_plans_directory(plans_dir: Path) -> list[dict[str, Any]]:
    """Scan a directory for plan files."""
    plans = []

    for file_path in plans_dir.glob("*.md"):
        plan_info = _parse_plan_file(file_path)
        if plan_info:
            plans.append(plan_info)

    return plans


def _parse_plan_file(file_path: Path) -> dict[str, Any] | None:
    """Parse a plan file and extract metadata."""
    filename = file_path.name
    match = PLAN_FILENAME_PATTERN.match(filename)

    if match:
        date_str, time_str, topic = match.groups()
        formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
        formatted_time = f"{time_str[:2]}:{time_str[2:4]}:{time_str[4:]}"
    else:
        # Non-standard filename, use mtime
        stat = file_path.stat()
        from datetime import datetime
        mtime = datetime.fromtimestamp(stat.st_mtime)
        formatted_date = mtime.strftime("%Y-%m-%d")
        formatted_time = mtime.strftime("%H:%M:%S")
        topic = file_path.stem
        date_str = mtime.strftime("%Y%m%d")
        time_str = mtime.strftime("%H%M%S")

    has_incomplete_todos = _check_incomplete_todos(file_path)

    return {
        "filename": filename,
        "path": str(file_path),
        "topic": topic,
        "date": formatted_date,
        "time": formatted_time,
        "has_incomplete_todos": has_incomplete_todos,
        "sort_key": f"{date_str}_{time_str}",
    }


def _check_incomplete_todos(file_path: Path) -> bool:
    """Check if plan file has incomplete TODO items."""
    try:
        content = file_path.read_text()
        # Look for unchecked checkboxes or TODO markers
        patterns = [
            r"\[ \]",           # Unchecked markdown checkbox
            r"- pending",       # Status: pending
            r"in_progress",     # Status: in_progress
            r"TODO:",           # TODO marker
        ]
        for pattern in patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True
        return False
    except Exception as e:
        log.warning("plan_read_failed", path=str(file_path), error=str(e))
        return False
