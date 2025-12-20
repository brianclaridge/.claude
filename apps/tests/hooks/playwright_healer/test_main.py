"""Tests for playwright_healer hook main module."""

import json
import sys
from io import StringIO
from unittest.mock import MagicMock, patch

import pytest

from claude_apps.hooks.playwright_healer.__main__ import (
    main,
    process_hook_event,
)


class TestProcessHookEvent:
    """Tests for process_hook_event function."""

    def test_returns_continue_for_non_playwright_tool(self):
        """Test returns continue for non-Playwright tools."""
        hook_data = {
            "tool_name": "bash",
            "tool_response": "output",
            "session_id": "session123",
        }

        result = process_hook_event(hook_data)

        assert result["continue"] is True
        assert result["suppressOutput"] is False
        assert "hookSpecificOutput" not in result

    def test_returns_continue_when_no_error(self):
        """Test returns continue when no error detected."""
        hook_data = {
            "tool_name": "mcp__playwright__browser_click",
            "tool_response": "clicked successfully",
            "session_id": "session123",
        }

        with patch(
            "claude_apps.hooks.playwright_healer.__main__.detect_browser_error",
            return_value={"detected": False},
        ):
            result = process_hook_event(hook_data)

            assert result["continue"] is True
            assert "hookSpecificOutput" not in result

    def test_includes_context_on_successful_recovery(self):
        """Test includes context on successful recovery."""
        hook_data = {
            "tool_name": "mcp__playwright__browser_click",
            "tool_response": "Browser is already in use",
            "session_id": "session123",
        }

        with patch(
            "claude_apps.hooks.playwright_healer.__main__.detect_browser_error",
            return_value={
                "detected": True,
                "pattern": "Browser is already in use",
                "message": "Full error message",
                "error_type": "browser_lock",
            },
        ):
            with patch(
                "claude_apps.hooks.playwright_healer.__main__.attempt_recovery",
                return_value={
                    "success": True,
                    "action": "browser_lock_recovery",
                    "message": "Recovered",
                },
            ):
                with patch(
                    "claude_apps.hooks.playwright_healer.__main__.log_healing_event"
                ):
                    result = process_hook_event(hook_data)

                    assert "hookSpecificOutput" in result
                    assert "PLAYWRIGHT HEALER" in result["hookSpecificOutput"]["additionalContext"]

    def test_no_context_on_failed_recovery(self):
        """Test no additional context on failed recovery."""
        hook_data = {
            "tool_name": "mcp__playwright__browser_click",
            "tool_response": "Browser is already in use",
            "session_id": "session123",
        }

        with patch(
            "claude_apps.hooks.playwright_healer.__main__.detect_browser_error",
            return_value={
                "detected": True,
                "pattern": "Browser is already in use",
                "message": "Full error message",
                "error_type": "browser_lock",
            },
        ):
            with patch(
                "claude_apps.hooks.playwright_healer.__main__.attempt_recovery",
                return_value={
                    "success": False,
                    "action": "skipped",
                    "error": "Max attempts reached",
                },
            ):
                with patch(
                    "claude_apps.hooks.playwright_healer.__main__.log_healing_event"
                ):
                    result = process_hook_event(hook_data)

                    assert "hookSpecificOutput" not in result

    def test_logs_error_detection(self):
        """Test logs error detection event."""
        hook_data = {
            "tool_name": "mcp__playwright__browser_click",
            "tool_response": "Browser is already in use",
            "session_id": "session123",
        }

        with patch(
            "claude_apps.hooks.playwright_healer.__main__.detect_browser_error",
            return_value={
                "detected": True,
                "pattern": "Browser is already in use",
                "message": "Full error message",
                "error_type": "browser_lock",
            },
        ):
            with patch(
                "claude_apps.hooks.playwright_healer.__main__.attempt_recovery",
                return_value={"success": True, "action": "test", "message": "ok"},
            ):
                with patch(
                    "claude_apps.hooks.playwright_healer.__main__.log_healing_event"
                ) as mock_log:
                    process_hook_event(hook_data)

                    # Should be called at least for error_detected
                    assert mock_log.called


class TestMain:
    """Tests for main function."""

    def test_returns_zero_on_success(self):
        """Test returns 0 on success."""
        with patch.object(sys, "argv", ["playwright_healer"]):
            with patch("sys.stdin", StringIO("")):
                with patch(
                    "claude_apps.hooks.playwright_healer.__main__.setup_logger"
                ):
                    result = main()

                    assert result == 0

    def test_shows_help_on_help_flag(self):
        """Test shows help and exits on help flag."""
        with patch.object(sys, "argv", ["playwright_healer", "--help"]):
            with patch(
                "claude_apps.hooks.playwright_healer.__main__.show_help"
            ) as mock_help:
                main()

                mock_help.assert_called_once()

    def test_processes_stdin_events(self, capsys):
        """Test processes stdin events."""
        input_data = json.dumps({
            "tool_name": "mcp__playwright__browser_click",
            "tool_response": "success",
            "session_id": "abc123",
        }) + "\n"

        with patch.object(sys, "argv", ["playwright_healer"]):
            with patch("sys.stdin", StringIO(input_data)):
                with patch(
                    "claude_apps.hooks.playwright_healer.__main__.setup_logger"
                ):
                    with patch(
                        "claude_apps.hooks.playwright_healer.__main__.detect_browser_error",
                        return_value={"detected": False},
                    ):
                        result = main()

        assert result == 0
        captured = capsys.readouterr()
        # Should output hook response
        response = json.loads(captured.out)
        assert response["continue"] is True

    def test_handles_keyboard_interrupt(self):
        """Test handles KeyboardInterrupt."""
        with patch.object(sys, "argv", ["playwright_healer"]):
            with patch(
                "claude_apps.hooks.playwright_healer.__main__.parse_args",
                side_effect=KeyboardInterrupt,
            ):
                result = main()

                assert result == 0

    def test_handles_unexpected_error(self, capsys):
        """Test handles unexpected errors gracefully."""
        with patch.object(sys, "argv", ["playwright_healer"]):
            with patch(
                "claude_apps.hooks.playwright_healer.__main__.parse_args",
                side_effect=RuntimeError("Unexpected"),
            ):
                with patch(
                    "claude_apps.hooks.playwright_healer.__main__.log_error"
                ):
                    result = main()

                    assert result == 0

        captured = capsys.readouterr()
        # Should still output valid response
        response = json.loads(captured.out)
        assert response["continue"] is True
