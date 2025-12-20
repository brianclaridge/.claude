"""Tests for playwright_healer hook logger."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from claude_apps.hooks.playwright_healer.logger import (
    log_error,
    log_healing_event,
    setup_logger,
)


class TestSetupLogger:
    """Tests for setup_logger function."""

    def test_returns_logger_when_enabled(self):
        """Test returns logger when logging enabled."""
        with patch(
            "claude_apps.hooks.playwright_healer.logger.get_config",
            return_value={"log_enabled": True},
        ):
            # Reset global logger
            import claude_apps.hooks.playwright_healer.logger as logger_mod
            logger_mod._logger = None

            result = setup_logger()

            # Should return a logger
            assert result is not None

    def test_returns_none_when_disabled(self):
        """Test returns None when logging disabled."""
        with patch(
            "claude_apps.hooks.playwright_healer.logger.get_config",
            return_value={"log_enabled": False},
        ):
            # Reset global logger
            import claude_apps.hooks.playwright_healer.logger as logger_mod
            logger_mod._logger = None

            result = setup_logger()

            assert result is None

    def test_caches_logger(self):
        """Test caches logger after first call."""
        with patch(
            "claude_apps.hooks.playwright_healer.logger.get_config",
            return_value={"log_enabled": True},
        ):
            # Reset global logger
            import claude_apps.hooks.playwright_healer.logger as logger_mod
            logger_mod._logger = None

            first = setup_logger()
            second = setup_logger()

            assert first is second


class TestLogHealingEvent:
    """Tests for log_healing_event function."""

    def test_writes_to_log_file(self, tmp_path):
        """Test writes event to log file."""
        log_file = tmp_path / "event.json"

        with patch(
            "claude_apps.hooks.playwright_healer.logger.get_log_path",
            return_value=log_file,
        ):
            with patch(
                "claude_apps.hooks.playwright_healer.logger.setup_logger",
                return_value=None,
            ):
                log_healing_event(
                    session_id="session123",
                    event_type="error_detected",
                    tool_name="mcp__playwright__browser_click",
                    error_pattern="Browser is already in use",
                )

                assert log_file.exists()
                content = json.loads(log_file.read_text())
                assert len(content) == 1
                assert content[0]["session_id"] == "session123"
                assert content[0]["event_type"] == "error_detected"

    def test_includes_timestamp(self, tmp_path):
        """Test includes timestamp in log entry."""
        log_file = tmp_path / "event.json"

        with patch(
            "claude_apps.hooks.playwright_healer.logger.get_log_path",
            return_value=log_file,
        ):
            with patch(
                "claude_apps.hooks.playwright_healer.logger.setup_logger",
                return_value=None,
            ):
                log_healing_event(
                    session_id="session123",
                    event_type="test",
                    tool_name="tool",
                )

                content = json.loads(log_file.read_text())
                assert "timestamp" in content[0]

    def test_includes_extra_kwargs(self, tmp_path):
        """Test includes extra keyword arguments."""
        log_file = tmp_path / "event.json"

        with patch(
            "claude_apps.hooks.playwright_healer.logger.get_log_path",
            return_value=log_file,
        ):
            with patch(
                "claude_apps.hooks.playwright_healer.logger.setup_logger",
                return_value=None,
            ):
                log_healing_event(
                    session_id="session123",
                    event_type="test",
                    tool_name="tool",
                    custom_field="custom_value",
                )

                content = json.loads(log_file.read_text())
                assert content[0]["custom_field"] == "custom_value"

    def test_handles_write_error(self, capsys):
        """Test handles write errors gracefully."""
        with patch(
            "claude_apps.hooks.playwright_healer.logger.get_log_path",
            side_effect=Exception("Path error"),
        ):
            with patch(
                "claude_apps.hooks.playwright_healer.logger.setup_logger",
                return_value=None,
            ):
                # Should not raise
                log_healing_event(
                    session_id="session123",
                    event_type="test",
                    tool_name="tool",
                )

        captured = capsys.readouterr()
        assert "Failed to log healing event" in captured.err


class TestLogError:
    """Tests for log_error function."""

    def test_writes_to_error_log(self, tmp_path):
        """Test writes error to error log file."""
        log_file = tmp_path / "error.json"

        with patch(
            "claude_apps.hooks.playwright_healer.logger.get_error_log_path",
            return_value=log_file,
        ):
            with patch(
                "claude_apps.hooks.playwright_healer.logger.setup_logger",
                return_value=None,
            ):
                log_error("Test error message", session_id="session123")

                assert log_file.exists()
                content = json.loads(log_file.read_text())
                assert content[0]["error_message"] == "Test error message"

    def test_uses_default_session_id(self, tmp_path):
        """Test uses 'unknown' as default session_id."""
        log_file = tmp_path / "error.json"

        with patch(
            "claude_apps.hooks.playwright_healer.logger.get_error_log_path",
            return_value=log_file,
        ):
            with patch(
                "claude_apps.hooks.playwright_healer.logger.setup_logger",
                return_value=None,
            ):
                log_error("Test error")

                content = json.loads(log_file.read_text())
                assert content[0]["session_id"] == "unknown"

    def test_includes_extra_context(self, tmp_path):
        """Test includes extra context."""
        log_file = tmp_path / "error.json"

        with patch(
            "claude_apps.hooks.playwright_healer.logger.get_error_log_path",
            return_value=log_file,
        ):
            with patch(
                "claude_apps.hooks.playwright_healer.logger.setup_logger",
                return_value=None,
            ):
                log_error("Test error", extra_key="extra_value")

                content = json.loads(log_file.read_text())
                assert content[0]["extra_key"] == "extra_value"

    def test_handles_write_error(self, capsys):
        """Test handles write errors gracefully."""
        with patch(
            "claude_apps.hooks.playwright_healer.logger.get_error_log_path",
            side_effect=Exception("Path error"),
        ):
            with patch(
                "claude_apps.hooks.playwright_healer.logger.setup_logger",
                return_value=None,
            ):
                # Should not raise
                log_error("Test error")

        captured = capsys.readouterr()
        assert "Failed to log error" in captured.err
