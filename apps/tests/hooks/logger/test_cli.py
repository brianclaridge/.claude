"""Tests for logger hook CLI utilities."""

import sys
from unittest.mock import patch

import pytest

from claude_apps.hooks.logger.cli import parse_args, show_help


class TestParseArgs:
    """Tests for parse_args function."""

    def test_parses_no_args(self):
        """Test parses empty arguments."""
        with patch.object(sys, "argv", ["logger"]):
            args = parse_args()

            assert args.help is False

    def test_parses_help_flag_short(self):
        """Test parses -h flag."""
        with patch.object(sys, "argv", ["logger", "-h"]):
            args = parse_args()

            assert args.help is True

    def test_parses_help_flag_long(self):
        """Test parses --help flag."""
        with patch.object(sys, "argv", ["logger", "--help"]):
            args = parse_args()

            assert args.help is True


class TestShowHelp:
    """Tests for show_help function."""

    def test_exits_with_zero(self, capsys):
        """Test exits with code 0."""
        with pytest.raises(SystemExit) as exc_info:
            show_help()

        assert exc_info.value.code == 0

    def test_prints_help_text(self, capsys):
        """Test prints help text."""
        with pytest.raises(SystemExit):
            show_help()

        captured = capsys.readouterr()
        assert "uv run" in captured.out or "logger" in captured.out.lower()
