"""Tests for cloud auth prompt hook main module."""

import json
import sys
from io import StringIO
from unittest.mock import patch

import pytest

from claude_apps.hooks.cloud_auth_prompt.__main__ import (
    main,
    process_stdin,
    read_hook_event,
)


class TestReadHookEvent:
    """Tests for read_hook_event function."""

    def test_reads_valid_json(self):
        """Test reads valid JSON from stdin."""
        with patch("sys.stdin", StringIO('{"event": "test"}\n')):
            result = read_hook_event()

            assert result == {"event": "test"}

    def test_returns_none_for_empty(self):
        """Test returns None for empty input."""
        with patch("sys.stdin", StringIO("")):
            result = read_hook_event()

            assert result is None

    def test_returns_none_for_blank_line(self):
        """Test returns None for blank line."""
        with patch("sys.stdin", StringIO("\n")):
            result = read_hook_event()

            assert result is None

    def test_returns_none_for_invalid_json(self):
        """Test returns None for invalid JSON."""
        with patch("sys.stdin", StringIO("not json\n")):
            result = read_hook_event()

            assert result is None

    def test_strips_whitespace(self):
        """Test strips whitespace from line."""
        with patch("sys.stdin", StringIO('  {"key": "value"}  \n')):
            result = read_hook_event()

            assert result == {"key": "value"}


class TestProcessStdin:
    """Tests for process_stdin generator."""

    def test_yields_events(self):
        """Test yields parsed events."""
        input_data = '{"event": 1}\n{"event": 2}\n'

        with patch("sys.stdin", StringIO(input_data)):
            events = list(process_stdin())

            assert len(events) == 2
            assert events[0]["event"] == 1
            assert events[1]["event"] == 2

    def test_stops_on_empty(self):
        """Test stops on empty line."""
        input_data = '{"event": 1}\n\n{"event": 2}\n'

        with patch("sys.stdin", StringIO(input_data)):
            events = list(process_stdin())

            assert len(events) == 1

    def test_yields_nothing_for_empty_input(self):
        """Test yields nothing for empty input."""
        with patch("sys.stdin", StringIO("")):
            events = list(process_stdin())

            assert events == []


class TestMain:
    """Tests for main function."""

    def test_returns_zero_on_success(self):
        """Test returns 0 on success."""
        with patch("sys.stdin", StringIO("")):
            result = main()

            assert result == 0

    def test_processes_events(self, capsys):
        """Test processes stdin events."""
        input_data = json.dumps({
            "hook_event_name": "SessionStart",
            "session_id": "test123",
        }) + "\n"

        with patch("sys.stdin", StringIO(input_data)):
            with patch(
                "claude_apps.hooks.cloud_auth_prompt.__main__.get_enabled_providers",
                return_value=[],
            ):
                result = main()

        assert result == 0
        captured = capsys.readouterr()
        # Should output hook response
        response = json.loads(captured.out)
        assert "hookSpecificOutput" in response

    def test_outputs_provider_context(self, capsys):
        """Test outputs context for enabled providers."""
        input_data = json.dumps({
            "hook_event_name": "SessionStart",
            "session_id": "test123",
        }) + "\n"

        providers = [{"name": "aws", "display_name": "AWS", "description": "Login"}]

        with patch("sys.stdin", StringIO(input_data)):
            with patch(
                "claude_apps.hooks.cloud_auth_prompt.__main__.get_enabled_providers",
                return_value=providers,
            ):
                main()

        captured = capsys.readouterr()
        response = json.loads(captured.out)
        context = response["hookSpecificOutput"]["additionalContext"]
        assert "/auth-aws" in context

    def test_handles_keyboard_interrupt(self):
        """Test handles KeyboardInterrupt gracefully."""
        with patch(
            "claude_apps.hooks.cloud_auth_prompt.__main__.process_stdin",
            side_effect=KeyboardInterrupt,
        ):
            result = main()

            assert result == 0

    def test_handles_unexpected_error(self, capsys):
        """Test handles unexpected errors."""
        with patch(
            "claude_apps.hooks.cloud_auth_prompt.__main__.process_stdin",
            side_effect=RuntimeError("Test error"),
        ):
            result = main()

        assert result == 0
        captured = capsys.readouterr()
        # Should still output valid hook response
        response = json.loads(captured.out)
        assert "hookSpecificOutput" in response

    def test_uses_default_event_name(self, capsys):
        """Test uses SessionStart as default event name."""
        input_data = json.dumps({"session_id": "test"}) + "\n"

        with patch("sys.stdin", StringIO(input_data)):
            with patch(
                "claude_apps.hooks.cloud_auth_prompt.__main__.get_enabled_providers",
                return_value=[],
            ):
                main()

        captured = capsys.readouterr()
        response = json.loads(captured.out)
        assert response["hookSpecificOutput"]["hookEventName"] == "SessionStart"

    def test_processes_multiple_events(self, capsys):
        """Test processes multiple events."""
        input_data = (
            json.dumps({"session_id": "a", "hook_event_name": "E1"}) + "\n" +
            json.dumps({"session_id": "b", "hook_event_name": "E2"}) + "\n"
        )

        with patch("sys.stdin", StringIO(input_data)):
            with patch(
                "claude_apps.hooks.cloud_auth_prompt.__main__.get_enabled_providers",
                return_value=[],
            ):
                main()

        captured = capsys.readouterr()
        lines = [l for l in captured.out.strip().split("\n") if l]
        assert len(lines) == 2
