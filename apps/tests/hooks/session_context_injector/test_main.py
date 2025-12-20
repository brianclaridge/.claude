"""Tests for session_context_injector hook entry point."""

import json
from io import StringIO
from unittest.mock import patch

import pytest

from claude_apps.hooks.session_context_injector.__main__ import main


class TestMain:
    """Tests for main function."""

    def test_returns_zero_on_empty_input(self):
        """Test returns 0 for empty stdin."""
        with patch("sys.stdin", StringIO("")):
            result = main()

            assert result == 0

    def test_ignores_non_sessionstart_events(self, capsys):
        """Test ignores non-SessionStart events."""
        hook_data = {"hook_event_name": "OtherEvent"}

        with patch("sys.stdin", StringIO(json.dumps(hook_data))):
            result = main()

            assert result == 0
            captured = capsys.readouterr()
            output = json.loads(captured.out.strip())
            assert output["hookSpecificOutput"]["hookEventName"] == "OtherEvent"
            assert output["hookSpecificOutput"]["additionalContext"] == ""

    def test_processes_sessionstart_event(self, capsys):
        """Test processes SessionStart event."""
        hook_data = {
            "hook_event_name": "SessionStart",
            "source": "startup",
            "session_id": "test-123",
        }

        mock_config = {
            "auto_invoke_agent": True,
            "session_behavior": {"startup": "full"},
        }

        with patch("sys.stdin", StringIO(json.dumps(hook_data))):
            with patch(
                "claude_apps.hooks.session_context_injector.__main__.load_session_config"
            ) as mock_load:
                mock_load.return_value = mock_config

                result = main()

                assert result == 0
                captured = capsys.readouterr()
                output = json.loads(captured.out.strip())
                assert output["hookSpecificOutput"]["hookEventName"] == "SessionStart"
                assert "Session Context Injection" in output["hookSpecificOutput"]["additionalContext"]

    def test_skips_when_auto_invoke_disabled(self, capsys):
        """Test skips prompt injection when auto_invoke_agent=False."""
        hook_data = {
            "hook_event_name": "SessionStart",
            "source": "startup",
        }

        mock_config = {
            "auto_invoke_agent": False,
        }

        with patch("sys.stdin", StringIO(json.dumps(hook_data))):
            with patch(
                "claude_apps.hooks.session_context_injector.__main__.load_session_config"
            ) as mock_load:
                mock_load.return_value = mock_config

                result = main()

                assert result == 0
                captured = capsys.readouterr()
                output = json.loads(captured.out.strip())
                assert output["hookSpecificOutput"]["additionalContext"] == ""

    def test_handles_resume_source(self, capsys):
        """Test handles resume source type."""
        hook_data = {
            "hook_event_name": "SessionStart",
            "source": "resume",
        }

        mock_config = {
            "auto_invoke_agent": True,
            "session_behavior": {"resume": "abbreviated"},
        }

        with patch("sys.stdin", StringIO(json.dumps(hook_data))):
            with patch(
                "claude_apps.hooks.session_context_injector.__main__.load_session_config"
            ) as mock_load:
                mock_load.return_value = mock_config

                result = main()

                captured = capsys.readouterr()
                output = json.loads(captured.out.strip())
                assert "resume" in output["hookSpecificOutput"]["additionalContext"].lower()

    def test_handles_compact_source(self, capsys):
        """Test handles compact source type."""
        hook_data = {
            "hook_event_name": "SessionStart",
            "source": "compact",
        }

        mock_config = {
            "auto_invoke_agent": True,
            "session_behavior": {"compact": "abbreviated"},
        }

        with patch("sys.stdin", StringIO(json.dumps(hook_data))):
            with patch(
                "claude_apps.hooks.session_context_injector.__main__.load_session_config"
            ) as mock_load:
                mock_load.return_value = mock_config

                result = main()

                captured = capsys.readouterr()
                output = json.loads(captured.out.strip())
                assert "compact" in output["hookSpecificOutput"]["additionalContext"].lower()

    def test_handles_clear_source(self, capsys):
        """Test handles clear source type."""
        hook_data = {
            "hook_event_name": "SessionStart",
            "source": "clear",
        }

        mock_config = {
            "auto_invoke_agent": True,
            "session_behavior": {"clear": "full"},
        }

        with patch("sys.stdin", StringIO(json.dumps(hook_data))):
            with patch(
                "claude_apps.hooks.session_context_injector.__main__.load_session_config"
            ) as mock_load:
                mock_load.return_value = mock_config

                result = main()

                captured = capsys.readouterr()
                output = json.loads(captured.out.strip())
                assert "clear" in output["hookSpecificOutput"]["additionalContext"].lower()

    def test_returns_zero_on_invalid_json(self):
        """Test returns 0 on invalid JSON (doesn't crash hook)."""
        with patch("sys.stdin", StringIO("invalid json {")):
            with patch("builtins.print"):  # Mock print to avoid stdout issues
                result = main()

                # Hook should return 0 even on error to not block Claude
                assert result == 0

    def test_returns_zero_on_exception(self, capsys):
        """Test returns 0 on exception (hook shouldn't block Claude)."""
        hook_data = {
            "hook_event_name": "SessionStart",
            "source": "startup",
        }

        with patch("sys.stdin", StringIO(json.dumps(hook_data))):
            with patch(
                "claude_apps.hooks.session_context_injector.__main__.load_session_config"
            ) as mock_load:
                mock_load.side_effect = Exception("Config error")

                result = main()

                assert result == 0

    def test_defaults_source_to_startup(self, capsys):
        """Test defaults source to startup when not provided."""
        hook_data = {
            "hook_event_name": "SessionStart",
            # No source provided
        }

        mock_config = {
            "auto_invoke_agent": True,
            "session_behavior": {"startup": "full"},
        }

        with patch("sys.stdin", StringIO(json.dumps(hook_data))):
            with patch(
                "claude_apps.hooks.session_context_injector.__main__.load_session_config"
            ) as mock_load:
                mock_load.return_value = mock_config

                result = main()

                captured = capsys.readouterr()
                output = json.loads(captured.out.strip())
                # Should process with default startup source
                assert "additionalContext" in output["hookSpecificOutput"]
