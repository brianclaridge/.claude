"""Git lock file detection and cleanup."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import structlog

log = structlog.get_logger()

# Lock files that can safely be removed if stale
LOCK_FILES = [
    "index.lock",
    "HEAD.lock",
    "config.lock",
    "refs/heads/*.lock",
    "refs/remotes/*.lock",
]

# How old a lock must be (seconds) before considered stale
STALE_THRESHOLD_SECONDS = 5


@dataclass
class LockCleanResult:
    """Result of lock file cleanup."""

    cleaned: bool
    files_removed: list[str] = field(default_factory=list)
    files_skipped: list[str] = field(default_factory=list)
    error: str | None = None
    exit_code: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "cleaned": self.cleaned,
            "files_removed": self.files_removed,
            "files_skipped": self.files_skipped,
            "error": self.error,
            "exit_code": self.exit_code,
        }


def find_git_dir(repo_path: Path) -> Path | None:
    """Find .git directory, handling submodules.

    Args:
        repo_path: Path to repository or submodule

    Returns:
        Path to git directory or None if not found
    """
    git_path = repo_path / ".git"

    if git_path.is_dir():
        return git_path

    # Check for submodule (file pointing to gitdir)
    if git_path.is_file():
        content = git_path.read_text().strip()
        if content.startswith("gitdir:"):
            gitdir = content[7:].strip()
            # Handle relative paths
            if not Path(gitdir).is_absolute():
                gitdir = repo_path / gitdir
            return Path(gitdir).resolve()

    return None


def find_lock_files(git_dir: Path) -> list[Path]:
    """Find all lock files in git directory.

    Args:
        git_dir: Path to .git directory

    Returns:
        List of lock file paths
    """
    locks = []

    # Direct lock files
    for name in ["index.lock", "HEAD.lock", "config.lock"]:
        lock = git_dir / name
        if lock.exists():
            locks.append(lock)

    # Ref locks
    refs_dir = git_dir / "refs"
    if refs_dir.exists():
        for lock in refs_dir.rglob("*.lock"):
            locks.append(lock)

    # Module locks (for submodules)
    modules_dir = git_dir / "modules"
    if modules_dir.exists():
        for lock in modules_dir.rglob("*.lock"):
            locks.append(lock)

    return locks


def is_stale(lock_path: Path, threshold: int = STALE_THRESHOLD_SECONDS) -> bool:
    """Check if lock file is stale (old enough to remove).

    Args:
        lock_path: Path to lock file
        threshold: Age in seconds before considered stale

    Returns:
        True if lock is stale
    """
    try:
        mtime = lock_path.stat().st_mtime
        age = time.time() - mtime
        return age > threshold
    except OSError:
        return False


def clean_locks(
    repo_path: Path | None = None,
    force: bool = False,
    dry_run: bool = False,
) -> LockCleanResult:
    """Clean stale git lock files.

    Args:
        repo_path: Path to repository (defaults to cwd)
        force: Remove locks regardless of age
        dry_run: Report but don't remove

    Returns:
        LockCleanResult with details
    """
    repo_path = repo_path or Path.cwd()

    # Find git directory
    git_dir = find_git_dir(repo_path)
    if not git_dir:
        return LockCleanResult(
            cleaned=False,
            error=f"Not a git repository: {repo_path}",
            exit_code=1,
        )

    # Find all lock files
    locks = find_lock_files(git_dir)

    if not locks:
        return LockCleanResult(cleaned=True)

    removed = []
    skipped = []

    for lock in locks:
        relative = lock.relative_to(git_dir) if git_dir in lock.parents or lock.parent == git_dir else lock

        if force or is_stale(lock):
            if dry_run:
                log.info("would_remove", lock=str(relative))
                removed.append(str(relative))
            else:
                try:
                    lock.unlink()
                    log.info("removed_lock", lock=str(relative))
                    removed.append(str(relative))
                except OSError as e:
                    log.warning("failed_to_remove", lock=str(relative), error=str(e))
                    skipped.append(str(relative))
        else:
            log.debug("skipped_recent_lock", lock=str(relative))
            skipped.append(str(relative))

    return LockCleanResult(
        cleaned=len(removed) > 0 or len(locks) == 0,
        files_removed=removed,
        files_skipped=skipped,
    )
