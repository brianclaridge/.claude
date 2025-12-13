"""Git context collector."""

from pathlib import Path
from typing import Any

import structlog

log = structlog.get_logger()


def gather_git_context(repo_path: Path | None = None, commit_limit: int = 5) -> dict[str, Any]:
    """Gather git context from repository.

    Args:
        repo_path: Path to git repository (default: current working directory)
        commit_limit: Maximum number of recent commits to include

    Returns:
        Git context dict with branch, commits, and changes
    """
    try:
        from git import Repo
        from git.exc import InvalidGitRepositoryError
    except ImportError:
        log.warning("gitpython_not_installed")
        return _empty_context("gitpython not installed")

    if repo_path is None:
        repo_path = Path.cwd()

    try:
        repo = Repo(repo_path, search_parent_directories=True)
    except InvalidGitRepositoryError:
        log.debug("not_a_git_repo", path=str(repo_path))
        return _empty_context("not a git repository")
    except Exception as e:
        log.debug("git_init_failed", path=str(repo_path), error=str(e))
        return _empty_context(f"git init failed: {e}")

    try:
        branch = repo.active_branch.name
    except TypeError:
        branch = "HEAD (detached)"
    except Exception:
        branch = "unknown"

    commits = _get_recent_commits(repo, commit_limit)
    changes = _get_uncommitted_changes(repo)

    return {
        "branch": branch,
        "last_commits": commits,
        "uncommitted_changes": changes,
        "has_pending_work": changes["staged"] > 0 or changes["unstaged"] > 0,
        "repo_root": str(repo.working_dir),
    }


def _get_recent_commits(repo, limit: int) -> list[dict[str, str]]:
    """Get recent commits from repository."""
    commits = []
    try:
        # Check if repo has any commits at all
        try:
            head_valid = repo.head.is_valid()
        except Exception:
            head_valid = False

        if head_valid:
            for commit in repo.iter_commits(max_count=limit):
                commits.append({
                    "hash": commit.hexsha[:7],
                    "message": commit.message.split("\n")[0].strip(),
                    "date": commit.committed_datetime.strftime("%Y-%m-%d"),
                    "author": commit.author.name,
                })
    except Exception as e:
        log.debug("commit_fetch_failed", error=str(e))
    return commits


def _get_uncommitted_changes(repo) -> dict[str, int]:
    """Get count of uncommitted changes."""
    staged = 0
    unstaged = 0
    untracked = 0

    try:
        # Only diff against HEAD if it exists
        try:
            head_valid = repo.head.is_valid()
        except Exception:
            head_valid = False

        if head_valid:
            staged = len(repo.index.diff("HEAD"))
    except Exception:
        pass

    try:
        unstaged = len(repo.index.diff(None))
    except Exception:
        pass

    try:
        untracked = len(repo.untracked_files)
    except Exception:
        pass

    return {
        "staged": staged,
        "unstaged": unstaged,
        "untracked": untracked,
    }


def _empty_context(reason: str) -> dict[str, Any]:
    """Return empty git context with reason."""
    return {
        "branch": None,
        "last_commits": [],
        "uncommitted_changes": {"staged": 0, "unstaged": 0, "untracked": 0},
        "has_pending_work": False,
        "error": reason,
    }
