"""Tests for submodule auto-updater state management."""

import json
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from claude_apps.hooks.submodule_auto_updater.updater import UpdateResult


class TestStateManager:
    """Tests for state management functions."""

    @pytest.fixture(autouse=True)
    def setup_data_dir(self, tmp_path, monkeypatch):
        """Set up temp data directory."""
        data_dir = tmp_path / "data"
        monkeypatch.setattr(
            "claude_apps.hooks.submodule_auto_updater.state_manager.DATA_DIR",
            data_dir,
        )
        monkeypatch.setattr(
            "claude_apps.hooks.submodule_auto_updater.state_manager.CHECK_STATE_FILE",
            data_dir / "submodule_check_state.json",
        )
        monkeypatch.setattr(
            "claude_apps.hooks.submodule_auto_updater.state_manager.NOTIFY_STATE_FILE",
            data_dir / "submodule_notify_state.json",
        )
        self.data_dir = data_dir
        self.check_file = data_dir / "submodule_check_state.json"
        self.notify_file = data_dir / "submodule_notify_state.json"

    def test_ensure_data_dir_creates_directory(self):
        """Test creates data directory."""
        from claude_apps.hooks.submodule_auto_updater.state_manager import ensure_data_dir

        ensure_data_dir()

        assert self.data_dir.exists()

    def test_read_check_state_returns_empty_when_no_file(self):
        """Test returns empty dict when file doesn't exist."""
        from claude_apps.hooks.submodule_auto_updater.state_manager import read_check_state

        result = read_check_state()

        assert result == {}

    def test_read_check_state_parses_json(self):
        """Test parses JSON from file."""
        from claude_apps.hooks.submodule_auto_updater.state_manager import read_check_state

        self.data_dir.mkdir(parents=True)
        self.check_file.write_text('{"last_check_time": 12345}')

        result = read_check_state()

        assert result["last_check_time"] == 12345

    def test_read_check_state_handles_invalid_json(self):
        """Test handles invalid JSON gracefully."""
        from claude_apps.hooks.submodule_auto_updater.state_manager import read_check_state

        self.data_dir.mkdir(parents=True)
        self.check_file.write_text("not valid json")

        result = read_check_state()

        assert result == {}

    def test_write_check_state_creates_file(self):
        """Test creates state file."""
        from claude_apps.hooks.submodule_auto_updater.state_manager import write_check_state

        write_check_state()

        assert self.check_file.exists()
        state = json.loads(self.check_file.read_text())
        assert "last_check_time" in state
        assert "last_check_iso" in state

    def test_write_check_state_with_update_result(self):
        """Test writes update result when provided."""
        from claude_apps.hooks.submodule_auto_updater.state_manager import write_check_state

        result = UpdateResult(
            updated=True,
            old_commit="abc123",
            new_commit="def456",
            commits_behind=3,
            commits_pulled=["fix bug"],
        )

        write_check_state(result)

        state = json.loads(self.check_file.read_text())
        assert "last_update_time" in state
        assert state["last_update_result"]["updated"] is True
        assert state["last_update_result"]["old_commit"] == "abc123"

    def test_should_check_returns_true_when_no_state(self):
        """Test returns True when no previous check."""
        from claude_apps.hooks.submodule_auto_updater.state_manager import should_check

        with patch(
            "claude_apps.hooks.submodule_auto_updater.state_manager.get_check_interval_seconds"
        ) as mock_interval:
            mock_interval.return_value = 3600

            result = should_check()

            assert result is True

    def test_should_check_returns_false_when_recent(self):
        """Test returns False when checked recently."""
        from claude_apps.hooks.submodule_auto_updater.state_manager import (
            should_check,
            write_check_state,
        )

        write_check_state()  # Write current time

        with patch(
            "claude_apps.hooks.submodule_auto_updater.state_manager.get_check_interval_seconds"
        ) as mock_interval:
            mock_interval.return_value = 3600  # 1 hour

            result = should_check()

            assert result is False

    def test_should_check_returns_true_when_interval_passed(self):
        """Test returns True when interval has passed."""
        from claude_apps.hooks.submodule_auto_updater.state_manager import (
            read_check_state,
            should_check,
        )

        # Write old timestamp
        self.data_dir.mkdir(parents=True)
        old_time = time.time() - 7200  # 2 hours ago
        self.check_file.write_text(json.dumps({"last_check_time": old_time}))

        with patch(
            "claude_apps.hooks.submodule_auto_updater.state_manager.get_check_interval_seconds"
        ) as mock_interval:
            mock_interval.return_value = 3600  # 1 hour

            result = should_check()

            assert result is True

    def test_read_notify_state_returns_empty_when_no_file(self):
        """Test returns empty dict when notify file doesn't exist."""
        from claude_apps.hooks.submodule_auto_updater.state_manager import read_notify_state

        result = read_notify_state()

        assert result == {}

    def test_should_notify_returns_true_for_new_session(self):
        """Test returns True for new session."""
        from claude_apps.hooks.submodule_auto_updater.state_manager import should_notify

        result = should_notify("new-session-123")

        assert result is True

    def test_should_notify_returns_false_for_same_session(self):
        """Test returns False for same session."""
        from claude_apps.hooks.submodule_auto_updater.state_manager import (
            mark_notified,
            should_notify,
        )

        mark_notified("session-123")

        result = should_notify("session-123")

        assert result is False

    def test_should_notify_returns_true_for_different_session(self):
        """Test returns True for different session."""
        from claude_apps.hooks.submodule_auto_updater.state_manager import (
            mark_notified,
            should_notify,
        )

        mark_notified("session-123")

        result = should_notify("session-456")

        assert result is True

    def test_mark_notified_creates_file(self):
        """Test creates notify state file."""
        from claude_apps.hooks.submodule_auto_updater.state_manager import mark_notified

        mark_notified("my-session")

        assert self.notify_file.exists()
        state = json.loads(self.notify_file.read_text())
        assert state["last_notified_session"] == "my-session"
