"""Tests for playwright_healer hook path utilities."""

import re
from pathlib import Path
from unittest.mock import patch

import pytest

from claude_apps.hooks.playwright_healer.paths import (
    get_config,
    get_error_log_path,
    get_log_base,
    get_log_path,
    get_state_path,
)


class TestGetConfig:
    """Tests for get_config function."""

    def test_returns_validated_config(self):
        """Test returns validated config dict."""
        with patch(
            "claude_apps.hooks.playwright_healer.paths.get_hook_config",
            return_value={"log_enabled": True, "max_recovery_attempts": 5},
        ):
            config = get_config()

            assert isinstance(config, dict)
            assert config["log_enabled"] is True
            assert config["max_recovery_attempts"] == 5

    def test_applies_defaults(self):
        """Test applies default values for missing keys."""
        with patch(
            "claude_apps.hooks.playwright_healer.paths.get_hook_config",
            return_value={},
        ):
            config = get_config()

            assert config["log_enabled"] is True
            assert config["max_recovery_attempts"] == 3

    def test_includes_error_patterns(self):
        """Test includes default error patterns."""
        with patch(
            "claude_apps.hooks.playwright_healer.paths.get_hook_config",
            return_value={},
        ):
            config = get_config()

            assert "error_patterns" in config
            assert len(config["error_patterns"]) > 0


class TestGetLogBase:
    """Tests for get_log_base function."""

    def test_returns_path(self):
        """Test returns Path object."""
        with patch(
            "claude_apps.hooks.playwright_healer.paths.resolve_log_path",
            return_value=Path("/logs/playwright_healer"),
        ):
            result = get_log_base()

            assert isinstance(result, Path)


class TestGetLogPath:
    """Tests for get_log_path function."""

    def test_includes_session_id(self):
        """Test includes session ID in path."""
        with patch(
            "claude_apps.hooks.playwright_healer.paths.get_log_base",
            return_value=Path("/logs"),
        ):
            result = get_log_path("session123", "error_detected")

            assert "session123" in str(result)

    def test_includes_event_type(self):
        """Test includes event type in path."""
        with patch(
            "claude_apps.hooks.playwright_healer.paths.get_log_base",
            return_value=Path("/logs"),
        ):
            result = get_log_path("session123", "recovery_success")

            assert "recovery_success" in str(result)

    def test_includes_timestamp(self):
        """Test includes timestamp in filename."""
        with patch(
            "claude_apps.hooks.playwright_healer.paths.get_log_base",
            return_value=Path("/logs"),
        ):
            result = get_log_path("session123", "event")

            # Check filename matches timestamp pattern
            assert re.match(r"^\d{8}_\d{6}\.json$", result.name)

    def test_has_json_extension(self):
        """Test has .json extension."""
        with patch(
            "claude_apps.hooks.playwright_healer.paths.get_log_base",
            return_value=Path("/logs"),
        ):
            result = get_log_path("session123", "event")

            assert result.suffix == ".json"


class TestGetErrorLogPath:
    """Tests for get_error_log_path function."""

    def test_includes_session_id(self):
        """Test includes session ID in path."""
        with patch(
            "claude_apps.hooks.playwright_healer.paths.get_log_base",
            return_value=Path("/logs"),
        ):
            result = get_error_log_path("session123")

            assert "session123" in str(result)

    def test_includes_errors_directory(self):
        """Test includes 'errors' in path."""
        with patch(
            "claude_apps.hooks.playwright_healer.paths.get_log_base",
            return_value=Path("/logs"),
        ):
            result = get_error_log_path("session123")

            assert "errors" in str(result)


class TestGetStatePath:
    """Tests for get_state_path function."""

    def test_includes_session_id(self):
        """Test includes session ID in path."""
        with patch(
            "claude_apps.hooks.playwright_healer.paths.get_log_base",
            return_value=Path("/logs"),
        ):
            result = get_state_path("session123")

            assert "session123" in str(result)

    def test_includes_state_directory(self):
        """Test includes 'state' in path."""
        with patch(
            "claude_apps.hooks.playwright_healer.paths.get_log_base",
            return_value=Path("/logs"),
        ):
            result = get_state_path("session123")

            assert "state" in str(result)

    def test_filename_is_recovery_state(self):
        """Test filename is recovery_state.json."""
        with patch(
            "claude_apps.hooks.playwright_healer.paths.get_log_base",
            return_value=Path("/logs"),
        ):
            result = get_state_path("session123")

            assert result.name == "recovery_state.json"
