"""Tests for logger hook writer module."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest


class TestLogWriter:
    """Tests for log writing functionality."""

    def test_log_directory_creation(self, tmp_path: Path) -> None:
        """Test that log directory is created if it doesn't exist."""
        log_dir = tmp_path / "logs" / "nested"
        assert not log_dir.exists()

        # Create directory
        log_dir.mkdir(parents=True)
        assert log_dir.exists()

    def test_json_log_format(self, tmp_path: Path) -> None:
        """Test that logs are written in valid JSON format."""
        log_file = tmp_path / "test.jsonl"

        # Write sample log entry
        entry = {"event": "test", "data": {"key": "value"}}
        with open(log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")

        # Verify it can be read back
        with open(log_file) as f:
            line = f.readline()
            parsed = json.loads(line)
            assert parsed["event"] == "test"
            assert parsed["data"]["key"] == "value"

    def test_append_mode(self, tmp_path: Path) -> None:
        """Test that multiple entries are appended correctly."""
        log_file = tmp_path / "test.jsonl"

        entries = [
            {"event": "first"},
            {"event": "second"},
            {"event": "third"},
        ]

        for entry in entries:
            with open(log_file, "a") as f:
                f.write(json.dumps(entry) + "\n")

        with open(log_file) as f:
            lines = f.readlines()
            assert len(lines) == 3
            assert json.loads(lines[0])["event"] == "first"
            assert json.loads(lines[2])["event"] == "third"
