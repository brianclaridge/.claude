"""Commit message generation from plans and diff."""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import structlog

from .plan import find_active_plan, PlanInfo
from .stats import get_session_stats, format_stats_section

logger = structlog.get_logger()

# Scope inference patterns
SCOPE_PATTERNS = {
    "auth": [r"auth", r"login", r"session", r"oauth"],
    "api": [r"api/", r"endpoint", r"route"],
    "ui": [r"component", r"page", r"view", r"\.tsx?$", r"\.vue$"],
    "db": [r"model", r"migration", r"schema", r"database"],
    "config": [r"config", r"settings", r"\.env", r"\.yaml$", r"\.toml$"],
    "skill": [r"skills/", r"skill\.md", r"SKILL\.md"],
    "agent": [r"agents/", r"agent\.md"],
    "hook": [r"hooks/"],
    "test": [r"test", r"spec", r"_test\."],
    "docs": [r"docs/", r"README", r"\.md$"],
}


@dataclass
class MessageResult:
    """Result of message generation."""

    type: str = "chore"
    scope: Optional[str] = None
    subject: str = ""
    body: str = ""
    full_message: str = ""
    files_changed: int = 0
    plan_reference: Optional[str] = None
    exit_code: int = 0
    error: Optional[str] = None
    session_stats: Optional[dict] = None

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "scope": self.scope,
            "subject": self.subject,
            "body": self.body,
            "full_message": self.full_message,
            "files_changed": self.files_changed,
            "plan_reference": self.plan_reference,
            "error": self.error,
            "session_stats": self.session_stats,
        }


def get_diff_stat(repo_path: Path) -> tuple[list[str], int]:
    """Get list of changed files and count."""
    try:
        # Try staged first
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True,
            text=True,
            cwd=repo_path,
            timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            files = [f for f in result.stdout.strip().split("\n") if f]
            if files:
                return files, len(files)

        # Fallback to unstaged
        result = subprocess.run(
            ["git", "diff", "--name-only"],
            capture_output=True,
            text=True,
            cwd=repo_path,
            timeout=10,
        )
        if result.returncode == 0:
            files = [f for f in result.stdout.strip().split("\n") if f]
            return files, len(files)

        # Try status for untracked
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            cwd=repo_path,
            timeout=10,
        )
        if result.returncode == 0:
            files = []
            for line in result.stdout.strip().split("\n"):
                if line:
                    files.append(line[3:])
            return files, len(files)

    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
        logger.error("diff_stat_failed", error=str(e))

    return [], 0


def infer_scope(files: list[str]) -> Optional[str]:
    """Infer scope from file patterns."""
    scope_scores: dict[str, int] = {}

    for file in files:
        for scope, patterns in SCOPE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, file, re.IGNORECASE):
                    scope_scores[scope] = scope_scores.get(scope, 0) + 1

    if scope_scores:
        return max(scope_scores, key=scope_scores.get)
    return None


def infer_type(plan_info: Optional[PlanInfo], files: list[str]) -> str:
    """Infer commit type from plan and files."""
    if plan_info:
        objective = plan_info.objective.lower()
        if any(w in objective for w in ["fix", "bug", "issue", "error"]):
            return "fix"
        if any(w in objective for w in ["add", "implement", "create", "new"]):
            return "feat"
        if any(w in objective for w in ["refactor", "restructure", "clean", "move", "relocate"]):
            return "refactor"
        if any(w in objective for w in ["document", "readme", "docs"]):
            return "docs"
        if any(w in objective for w in ["test"]):
            return "test"

    # Infer from files
    if files and all(re.search(r"test|spec", f, re.IGNORECASE) for f in files):
        return "test"
    if files and all(re.search(r"\.md$|docs/", f, re.IGNORECASE) for f in files):
        return "docs"

    return "chore"


def generate_message(
    repo_path: Path,
    plans_dir: Optional[Path] = None,
    claude_plans_dir: Optional[Path] = None,
) -> MessageResult:
    """Generate commit message from context."""
    result = MessageResult()

    # Get changed files
    files, count = get_diff_stat(repo_path)
    result.files_changed = count

    if count == 0:
        result.exit_code = 1
        result.error = "No changes detected"
        return result

    # Find active plan
    plan_info = None
    plan_dirs = [d for d in [plans_dir, claude_plans_dir] if d and d.exists()]

    for d in plan_dirs:
        plan_info = find_active_plan(d)
        if plan_info:
            result.plan_reference = plan_info.topic
            break

    # Infer type and scope
    result.type = infer_type(plan_info, files)
    result.scope = infer_scope(files)

    # Generate subject
    if plan_info and plan_info.objective:
        # Clean objective for subject line
        subject = plan_info.objective.lower()
        subject = re.sub(r"^(implement|add|create|fix|update|refactor)\s+", "", subject)
        result.subject = subject[:50]
    else:
        result.subject = f"update {count} files"

    # Build full message
    scope_str = f"({result.scope})" if result.scope else ""
    header = f"{result.type}{scope_str}: {result.subject}"

    body_parts = []

    # Summary from plan
    if plan_info and plan_info.summary:
        body_parts.append("## Summary\n")
        body_parts.append(plan_info.summary)
        body_parts.append("")

    # Changes from plan TODOs
    if plan_info and plan_info.completed_todos:
        body_parts.append("## Changes\n")
        for todo in plan_info.completed_todos[:10]:
            body_parts.append(f"- {todo}")
        body_parts.append("")

    # Plan reference
    if result.plan_reference:
        body_parts.append("## Plan Reference\n")
        body_parts.append(f"Implementation of: {result.plan_reference}")
        body_parts.append("")

    # Files modified
    body_parts.append("## Files Modified\n")
    body_parts.append(f"{count} files changed")

    # Session statistics
    stats = get_session_stats(repo_path)
    stats_section = format_stats_section(stats)
    if stats_section:
        body_parts.append("")
        body_parts.append(stats_section)
    result.session_stats = stats.to_dict()

    result.body = "\n".join(body_parts)
    result.full_message = f"{header}\n\n{result.body}"
    result.exit_code = 0

    return result
