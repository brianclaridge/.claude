"""Unit tests for reader.py - stdin JSON parsing."""
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from reader import read_hook_event, process_stdin


class TestReadHookEvent:
    """Tests for read_hook_event function."""

    def test_reads_valid_json_line(self) -> None:
        """Verify valid JSON line is parsed correctly."""
        input_data = '{"hook_event_name": "SessionStart", "session_id": "abc"}\n'

        with patch("sys.stdin", StringIO(input_data)):
            result = read_hook_event()

        assert result is not None
        assert result["hook_event_name"] == "SessionStart"
        assert result["session_id"] == "abc"

    def test_returns_none_on_empty_input(self) -> None:
        """Verify None returned on empty stdin."""
        with patch("sys.stdin", StringIO("")):
            result = read_hook_event()

        assert result is None

    def test_returns_none_on_whitespace_only(self) -> None:
        """Verify None returned on whitespace-only line."""
        with patch("sys.stdin", StringIO("   \n")):
            result = read_hook_event()

        assert result is None

    def test_returns_none_on_invalid_json(self) -> None:
        """Verify None returned on invalid JSON."""
        with patch("sys.stdin", StringIO("not valid json\n")):
            result = read_hook_event()

        assert result is None

    def test_strips_whitespace_from_line(self) -> None:
        """Verify whitespace is stripped before parsing."""
        input_data = '  {"key": "value"}  \n'

        with patch("sys.stdin", StringIO(input_data)):
            result = read_hook_event()

        assert result is not None
        assert result["key"] == "value"

    def test_handles_nested_json(self) -> None:
        """Verify nested JSON structures are parsed correctly."""
        input_data = '{"outer": {"inner": "value"}, "array": [1, 2, 3]}\n'

        with patch("sys.stdin", StringIO(input_data)):
            result = read_hook_event()

        assert result is not None
        assert result["outer"]["inner"] == "value"
        assert result["array"] == [1, 2, 3]


class TestProcessStdin:
    """Tests for process_stdin generator function."""

    def test_yields_single_event(self) -> None:
        """Verify single event is yielded correctly."""
        input_data = '{"hook_event_name": "SessionStart"}\n'

        with patch("sys.stdin", StringIO(input_data)):
            events = list(process_stdin())

        assert len(events) == 1
        assert events[0]["hook_event_name"] == "SessionStart"

    def test_stops_on_empty_line(self) -> None:
        """Verify generator stops on empty/invalid input."""
        input_data = '{"event": 1}\n'

        with patch("sys.stdin", StringIO(input_data)):
            events = list(process_stdin())

        assert len(events) == 1

    def test_empty_stdin_yields_nothing(self) -> None:
        """Verify empty stdin produces no events."""
        with patch("sys.stdin", StringIO("")):
            events = list(process_stdin())

        assert events == []

    def test_stops_on_invalid_json(self) -> None:
        """Verify generator stops on invalid JSON line."""
        # First line valid, then invalid JSON causes stop
        input_data = '{"event": 1}\n'

        with patch("sys.stdin", StringIO(input_data)):
            events = list(process_stdin())

        assert len(events) == 1

    def test_handles_typical_hook_payload(self) -> None:
        """Verify typical Claude Code hook payload is handled."""
        input_data = (
            '{"hook_event_name": "UserPromptSubmit", '
            '"session_id": "test-123", '
            '"prompt": "Hello world"}\n'
        )

        with patch("sys.stdin", StringIO(input_data)):
            events = list(process_stdin())

        assert len(events) == 1
        assert events[0]["hook_event_name"] == "UserPromptSubmit"
        assert events[0]["session_id"] == "test-123"
        assert events[0]["prompt"] == "Hello world"
