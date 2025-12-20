"""Tests for logger hook file writer."""

import json
from pathlib import Path

import pytest

from claude_apps.hooks.logger.writer import (
    ensure_directory,
    read_existing_entries,
    write_log_entry,
)


class TestEnsureDirectory:
    """Tests for ensure_directory function."""

    def test_creates_parent_directories(self, tmp_path):
        """Test creates parent directories."""
        file_path = tmp_path / "a" / "b" / "c" / "file.json"

        ensure_directory(file_path)

        assert file_path.parent.exists()
        assert file_path.parent.is_dir()

    def test_does_not_fail_if_exists(self, tmp_path):
        """Test does not fail if directory already exists."""
        file_path = tmp_path / "existing" / "file.json"
        file_path.parent.mkdir(parents=True)

        # Should not raise
        ensure_directory(file_path)

        assert file_path.parent.exists()

    def test_handles_permission_error(self, tmp_path):
        """Test handles permission errors gracefully."""
        # Create a read-only file where we'd want a directory
        blocker = tmp_path / "blocked"
        blocker.write_text("blocking")
        blocker.chmod(0o000)

        try:
            file_path = blocker / "nested" / "file.json"
            # Should not raise, just log to stderr
            ensure_directory(file_path)
        finally:
            blocker.chmod(0o644)


class TestReadExistingEntries:
    """Tests for read_existing_entries function."""

    def test_returns_empty_for_nonexistent_file(self, tmp_path):
        """Test returns empty list for non-existent file."""
        file_path = tmp_path / "nonexistent.json"

        result = read_existing_entries(file_path)

        assert result == []

    def test_returns_empty_for_empty_file(self, tmp_path):
        """Test returns empty list for empty file."""
        file_path = tmp_path / "empty.json"
        file_path.write_text("")

        result = read_existing_entries(file_path)

        assert result == []

    def test_returns_empty_for_whitespace_only(self, tmp_path):
        """Test returns empty list for whitespace-only file."""
        file_path = tmp_path / "whitespace.json"
        file_path.write_text("   \n\t  ")

        result = read_existing_entries(file_path)

        assert result == []

    def test_reads_json_array(self, tmp_path):
        """Test reads existing JSON array."""
        file_path = tmp_path / "array.json"
        entries = [{"event": 1}, {"event": 2}]
        file_path.write_text(json.dumps(entries))

        result = read_existing_entries(file_path)

        assert result == entries

    def test_wraps_single_object_in_list(self, tmp_path):
        """Test wraps single JSON object in list."""
        file_path = tmp_path / "single.json"
        entry = {"event": "single"}
        file_path.write_text(json.dumps(entry))

        result = read_existing_entries(file_path)

        assert result == [entry]

    def test_returns_empty_for_invalid_json(self, tmp_path):
        """Test returns empty list for invalid JSON."""
        file_path = tmp_path / "invalid.json"
        file_path.write_text("not valid json {")

        result = read_existing_entries(file_path)

        assert result == []


class TestWriteLogEntry:
    """Tests for write_log_entry function."""

    def test_writes_first_entry(self, tmp_path):
        """Test writes first entry to new file."""
        file_path = tmp_path / "log.json"
        entry = {"session_id": "abc", "event": "test"}

        write_log_entry(file_path, entry)

        content = json.loads(file_path.read_text())
        assert content == [entry]

    def test_appends_to_existing_entries(self, tmp_path):
        """Test appends to existing entries."""
        file_path = tmp_path / "log.json"
        existing = [{"event": "first"}]
        file_path.write_text(json.dumps(existing))

        new_entry = {"event": "second"}
        write_log_entry(file_path, new_entry)

        content = json.loads(file_path.read_text())
        assert len(content) == 2
        assert content[0] == existing[0]
        assert content[1] == new_entry

    def test_creates_parent_directories(self, tmp_path):
        """Test creates parent directories."""
        file_path = tmp_path / "nested" / "deep" / "log.json"
        entry = {"event": "test"}

        write_log_entry(file_path, entry)

        assert file_path.exists()
        content = json.loads(file_path.read_text())
        assert content == [entry]

    def test_pretty_prints_json(self, tmp_path):
        """Test output is pretty-printed."""
        file_path = tmp_path / "log.json"
        entry = {"event": "test", "data": "value"}

        write_log_entry(file_path, entry)

        content = file_path.read_text()
        # Should contain newlines and indentation
        assert "\n" in content
        assert "  " in content

    def test_ends_with_newline(self, tmp_path):
        """Test file ends with newline."""
        file_path = tmp_path / "log.json"
        entry = {"event": "test"}

        write_log_entry(file_path, entry)

        content = file_path.read_text()
        assert content.endswith("\n")

    def test_preserves_unicode(self, tmp_path):
        """Test preserves unicode characters."""
        file_path = tmp_path / "log.json"
        entry = {"text": "日本語 emoji: 🚀"}

        write_log_entry(file_path, entry)

        content = json.loads(file_path.read_text())
        assert content[0]["text"] == "日本語 emoji: 🚀"

    def test_handles_write_error_gracefully(self, tmp_path):
        """Test handles write errors gracefully."""
        # Create a directory where we expect a file
        file_path = tmp_path / "blocked"
        file_path.mkdir()

        # Should not raise, just log to stderr
        entry = {"event": "test"}
        write_log_entry(file_path, entry)
