"""Pending work detection."""

from pathlib import Path
from typing import Any

import structlog

from .git_context import gather_git_context
from .plans_collector import gather_recent_plans

log = structlog.get_logger()


def detect_pending_work(
    repo_path: Path | None = None,
    plans_dir: Path | None = None,
) -> dict[str, Any]:
    """Detect pending/unfinished work.

    Checks for:
    - Uncommitted git changes
    - Incomplete TODOs in recent plans
    - Unfinished branches (if applicable)

    Args:
        repo_path: Path to git repository
        plans_dir: Path to plans directory

    Returns:
        Pending work summary
    """
    git_context = gather_git_context(repo_path, commit_limit=1)
    recent_plans = gather_recent_plans(limit=5, plans_dir=plans_dir)

    # Check git pending work
    git_pending = git_context.get("has_pending_work", False)
    uncommitted = git_context.get("uncommitted_changes", {})

    # Check plans pending work
    plans_with_todos = [p for p in recent_plans if p.get("has_incomplete_todos", False)]

    has_pending_work = git_pending or len(plans_with_todos) > 0

    return {
        "has_pending_work": has_pending_work,
        "git_pending": {
            "has_changes": git_pending,
            "staged": uncommitted.get("staged", 0),
            "unstaged": uncommitted.get("unstaged", 0),
            "untracked": uncommitted.get("untracked", 0),
        },
        "plans_pending": {
            "count": len(plans_with_todos),
            "files": [p["filename"] for p in plans_with_todos],
        },
        "summary": _build_summary(git_pending, uncommitted, plans_with_todos),
    }


def _build_summary(git_pending: bool, uncommitted: dict, plans_with_todos: list) -> str:
    """Build human-readable pending work summary."""
    parts = []

    if git_pending:
        changes = []
        if uncommitted.get("staged", 0) > 0:
            changes.append(f"{uncommitted['staged']} staged")
        if uncommitted.get("unstaged", 0) > 0:
            changes.append(f"{uncommitted['unstaged']} unstaged")
        if uncommitted.get("untracked", 0) > 0:
            changes.append(f"{uncommitted['untracked']} untracked")
        if changes:
            parts.append(f"Git: {', '.join(changes)} files")

    if plans_with_todos:
        parts.append(f"Plans: {len(plans_with_todos)} with incomplete TODOs")

    if not parts:
        return "No pending work detected"

    return "; ".join(parts)
