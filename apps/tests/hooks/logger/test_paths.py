"""Tests for logger hook path utilities."""

import re
from pathlib import Path
from unittest.mock import patch

import pytest

from claude_apps.hooks.logger.paths import DEFAULT_CONFIG, get_config, get_log_path


class TestDefaultConfig:
    """Tests for default configuration values."""

    def test_has_log_base_path(self):
        """Test has log base path."""
        assert "log_base_path" in DEFAULT_CONFIG

    def test_has_log_enabled(self):
        """Test has log enabled flag."""
        assert "log_enabled" in DEFAULT_CONFIG
        assert DEFAULT_CONFIG["log_enabled"] is True

    def test_has_log_level(self):
        """Test has log level."""
        assert "log_level" in DEFAULT_CONFIG
        assert DEFAULT_CONFIG["log_level"] == "INFO"


class TestGetConfig:
    """Tests for get_config function."""

    def test_returns_default_values(self):
        """Test returns default values when no hook config."""
        with patch(
            "claude_apps.hooks.logger.paths.get_hook_config", return_value={}
        ):
            config = get_config()

            assert config["log_enabled"] is True
            assert config["log_level"] == "INFO"

    def test_merges_with_hook_config(self):
        """Test merges with hook configuration."""
        with patch(
            "claude_apps.hooks.logger.paths.get_hook_config",
            return_value={"log_level": "DEBUG", "custom_key": "value"},
        ):
            config = get_config()

            assert config["log_level"] == "DEBUG"
            assert config["custom_key"] == "value"
            # Default still present
            assert config["log_enabled"] is True

    def test_hook_config_overrides_defaults(self):
        """Test hook config overrides defaults."""
        with patch(
            "claude_apps.hooks.logger.paths.get_hook_config",
            return_value={"log_enabled": False},
        ):
            config = get_config()

            assert config["log_enabled"] is False


class TestGetLogPath:
    """Tests for get_log_path function."""

    def test_returns_path_object(self):
        """Test returns Path object."""
        with patch(
            "claude_apps.hooks.logger.paths.resolve_log_path",
            return_value=Path("/logs"),
        ):
            result = get_log_path("SessionStart", "session123")

            assert isinstance(result, Path)

    def test_includes_session_id_in_path(self):
        """Test includes session ID in path."""
        with patch(
            "claude_apps.hooks.logger.paths.resolve_log_path",
            return_value=Path("/logs"),
        ):
            result = get_log_path("SessionStart", "session123")

            assert "session123" in str(result)

    def test_includes_hook_event_name_in_path(self):
        """Test includes hook event name in path."""
        with patch(
            "claude_apps.hooks.logger.paths.resolve_log_path",
            return_value=Path("/logs"),
        ):
            result = get_log_path("UserPromptSubmit", "session123")

            assert "UserPromptSubmit" in str(result)

    def test_includes_timestamp_in_filename(self):
        """Test includes timestamp in filename."""
        with patch(
            "claude_apps.hooks.logger.paths.resolve_log_path",
            return_value=Path("/logs"),
        ):
            result = get_log_path("SessionStart", "session123")

            # Check filename matches timestamp pattern
            filename = result.name
            assert re.match(r"^\d{8}_\d{6}\.json$", filename)

    def test_file_extension_is_json(self):
        """Test file has .json extension."""
        with patch(
            "claude_apps.hooks.logger.paths.resolve_log_path",
            return_value=Path("/logs"),
        ):
            result = get_log_path("SessionStart", "session123")

            assert result.suffix == ".json"

    def test_path_structure(self):
        """Test path follows expected structure."""
        with patch(
            "claude_apps.hooks.logger.paths.resolve_log_path",
            return_value=Path("/logs"),
        ):
            result = get_log_path("SessionStart", "abc123")

            # Structure: base / session_id / hook_event_name / timestamp.json
            parts = result.parts
            assert "abc123" in parts
            assert "SessionStart" in parts
