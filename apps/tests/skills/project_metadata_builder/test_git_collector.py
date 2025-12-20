"""Tests for git metadata collector."""

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from claude_apps.skills.project_metadata_builder.collectors.git_collector import (
    collect_git_metadata,
)
from claude_apps.skills.project_metadata_builder.schema import GitMetadata


class TestCollectGitMetadata:
    """Tests for collect_git_metadata function."""

    def test_returns_empty_for_non_repo(self, tmp_path):
        """Test returns empty metadata for non-git directory."""
        result = collect_git_metadata(tmp_path)

        assert isinstance(result, GitMetadata)
        assert result.remote_url is None
        assert result.branch is None
        assert result.total_commits == 0

    def test_collects_from_valid_repo(self, tmp_path, monkeypatch):
        """Test collecting metadata from valid repo."""
        from git import Repo

        # Create a real git repo
        repo = Repo.init(tmp_path)

        # Configure git user
        repo.config_writer().set_value("user", "name", "Test User").release()
        repo.config_writer().set_value("user", "email", "test@test.com").release()

        # Create initial commit
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        repo.index.add(["test.txt"])
        repo.index.commit("Initial commit")

        result = collect_git_metadata(tmp_path)

        assert result.branch == "master" or result.branch == "main"
        assert result.total_commits >= 1
        assert result.last_commit is not None
        assert result.last_commit.message == "Initial commit"
        assert result.last_commit.author == "Test User"

    def test_handles_no_remote(self, tmp_path):
        """Test handles repo without remote."""
        from git import Repo

        repo = Repo.init(tmp_path)
        repo.config_writer().set_value("user", "name", "Test").release()
        repo.config_writer().set_value("user", "email", "test@test.com").release()

        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        repo.index.add(["test.txt"])
        repo.index.commit("Test")

        result = collect_git_metadata(tmp_path)

        assert result.remote_url is None

    def test_collects_remote_url(self, tmp_path):
        """Test collecting remote URL."""
        from git import Repo

        repo = Repo.init(tmp_path)
        repo.config_writer().set_value("user", "name", "Test").release()
        repo.config_writer().set_value("user", "email", "test@test.com").release()

        # Add a remote
        repo.create_remote("origin", "https://github.com/user/repo.git")

        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        repo.index.add(["test.txt"])
        repo.index.commit("Test")

        result = collect_git_metadata(tmp_path)

        assert result.remote_url == "https://github.com/user/repo.git"

    def test_truncates_commit_hash(self, tmp_path):
        """Test that commit hash is truncated to 12 chars."""
        from git import Repo

        repo = Repo.init(tmp_path)
        repo.config_writer().set_value("user", "name", "Test").release()
        repo.config_writer().set_value("user", "email", "test@test.com").release()

        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        repo.index.add(["test.txt"])
        repo.index.commit("Test")

        result = collect_git_metadata(tmp_path)

        assert len(result.last_commit.hash) == 12

    def test_takes_first_line_of_message(self, tmp_path):
        """Test that only first line of commit message is used."""
        from git import Repo

        repo = Repo.init(tmp_path)
        repo.config_writer().set_value("user", "name", "Test").release()
        repo.config_writer().set_value("user", "email", "test@test.com").release()

        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        repo.index.add(["test.txt"])
        repo.index.commit("First line\n\nBody text\nMore details")

        result = collect_git_metadata(tmp_path)

        assert result.last_commit.message == "First line"
