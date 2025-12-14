"""Git operations for submodule updates."""

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

import structlog

log = structlog.get_logger()

WORKSPACE_PATH = os.environ.get("WORKSPACE_PATH", "/workspace")
CLAUDE_PROJECT_SLUG = os.environ.get("CLAUDE_PROJECT_SLUG", "")


@dataclass
class UpdateResult:
    """Result of a check/update operation."""

    checked: bool = False
    updated: bool = False
    old_commit: str = ""
    new_commit: str = ""
    commits_behind: int = 0
    commits_pulled: list[str] | None = None
    error: str | None = None


def get_submodule_path() -> Path:
    """Get the path to the .claude submodule."""
    return Path(f"{WORKSPACE_PATH}{CLAUDE_PROJECT_SLUG}/.claude")


def is_git_repo(path: Path) -> bool:
    """Check if path is a git repository."""
    git_dir = path / ".git"
    return git_dir.exists() or (path / "HEAD").exists()


def run_git_command(args: list[str], cwd: Path) -> tuple[bool, str]:
    """Run a git command and return success status and output."""
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            return True, result.stdout.strip()
        return False, result.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, "Command timed out"
    except Exception as e:
        return False, str(e)


def check_and_update() -> UpdateResult:
    """Check for updates and apply them if available."""
    result = UpdateResult()
    submodule_path = get_submodule_path()

    if not submodule_path.exists():
        log.warning("submodule_path_not_found", path=str(submodule_path))
        result.error = "Submodule path does not exist"
        return result

    if not is_git_repo(submodule_path):
        log.warning("not_a_git_repo", path=str(submodule_path))
        result.error = "Not a git repository"
        return result

    # Fetch from origin
    success, output = run_git_command(["fetch", "origin", "--quiet"], submodule_path)
    if not success:
        log.error("git_fetch_failed", error=output)
        result.error = f"Git fetch failed: {output}"
        return result

    result.checked = True

    # Get current HEAD
    success, local_commit = run_git_command(["rev-parse", "HEAD"], submodule_path)
    if not success:
        result.error = f"Failed to get HEAD: {local_commit}"
        return result
    result.old_commit = local_commit

    # Get origin/main
    success, remote_commit = run_git_command(
        ["rev-parse", "origin/main"], submodule_path
    )
    if not success:
        result.error = f"Failed to get origin/main: {remote_commit}"
        return result
    result.new_commit = remote_commit

    # Check if already up to date
    if local_commit == remote_commit:
        log.info("submodule_up_to_date", commit=local_commit[:8])
        return result

    # Get commits behind count
    success, count_str = run_git_command(
        ["rev-list", "--count", "HEAD..origin/main"], submodule_path
    )
    if success:
        result.commits_behind = int(count_str)

    # Get commit log for what we're pulling
    success, commit_log = run_git_command(
        ["log", "--oneline", "HEAD..origin/main"], submodule_path
    )
    if success:
        result.commits_pulled = commit_log.split("\n") if commit_log else []

    log.info(
        "updates_available",
        local=local_commit[:8],
        remote=remote_commit[:8],
        behind=result.commits_behind,
    )

    # Reset to origin/main
    success, output = run_git_command(
        ["reset", "--hard", "origin/main"], submodule_path
    )
    if not success:
        log.error("git_reset_failed", error=output)
        result.error = f"Git reset failed: {output}"
        return result

    # Clean untracked files
    success, output = run_git_command(["clean", "-fd"], submodule_path)
    if not success:
        log.warning("git_clean_failed", error=output)
        # Don't fail the update for clean issues

    result.updated = True
    log.info(
        "submodule_updated",
        old_commit=local_commit[:8],
        new_commit=remote_commit[:8],
        commits_pulled=result.commits_behind,
    )

    return result
