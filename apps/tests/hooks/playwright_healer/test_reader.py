"""Tests for playwright_healer hook stdin reader."""

from io import StringIO
from unittest.mock import patch

import pytest

from claude_apps.hooks.playwright_healer.reader import process_stdin, read_hook_event


class TestReadHookEvent:
    """Tests for read_hook_event function."""

    def test_reads_valid_json(self):
        """Test reads valid JSON from stdin."""
        with patch("sys.stdin", StringIO('{"tool_name": "test"}\n')):
            result = read_hook_event()

            assert result == {"tool_name": "test"}

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
