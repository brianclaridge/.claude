"""Tests for submodule updater git operations."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from claude_apps.hooks.submodule_auto_updater.updater import (
    UpdateResult,
    check_and_update,
    is_git_repo,
    run_git_command,
)


class TestUpdateResult:
    """Tests for UpdateResult dataclass."""

    def test_defaults(self):
        """Test default values."""
        result = UpdateResult()

        assert result.checked is False
        assert result.updated is False
        assert result.old_commit == ""
        assert result.new_commit == ""
        assert result.commits_behind == 0
        assert result.commits_pulled is None
        assert result.error is None

    def test_populated_result(self):
        """Test populated result."""
        result = UpdateResult(
            checked=True,
            updated=True,
            old_commit="abc123",
            new_commit="def456",
            commits_behind=3,
            commits_pulled=["abc123 Fix bug", "def456 Add feature"],
        )

        assert result.checked is True
        assert result.updated is True
        assert result.commits_behind == 3


class TestIsGitRepo:
    """Tests for is_git_repo function."""

    def test_returns_true_for_git_dir(self, tmp_path):
        """Test returns True when .git exists."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        assert is_git_repo(tmp_path) is True

    def test_returns_true_for_head_file(self, tmp_path):
        """Test returns True when HEAD exists (worktree)."""
        head_file = tmp_path / "HEAD"
        head_file.write_text("ref: refs/heads/main")

        assert is_git_repo(tmp_path) is True

    def test_returns_false_for_non_git(self, tmp_path):
        """Test returns False for non-git directory."""
        assert is_git_repo(tmp_path) is False


class TestRunGitCommand:
    """Tests for run_git_command function."""

    def test_returns_success_and_output(self, tmp_path):
        """Test returns success and output on success."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="abc123\n",
            )

            success, output = run_git_command(["rev-parse", "HEAD"], tmp_path)

            assert success is True
            assert output == "abc123"

    def test_returns_failure_and_stderr(self, tmp_path):
        """Test returns failure and stderr on error."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stderr="fatal: not a git repository",
            )

            success, output = run_git_command(["status"], tmp_path)

            assert success is False
            assert "not a git repository" in output

    def test_handles_timeout(self, tmp_path):
        """Test handles command timeout."""
        import subprocess

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(cmd="git", timeout=30)

            success, output = run_git_command(["fetch"], tmp_path)

            assert success is False
            assert "timed out" in output.lower()

    def test_handles_exception(self, tmp_path):
        """Test handles generic exception."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = Exception("Command not found")

            success, output = run_git_command(["status"], tmp_path)

            assert success is False
            assert "Command not found" in output


class TestCheckAndUpdate:
    """Tests for check_and_update function."""

    def test_returns_error_when_path_not_exists(self, tmp_path, monkeypatch):
        """Test returns error when submodule path doesn't exist."""
        monkeypatch.setenv("CLAUDE_PATH", str(tmp_path / "nonexistent"))

        with patch(
            "claude_apps.hooks.submodule_auto_updater.updater.get_submodule_path"
        ) as mock_path:
            mock_path.return_value = tmp_path / "nonexistent"

            result = check_and_update()

            assert result.error is not None
            assert "does not exist" in result.error

    def test_returns_error_when_not_git_repo(self, tmp_path, monkeypatch):
        """Test returns error when path is not a git repo."""
        monkeypatch.setenv("CLAUDE_PATH", str(tmp_path))

        with patch(
            "claude_apps.hooks.submodule_auto_updater.updater.get_submodule_path"
        ) as mock_path:
            mock_path.return_value = tmp_path

            result = check_and_update()

            assert result.error is not None
            assert "Not a git repository" in result.error

    def test_returns_error_on_fetch_failure(self, tmp_path, monkeypatch):
        """Test returns error when fetch fails."""
        (tmp_path / ".git").mkdir()
        monkeypatch.setenv("CLAUDE_PATH", str(tmp_path))

        with patch(
            "claude_apps.hooks.submodule_auto_updater.updater.get_submodule_path"
        ) as mock_path:
            mock_path.return_value = tmp_path

            with patch(
                "claude_apps.hooks.submodule_auto_updater.updater.run_git_command"
            ) as mock_git:
                mock_git.return_value = (False, "Network error")

                result = check_and_update()

                assert result.error is not None
                assert "fetch failed" in result.error.lower()

    def test_up_to_date_no_update(self, tmp_path, monkeypatch):
        """Test no update when already up to date."""
        (tmp_path / ".git").mkdir()
        monkeypatch.setenv("CLAUDE_PATH", str(tmp_path))

        with patch(
            "claude_apps.hooks.submodule_auto_updater.updater.get_submodule_path"
        ) as mock_path:
            mock_path.return_value = tmp_path

            with patch(
                "claude_apps.hooks.submodule_auto_updater.updater.run_git_command"
            ) as mock_git:
                # Simulate: fetch OK, HEAD and origin/main are same
                mock_git.side_effect = [
                    (True, ""),  # fetch
                    (True, "abc123"),  # rev-parse HEAD
                    (True, "abc123"),  # rev-parse origin/main
                ]

                result = check_and_update()

                assert result.checked is True
                assert result.updated is False
                assert result.old_commit == "abc123"
                assert result.new_commit == "abc123"

    def test_skips_update_with_local_commits(self, tmp_path, monkeypatch):
        """Test skips update when local commits exist."""
        (tmp_path / ".git").mkdir()
        monkeypatch.setenv("CLAUDE_PATH", str(tmp_path))

        with patch(
            "claude_apps.hooks.submodule_auto_updater.updater.get_submodule_path"
        ) as mock_path:
            mock_path.return_value = tmp_path

            with patch(
                "claude_apps.hooks.submodule_auto_updater.updater.run_git_command"
            ) as mock_git:
                mock_git.side_effect = [
                    (True, ""),  # fetch
                    (True, "local123"),  # rev-parse HEAD
                    (True, "remote456"),  # rev-parse origin/main
                    (True, "2"),  # commits ahead (local commits exist!)
                ]

                result = check_and_update()

                assert result.updated is False
                assert result.error is not None
                assert "unpushed" in result.error.lower()

    def test_performs_update_when_behind(self, tmp_path, monkeypatch):
        """Test performs update when behind origin."""
        (tmp_path / ".git").mkdir()
        monkeypatch.setenv("CLAUDE_PATH", str(tmp_path))

        with patch(
            "claude_apps.hooks.submodule_auto_updater.updater.get_submodule_path"
        ) as mock_path:
            mock_path.return_value = tmp_path

            with patch(
                "claude_apps.hooks.submodule_auto_updater.updater.run_git_command"
            ) as mock_git:
                mock_git.side_effect = [
                    (True, ""),  # fetch
                    (True, "old123"),  # rev-parse HEAD
                    (True, "new456"),  # rev-parse origin/main
                    (True, "0"),  # commits ahead (no local commits)
                    (True, "3"),  # commits behind
                    (True, "abc Fix\ndef Add"),  # commit log
                    (True, ""),  # reset --hard
                    (True, ""),  # clean -fd
                ]

                result = check_and_update()

                assert result.checked is True
                assert result.updated is True
                assert result.old_commit == "old123"
                assert result.new_commit == "new456"
                assert result.commits_behind == 3
