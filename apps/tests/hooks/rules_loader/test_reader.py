"""Tests for rules loader stdin reader."""

from io import StringIO
from unittest.mock import patch

import pytest

from claude_apps.hooks.rules_loader.reader import process_stdin, read_hook_event


class TestReadHookEvent:
    """Tests for read_hook_event function."""

    def test_reads_json_line(self):
        """Test reads and parses JSON from stdin."""
        with patch("sys.stdin", StringIO('{"event": "test"}\n')):
            result = read_hook_event()

            assert result == {"event": "test"}

    def test_returns_none_for_empty_line(self):
        """Test returns None for empty line."""
        with patch("sys.stdin", StringIO("\n")):
            result = read_hook_event()

            assert result is None

    def test_returns_none_for_eof(self):
        """Test returns None at EOF."""
        with patch("sys.stdin", StringIO("")):
            result = read_hook_event()

            assert result is None

    def test_returns_none_for_invalid_json(self):
        """Test returns None for invalid JSON."""
        with patch("sys.stdin", StringIO("not valid json\n")):
            result = read_hook_event()

            assert result is None

    def test_strips_whitespace(self):
        """Test strips whitespace from line."""
        with patch("sys.stdin", StringIO('  {"key": "value"}  \n')):
            result = read_hook_event()

            assert result == {"key": "value"}


class TestProcessStdin:
    """Tests for process_stdin generator."""

    def test_yields_multiple_events(self):
        """Test yields multiple JSON events."""
        input_data = '{"event": 1}\n{"event": 2}\n{"event": 3}\n'

        with patch("sys.stdin", StringIO(input_data)):
            events = list(process_stdin())

            assert len(events) == 3
            assert events[0]["event"] == 1
            assert events[1]["event"] == 2
            assert events[2]["event"] == 3

    def test_stops_on_empty_line(self):
        """Test stops on empty line."""
        input_data = '{"event": 1}\n\n{"event": 2}\n'

        with patch("sys.stdin", StringIO(input_data)):
            events = list(process_stdin())

            # Should stop at empty line
            assert len(events) == 1

    def test_stops_on_eof(self):
        """Test stops at EOF."""
        input_data = '{"event": 1}\n{"event": 2}\n'

        with patch("sys.stdin", StringIO(input_data)):
            events = list(process_stdin())

            assert len(events) == 2

    def test_yields_nothing_for_empty_input(self):
        """Test yields nothing for empty input."""
        with patch("sys.stdin", StringIO("")):
            events = list(process_stdin())

            assert events == []
