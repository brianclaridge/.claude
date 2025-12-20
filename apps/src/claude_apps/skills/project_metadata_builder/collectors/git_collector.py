"""
Git metadata collector.
"""
from datetime import datetime
from pathlib import Path

from git import InvalidGitRepositoryError, Repo
from loguru import logger

from ..schema import GitCommit, GitMetadata


def collect_git_metadata(project_path: Path) -> GitMetadata:
    """Collect git metadata from a project directory."""
    metadata = GitMetadata()

    try:
        repo = Repo(project_path)
    except InvalidGitRepositoryError:
        logger.warning(f"Not a git repository: {project_path}")
        return metadata

    try:
        # Get remote URL
        if repo.remotes:
            metadata.remote_url = repo.remotes.origin.url
    except Exception as e:
        logger.debug(f"Could not get remote URL: {e}")

    try:
        # Get current branch
        metadata.branch = repo.active_branch.name
    except Exception as e:
        logger.debug(f"Could not get branch: {e}")

    try:
        # Get commit count
        metadata.total_commits = len(list(repo.iter_commits()))
    except Exception as e:
        logger.debug(f"Could not count commits: {e}")

    try:
        # Get last commit
        if repo.head.is_valid():
            commit = repo.head.commit
            metadata.last_commit = GitCommit(
                hash=commit.hexsha[:12],
                message=commit.message.strip().split("\n")[0],  # First line only
                author=commit.author.name,
                date=datetime.fromtimestamp(commit.committed_date),
            )
    except Exception as e:
        logger.debug(f"Could not get last commit: {e}")

    logger.info(
        f"Collected git metadata: branch={metadata.branch}, "
        f"commits={metadata.total_commits}"
    )
    return metadata
