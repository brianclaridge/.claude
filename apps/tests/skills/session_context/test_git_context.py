"""Tests for git context collector."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from claude_apps.skills.session_context.collectors.git_context import (
    _empty_context,
    _get_recent_commits,
    _get_uncommitted_changes,
    gather_git_context,
)


class TestGatherGitContext:
    """Tests for gather_git_context function."""

    def test_returns_empty_when_not_git_repo(self, tmp_path):
        """Test returns empty context for non-git directory."""
        result = gather_git_context(tmp_path)

        assert result["branch"] is None
        assert result["last_commits"] == []
        assert result["has_pending_work"] is False
        assert "error" in result

    def test_gathers_context_from_git_repo(self, tmp_path):
        """Test gathering context from valid git repo."""
        # Create a minimal git repo
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (git_dir / "HEAD").write_text("ref: refs/heads/main\n")
        (git_dir / "config").write_text("[core]\n\trepositoryformatversion = 0\n")

        # Mock the Repo class - import happens inside function so mock git.Repo
        with patch("git.Repo") as mock_repo_cls:
            mock_repo = MagicMock()
            mock_repo.active_branch.name = "feature-branch"
            mock_repo.working_dir = str(tmp_path)
            mock_repo.head.is_valid.return_value = False
            mock_repo.index.diff.return_value = []
            mock_repo.untracked_files = []
            mock_repo_cls.return_value = mock_repo

            result = gather_git_context(tmp_path)

            assert result["branch"] == "feature-branch"
            assert result["repo_root"] == str(tmp_path)

    def test_handles_detached_head(self, tmp_path):
        """Test handles detached HEAD state."""
        with patch("git.Repo") as mock_repo_cls:
            mock_repo = MagicMock()

            # Simulate TypeError when accessing active_branch.name
            type(mock_repo).active_branch = property(
                lambda self: (_ for _ in ()).throw(TypeError("detached HEAD"))
            )

            mock_repo.working_dir = str(tmp_path)
            mock_repo.head.is_valid.return_value = False
            mock_repo.index.diff.return_value = []
            mock_repo.untracked_files = []
            mock_repo_cls.return_value = mock_repo

            result = gather_git_context(tmp_path)

            assert result["branch"] == "HEAD (detached)"

    def test_uses_cwd_when_no_path(self):
        """Test uses current working directory when no path given."""
        from git.exc import InvalidGitRepositoryError
        with patch("git.Repo") as mock_repo_cls:
            mock_repo_cls.side_effect = InvalidGitRepositoryError("not a git repo")

            result = gather_git_context()  # No path

            assert "error" in result

    def test_handles_invalid_repo(self, tmp_path):
        """Test handles invalid git repository gracefully."""
        from git.exc import InvalidGitRepositoryError
        with patch("git.Repo") as mock_repo_cls:
            mock_repo_cls.side_effect = InvalidGitRepositoryError("not a git repo")

            result = gather_git_context(tmp_path)
            assert "error" in result
            assert result["branch"] is None


class TestGetRecentCommits:
    """Tests for _get_recent_commits helper."""

    def test_returns_empty_for_no_commits(self):
        """Test returns empty list when no commits."""
        mock_repo = MagicMock()
        mock_repo.head.is_valid.return_value = False

        result = _get_recent_commits(mock_repo, limit=5)

        assert result == []

    def test_extracts_commit_info(self):
        """Test extracts commit hash, message, date, author."""
        from datetime import datetime

        mock_commit = MagicMock()
        mock_commit.hexsha = "abc123def456"
        mock_commit.message = "feat: add feature\n\nLong description"
        mock_commit.committed_datetime = datetime(2025, 1, 15, 10, 30)
        mock_commit.author.name = "Test Author"

        mock_repo = MagicMock()
        mock_repo.head.is_valid.return_value = True
        mock_repo.iter_commits.return_value = [mock_commit]

        result = _get_recent_commits(mock_repo, limit=5)

        assert len(result) == 1
        assert result[0]["hash"] == "abc123d"  # First 7 chars
        assert result[0]["message"] == "feat: add feature"  # First line
        assert result[0]["date"] == "2025-01-15"
        assert result[0]["author"] == "Test Author"

    def test_respects_limit(self):
        """Test respects commit limit."""
        from datetime import datetime

        mock_commits = []
        for i in range(10):
            mock_commit = MagicMock()
            mock_commit.hexsha = f"abc{i}def456"
            mock_commit.message = f"commit {i}"
            mock_commit.committed_datetime = datetime(2025, 1, i + 1)
            mock_commit.author.name = "Author"
            mock_commits.append(mock_commit)

        mock_repo = MagicMock()
        mock_repo.head.is_valid.return_value = True
        mock_repo.iter_commits.return_value = mock_commits[:3]  # Only 3 returned

        result = _get_recent_commits(mock_repo, limit=3)

        assert len(result) == 3

    def test_handles_exception(self):
        """Test handles exception gracefully."""
        mock_repo = MagicMock()
        mock_repo.head.is_valid.return_value = True
        mock_repo.iter_commits.side_effect = Exception("git error")

        result = _get_recent_commits(mock_repo, limit=5)

        assert result == []


class TestGetUncommittedChanges:
    """Tests for _get_uncommitted_changes helper."""

    def test_counts_staged_files(self):
        """Test counts staged files against HEAD."""
        mock_repo = MagicMock()
        mock_repo.head.is_valid.return_value = True
        mock_repo.index.diff.side_effect = lambda target: (
            [1, 2, 3] if target == "HEAD" else []  # 3 staged
        )
        mock_repo.untracked_files = []

        result = _get_uncommitted_changes(mock_repo)

        assert result["staged"] == 3
        assert result["unstaged"] == 0
        assert result["untracked"] == 0

    def test_counts_unstaged_files(self):
        """Test counts unstaged modifications."""
        mock_repo = MagicMock()
        mock_repo.head.is_valid.return_value = True
        mock_repo.index.diff.side_effect = lambda target: (
            [] if target == "HEAD" else [1, 2]  # 2 unstaged
        )
        mock_repo.untracked_files = []

        result = _get_uncommitted_changes(mock_repo)

        assert result["staged"] == 0
        assert result["unstaged"] == 2

    def test_counts_untracked_files(self):
        """Test counts untracked files."""
        mock_repo = MagicMock()
        mock_repo.head.is_valid.return_value = True
        mock_repo.index.diff.return_value = []
        mock_repo.untracked_files = ["file1.txt", "file2.txt", "dir/file3.txt"]

        result = _get_uncommitted_changes(mock_repo)

        assert result["untracked"] == 3

    def test_handles_new_repo_no_head(self):
        """Test handles fresh repo with no HEAD."""
        mock_repo = MagicMock()
        mock_repo.head.is_valid.return_value = False
        mock_repo.index.diff.return_value = []
        mock_repo.untracked_files = ["newfile.txt"]

        result = _get_uncommitted_changes(mock_repo)

        assert result["staged"] == 0
        assert result["untracked"] == 1

    def test_handles_exceptions(self):
        """Test handles exceptions gracefully."""
        mock_repo = MagicMock()
        mock_repo.head.is_valid.side_effect = Exception("error")
        mock_repo.index.diff.side_effect = Exception("error")
        mock_repo.untracked_files = property(lambda self: (_ for _ in ()).throw(Exception()))

        result = _get_uncommitted_changes(mock_repo)

        assert result["staged"] == 0
        assert result["unstaged"] == 0
        assert result["untracked"] == 0


class TestEmptyContext:
    """Tests for _empty_context helper."""

    def test_returns_empty_structure(self):
        """Test returns proper empty context structure."""
        result = _empty_context("test reason")

        assert result["branch"] is None
        assert result["last_commits"] == []
        assert result["uncommitted_changes"]["staged"] == 0
        assert result["uncommitted_changes"]["unstaged"] == 0
        assert result["uncommitted_changes"]["untracked"] == 0
        assert result["has_pending_work"] is False
        assert result["error"] == "test reason"
