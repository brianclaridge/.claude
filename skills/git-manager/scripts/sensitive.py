"""Detect sensitive files in git staging area."""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import structlog

logger = structlog.get_logger()

# Sensitive file patterns
SENSITIVE_PATTERNS = [
    r"\.env$",
    r"\.env\.",
    r"\.pem$",
    r"\.key$",
    r"\.p12$",
    r"\.pfx$",
    r"credentials",
    r"secret",
    r"aws-exports\.js$",
    r"\.htpasswd$",
    r"id_rsa",
    r"id_ed25519",
    r"\.kube/config",
]

# Excluded patterns (safe to commit)
SAFE_PATTERNS = [
    r"\.env\.example$",
    r"\.env\.template$",
    r"\.env\.sample$",
]


@dataclass
class SensitiveFile:
    """A detected sensitive file."""

    path: str
    pattern_matched: str
    status: str  # "new", "modified", "staged"


@dataclass
class SensitiveResult:
    """Result of sensitive file scan."""

    found: bool = False
    files: list[SensitiveFile] = field(default_factory=list)
    exit_code: int = 0
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "found": self.found,
            "files": [
                {
                    "path": f.path,
                    "pattern": f.pattern_matched,
                    "status": f.status,
                }
                for f in self.files
            ],
            "error": self.error,
        }


def get_status_files(repo_path: Path) -> list[tuple[str, str]]:
    """Get files from git status --porcelain."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            cwd=repo_path,
            timeout=10,
        )
        if result.returncode != 0:
            return []

        files = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            status = line[:2].strip()
            path = line[3:]

            # Map status codes
            if status in ["A", "M", "AM", "MM"]:
                files.append((path, "staged" if status[0] != " " else "modified"))
            elif status == "??":
                files.append((path, "new"))
            elif status:
                files.append((path, "modified"))

        return files
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
        logger.error("status_failed", error=str(e))
        return []


def is_safe_pattern(path: str) -> bool:
    """Check if file matches safe pattern (e.g., .env.example)."""
    for pattern in SAFE_PATTERNS:
        if re.search(pattern, path, re.IGNORECASE):
            return True
    return False


def scan_sensitive(repo_path: Path) -> SensitiveResult:
    """Scan git status for sensitive files."""
    result = SensitiveResult()

    files = get_status_files(repo_path)
    if not files:
        result.exit_code = 0
        return result

    for path, status in files:
        # Skip safe patterns
        if is_safe_pattern(path):
            continue

        # Check against sensitive patterns
        for pattern in SENSITIVE_PATTERNS:
            if re.search(pattern, path, re.IGNORECASE):
                result.files.append(
                    SensitiveFile(
                        path=path,
                        pattern_matched=pattern,
                        status=status,
                    )
                )
                break

    if result.files:
        result.found = True
        result.exit_code = 1  # Warn about sensitive files
        logger.warning(
            "sensitive_files_found",
            count=len(result.files),
            files=[f.path for f in result.files],
        )
    else:
        result.exit_code = 0

    return result
