"""Parse plan markdown files."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import structlog

logger = structlog.get_logger()


@dataclass
class PlanInfo:
    """Extracted information from a plan file."""

    path: Path
    topic: str = ""
    objective: str = ""
    summary: str = ""
    status: str = ""
    completed_todos: list[str] = field(default_factory=list)
    pending_todos: list[str] = field(default_factory=list)


def extract_plan_info(plan_path: Path) -> PlanInfo:
    """Extract key information from a plan markdown file."""
    info = PlanInfo(path=plan_path)

    # Extract topic from filename (e.g., 20251213_133723_stack-manager.md)
    filename = plan_path.stem
    parts = filename.split("_", 2)
    if len(parts) >= 3:
        info.topic = parts[2]

    content = plan_path.read_text()
    lines = content.splitlines()

    # Extract title (first # heading)
    for line in lines:
        if line.startswith("# "):
            info.objective = line[2:].strip()
            # Clean "Plan: " prefix if present
            info.objective = re.sub(r"^Plan:\s*", "", info.objective)
            break

    # Extract status
    status_match = re.search(r"\*\*Status:\*\*\s*(.+?)(?:\n|$)", content)
    if status_match:
        info.status = status_match.group(1).strip()

    # Extract summary section
    summary_match = re.search(
        r"## Summary\s*\n(.*?)(?=\n##|\Z)",
        content,
        re.DOTALL,
    )
    if summary_match:
        info.summary = summary_match.group(1).strip()

    # Extract TODOs from various formats
    # Format 1: ## TODO List with checkboxes
    todo_section = re.search(r"## TODO\s*(?:List)?\s*\n(.*?)(?=\n##|\Z)", content, re.DOTALL)
    if todo_section:
        _parse_todos(todo_section.group(1), info)

    # Format 2: ## Completed section
    completed_section = re.search(r"## Completed\s*\n(.*?)(?=\n##|\Z)", content, re.DOTALL)
    if completed_section:
        for line in completed_section.group(1).splitlines():
            line = line.strip()
            if line.startswith("- [x]") or line.startswith("- [X]"):
                info.completed_todos.append(line[6:].strip())

    return info


def _parse_todos(content: str, info: PlanInfo) -> None:
    """Parse TODO items from content."""
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("- [x]") or line.startswith("- [X]"):
            info.completed_todos.append(line[6:].strip())
        elif line.startswith("- [ ]"):
            info.pending_todos.append(line[6:].strip())


def find_active_plan(plans_dir: Path) -> Optional[PlanInfo]:
    """Find the most recent active plan (not completed)."""
    if not plans_dir.exists():
        return None

    plan_files = sorted(
        plans_dir.glob("*.md"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    for plan_file in plan_files[:5]:
        info = extract_plan_info(plan_file)

        # Skip completed plans
        if info.status.upper() in ("COMPLETED", "COMPLETE"):
            continue

        # If has pending TODOs, it's likely active
        if info.pending_todos:
            return info

        # If recently modified and has completed TODOs, might be current
        if info.completed_todos:
            return info

    # Return most recent plan with info
    for plan_file in plan_files[:3]:
        info = extract_plan_info(plan_file)
        if info.objective:
            return info

    return None
