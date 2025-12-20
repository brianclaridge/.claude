"""Tests for logger hook main module."""

import json
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from claude_apps.hooks.logger.__main__ import (
    log_hook_event,
    main,
    output_hook_response,
)


class TestLogHookEvent:
    """Tests for log_hook_event function."""

    def test_skips_when_no_session_id(self):
        """Test skips when session_id is missing."""
        hook_data = {"hook_event_name": "SessionStart"}

        with patch(
            "claude_apps.hooks.logger.__main__.get_log_path"
        ) as mock_path:
            log_hook_event(hook_data)

            mock_path.assert_not_called()

    def test_skips_when_no_hook_event_name(self):
        """Test skips when hook_event_name is missing."""
        hook_data = {"session_id": "abc123"}

        with patch(
            "claude_apps.hooks.logger.__main__.get_log_path"
        ) as mock_path:
            log_hook_event(hook_data)

            mock_path.assert_not_called()

    def test_writes_log_entry(self, tmp_path):
        """Test writes log entry for valid hook data."""
        log_file = tmp_path / "log.json"
        hook_data = {
            "session_id": "abc123",
            "hook_event_name": "SessionStart",
            "data": "test",
        }

        with patch(
            "claude_apps.hooks.logger.__main__.get_log_path",
            return_value=log_file,
        ):
            with patch(
                "claude_apps.hooks.logger.__main__.write_log_entry"
            ) as mock_write:
                log_hook_event(hook_data)

                mock_write.assert_called_once_with(log_file, hook_data)

    def test_handles_write_error(self, capsys):
        """Test handles write error gracefully."""
        hook_data = {
            "session_id": "abc123",
            "hook_event_name": "SessionStart",
        }

        with patch(
            "claude_apps.hooks.logger.__main__.get_log_path",
            side_effect=Exception("Write failed"),
        ):
            # Should not raise
            log_hook_event(hook_data)

        # Check error logged to stderr
        captured = capsys.readouterr()
        assert "Failed to log event" in captured.err


class TestOutputHookResponse:
    """Tests for output_hook_response function."""

    def test_outputs_valid_json(self, capsys):
        """Test outputs valid JSON."""
        output_hook_response()

        captured = capsys.readouterr()
        response = json.loads(captured.out)

        assert "continue" in response
        assert "suppressOutput" in response

    def test_continue_is_true(self, capsys):
        """Test continue flag is True."""
        output_hook_response()

        captured = capsys.readouterr()
        response = json.loads(captured.out)

        assert response["continue"] is True

    def test_suppress_output_is_false(self, capsys):
        """Test suppressOutput is False."""
        output_hook_response()

        captured = capsys.readouterr()
        response = json.loads(captured.out)

        assert response["suppressOutput"] is False


class TestMain:
    """Tests for main function."""

    def test_returns_zero_on_success(self):
        """Test returns 0 on success."""
        with patch.object(sys, "argv", ["logger"]):
            with patch("sys.stdin", StringIO("")):
                result = main()

                assert result == 0

    def test_shows_help_on_help_flag(self):
        """Test shows help and exits on help flag."""
        with patch.object(sys, "argv", ["logger", "--help"]):
            with patch(
                "claude_apps.hooks.logger.__main__.show_help"
            ) as mock_help:
                main()

                mock_help.assert_called_once()

    def test_processes_stdin_events(self, capsys):
        """Test processes stdin events."""
        input_data = json.dumps({
            "session_id": "abc",
            "hook_event_name": "SessionStart",
        }) + "\n"

        with patch("sys.stdin", StringIO(input_data)):
            with patch.object(sys, "argv", ["logger"]):
                with patch(
                    "claude_apps.hooks.logger.__main__.get_log_path",
                    return_value=Path("/tmp/log.json"),
                ):
                    with patch(
                        "claude_apps.hooks.logger.__main__.write_log_entry"
                    ):
                        result = main()

        assert result == 0
        # Check response was output
        captured = capsys.readouterr()
        assert "continue" in captured.out

    def test_handles_keyboard_interrupt(self):
        """Test handles KeyboardInterrupt."""
        with patch.object(sys, "argv", ["logger"]):
            with patch(
                "claude_apps.hooks.logger.__main__.parse_args",
                side_effect=KeyboardInterrupt,
            ):
                result = main()

                assert result == 0

    def test_handles_unexpected_error(self, capsys):
        """Test handles unexpected errors gracefully."""
        with patch.object(sys, "argv", ["logger"]):
            with patch(
                "claude_apps.hooks.logger.__main__.parse_args",
                side_effect=RuntimeError("Unexpected"),
            ):
                result = main()

                assert result == 0

        captured = capsys.readouterr()
        assert "Unexpected error" in captured.err

    def test_outputs_response_for_each_event(self, capsys):
        """Test outputs hook response for each event."""
        input_data = (
            json.dumps({"session_id": "a", "hook_event_name": "E1"}) + "\n" +
            json.dumps({"session_id": "b", "hook_event_name": "E2"}) + "\n"
        )

        with patch("sys.stdin", StringIO(input_data)):
            with patch.object(sys, "argv", ["logger"]):
                with patch(
                    "claude_apps.hooks.logger.__main__.get_log_path",
                    return_value=Path("/tmp/log.json"),
                ):
                    with patch(
                        "claude_apps.hooks.logger.__main__.write_log_entry"
                    ):
                        main()

        captured = capsys.readouterr()
        # Should have two JSON responses
        lines = [l for l in captured.out.strip().split("\n") if l]
        assert len(lines) == 2
