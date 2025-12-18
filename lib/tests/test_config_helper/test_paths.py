"""Tests for config_helper.paths module."""

import pytest

from config_helper import get_data_path, get_logs_path, ensure_directory


class TestGetDataPath:
    """Tests for get_data_path function."""

    def test_returns_env_path(self, monkeypatch, temp_dir):
        """Should return path from CLAUDE_DATA_PATH env var."""
        data_path = temp_dir / ".data"
        monkeypatch.setenv("CLAUDE_DATA_PATH", str(data_path))
        result = get_data_path()
        assert result == data_path

    def test_returns_subpath(self, monkeypatch, temp_dir):
        """Should append subpath when provided."""
        data_path = temp_dir / ".data"
        monkeypatch.setenv("CLAUDE_DATA_PATH", str(data_path))
        result = get_data_path("cache")
        assert result == data_path / "cache"


class TestGetLogsPath:
    """Tests for get_logs_path function."""

    def test_returns_env_path(self, monkeypatch, temp_dir):
        """Should return path from CLAUDE_LOGS_PATH env var."""
        logs_path = temp_dir / ".data/logs"
        monkeypatch.setenv("CLAUDE_LOGS_PATH", str(logs_path))
        result = get_logs_path()
        assert result == logs_path

    def test_returns_subpath(self, monkeypatch, temp_dir):
        """Should append subpath when provided."""
        logs_path = temp_dir / ".data/logs"
        monkeypatch.setenv("CLAUDE_LOGS_PATH", str(logs_path))
        result = get_logs_path("my_hook")
        assert result == logs_path / "my_hook"


class TestEnsureDirectory:
    """Tests for ensure_directory function."""

    def test_creates_directory(self, temp_dir):
        """Should create directory if it doesn't exist."""
        new_dir = temp_dir / "subdir" / "nested"
        result = ensure_directory(new_dir)
        assert new_dir.exists()
        assert new_dir.is_dir()
        assert result == new_dir

    def test_handles_existing_directory(self, temp_dir):
        """Should not fail if directory exists."""
        existing_dir = temp_dir / "existing"
        existing_dir.mkdir()
        result = ensure_directory(existing_dir)
        assert existing_dir.exists()
        assert result == existing_dir
