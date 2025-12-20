"""Tests for playwright_healer hook recovery logic."""

import json
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from claude_apps.hooks.playwright_healer.healer import (
    attempt_recovery,
    get_recovery_state,
    kill_stale_browser_processes,
    remove_browser_lock_files,
    save_recovery_state,
    should_attempt_recovery,
)


class TestGetRecoveryState:
    """Tests for get_recovery_state function."""

    def test_returns_default_state_when_no_file(self, tmp_path):
        """Test returns default state when no state file exists."""
        with patch(
            "claude_apps.hooks.playwright_healer.healer.get_state_path",
            return_value=tmp_path / "nonexistent.json",
        ):
            state = get_recovery_state("session123")

            assert state["attempt_count"] == 0
            assert state["last_attempt_time"] == 0
            assert state["last_error_type"] is None

    def test_reads_existing_state(self, tmp_path):
        """Test reads existing state from file."""
        state_file = tmp_path / "state.json"
        state_file.write_text(json.dumps({
            "attempt_count": 2,
            "last_attempt_time": 12345,
            "last_error_type": "browser_lock"
        }))

        with patch(
            "claude_apps.hooks.playwright_healer.healer.get_state_path",
            return_value=state_file,
        ):
            state = get_recovery_state("session123")

            assert state["attempt_count"] == 2
            assert state["last_error_type"] == "browser_lock"

    def test_returns_default_on_invalid_json(self, tmp_path):
        """Test returns default state on invalid JSON."""
        state_file = tmp_path / "state.json"
        state_file.write_text("invalid json")

        with patch(
            "claude_apps.hooks.playwright_healer.healer.get_state_path",
            return_value=state_file,
        ):
            state = get_recovery_state("session123")

            assert state["attempt_count"] == 0


class TestSaveRecoveryState:
    """Tests for save_recovery_state function."""

    def test_saves_state_to_file(self, tmp_path):
        """Test saves state to file."""
        state_file = tmp_path / "state" / "recovery_state.json"

        with patch(
            "claude_apps.hooks.playwright_healer.healer.get_state_path",
            return_value=state_file,
        ):
            state = {"attempt_count": 1, "last_error_type": "browser_lock"}
            save_recovery_state("session123", state)

            assert state_file.exists()
            saved = json.loads(state_file.read_text())
            assert saved["attempt_count"] == 1

    def test_creates_parent_directories(self, tmp_path):
        """Test creates parent directories."""
        state_file = tmp_path / "nested" / "deep" / "state.json"

        with patch(
            "claude_apps.hooks.playwright_healer.healer.get_state_path",
            return_value=state_file,
        ):
            save_recovery_state("session123", {"attempt_count": 0})

            assert state_file.parent.exists()


class TestShouldAttemptRecovery:
    """Tests for should_attempt_recovery function."""

    def test_allows_first_attempt(self, tmp_path):
        """Test allows first attempt."""
        config = {"max_recovery_attempts": 3, "recovery_cooldown_seconds": 5}
        state_file = tmp_path / "state.json"

        with patch(
            "claude_apps.hooks.playwright_healer.healer.get_config",
            return_value=config,
        ):
            with patch(
                "claude_apps.hooks.playwright_healer.healer.get_state_path",
                return_value=state_file,
            ):
                result = should_attempt_recovery("session123", "browser_lock")

                assert result is True

    def test_allows_different_error_type(self, tmp_path):
        """Test allows attempt for different error type."""
        config = {"max_recovery_attempts": 3, "recovery_cooldown_seconds": 5}
        state_file = tmp_path / "state.json"
        state_file.write_text(json.dumps({
            "attempt_count": 3,
            "last_error_type": "browser_lock",
            "last_attempt_time": time.time()
        }))

        with patch(
            "claude_apps.hooks.playwright_healer.healer.get_config",
            return_value=config,
        ):
            with patch(
                "claude_apps.hooks.playwright_healer.healer.get_state_path",
                return_value=state_file,
            ):
                result = should_attempt_recovery("session123", "browser_closed")

                assert result is True

    def test_blocks_max_attempts_reached(self, tmp_path):
        """Test blocks when max attempts reached."""
        config = {"max_recovery_attempts": 3, "recovery_cooldown_seconds": 5}
        state_file = tmp_path / "state.json"
        state_file.write_text(json.dumps({
            "attempt_count": 3,
            "last_error_type": "browser_lock",
            "last_attempt_time": time.time()
        }))

        with patch(
            "claude_apps.hooks.playwright_healer.healer.get_config",
            return_value=config,
        ):
            with patch(
                "claude_apps.hooks.playwright_healer.healer.get_state_path",
                return_value=state_file,
            ):
                result = should_attempt_recovery("session123", "browser_lock")

                assert result is False

    def test_blocks_during_cooldown(self, tmp_path):
        """Test blocks during cooldown period."""
        config = {"max_recovery_attempts": 3, "recovery_cooldown_seconds": 5}
        state_file = tmp_path / "state.json"
        state_file.write_text(json.dumps({
            "attempt_count": 1,
            "last_error_type": "browser_lock",
            "last_attempt_time": time.time()  # Just now
        }))

        with patch(
            "claude_apps.hooks.playwright_healer.healer.get_config",
            return_value=config,
        ):
            with patch(
                "claude_apps.hooks.playwright_healer.healer.get_state_path",
                return_value=state_file,
            ):
                result = should_attempt_recovery("session123", "browser_lock")

                assert result is False


class TestKillStaleBrowserProcesses:
    """Tests for kill_stale_browser_processes function."""

    def test_returns_success(self):
        """Test returns success result."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            result = kill_stale_browser_processes()

            assert result["success"] is True
            assert result["action"] == "kill_stale_processes"

    def test_handles_timeout(self):
        """Test handles timeout error."""
        import subprocess

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("pkill", 10)

            result = kill_stale_browser_processes()

            assert result["success"] is False
            assert "Timeout" in result["error"]

    def test_handles_exception(self):
        """Test handles other exceptions."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = Exception("Process error")

            result = kill_stale_browser_processes()

            assert result["success"] is False
            assert "Process error" in result["error"]


class TestRemoveBrowserLockFiles:
    """Tests for remove_browser_lock_files function."""

    def test_returns_success_with_no_files(self):
        """Test returns success even with no files to remove."""
        with patch("glob.glob", return_value=[]):
            result = remove_browser_lock_files()

            assert result["success"] is True
            assert result["action"] == "remove_lock_files"

    def test_removes_lock_files(self, tmp_path):
        """Test removes found lock files."""
        lock_file = tmp_path / "SingletonLock"
        lock_file.write_text("")

        with patch("glob.glob", return_value=[str(lock_file)]):
            result = remove_browser_lock_files()

            assert result["success"] is True
            assert len(result["files_removed"]) == 1


class TestAttemptRecovery:
    """Tests for attempt_recovery function."""

    def test_skips_when_blocked(self, tmp_path):
        """Test skips when should_attempt_recovery returns False."""
        with patch(
            "claude_apps.hooks.playwright_healer.healer.should_attempt_recovery",
            return_value=False,
        ):
            error_info = {"error_type": "browser_lock"}
            result = attempt_recovery("session123", "tool", error_info)

            assert result["success"] is False
            assert result["action"] == "skipped"

    def test_handles_browser_lock(self, tmp_path):
        """Test handles browser_lock error type."""
        state_file = tmp_path / "state.json"

        with patch(
            "claude_apps.hooks.playwright_healer.healer.should_attempt_recovery",
            return_value=True,
        ):
            with patch(
                "claude_apps.hooks.playwright_healer.healer.get_state_path",
                return_value=state_file,
            ):
                with patch(
                    "claude_apps.hooks.playwright_healer.healer.remove_browser_lock_files",
                    return_value={"success": True, "message": "Removed locks"},
                ):
                    with patch(
                        "claude_apps.hooks.playwright_healer.healer.kill_stale_browser_processes",
                        return_value={"success": True, "message": "Killed processes"},
                    ):
                        error_info = {"error_type": "browser_lock"}
                        result = attempt_recovery("session123", "tool", error_info)

                        assert result["success"] is True
                        assert result["action"] == "browser_lock_recovery"

    def test_handles_browser_closed(self, tmp_path):
        """Test handles browser_closed error type."""
        state_file = tmp_path / "state.json"

        with patch(
            "claude_apps.hooks.playwright_healer.healer.should_attempt_recovery",
            return_value=True,
        ):
            with patch(
                "claude_apps.hooks.playwright_healer.healer.get_state_path",
                return_value=state_file,
            ):
                error_info = {"error_type": "browser_closed"}
                result = attempt_recovery("session123", "tool", error_info)

                assert result["success"] is True
                assert result["action"] == "browser_closed_recovery"

    def test_handles_connection_lost(self, tmp_path):
        """Test handles connection_lost error type."""
        state_file = tmp_path / "state.json"

        with patch(
            "claude_apps.hooks.playwright_healer.healer.should_attempt_recovery",
            return_value=True,
        ):
            with patch(
                "claude_apps.hooks.playwright_healer.healer.get_state_path",
                return_value=state_file,
            ):
                with patch(
                    "claude_apps.hooks.playwright_healer.healer.kill_stale_browser_processes",
                    return_value={"success": True, "message": "Killed"},
                ):
                    error_info = {"error_type": "connection_lost"}
                    result = attempt_recovery("session123", "tool", error_info)

                    assert result["success"] is True
                    assert result["action"] == "connection_recovery"

    def test_handles_unknown_error_type(self, tmp_path):
        """Test handles unknown error type."""
        state_file = tmp_path / "state.json"

        with patch(
            "claude_apps.hooks.playwright_healer.healer.should_attempt_recovery",
            return_value=True,
        ):
            with patch(
                "claude_apps.hooks.playwright_healer.healer.get_state_path",
                return_value=state_file,
            ):
                error_info = {"error_type": "unknown"}
                result = attempt_recovery("session123", "tool", error_info)

                assert result["success"] is False
                assert result["action"] == "unknown"
