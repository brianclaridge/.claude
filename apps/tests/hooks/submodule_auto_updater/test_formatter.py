"""Tests for submodule update notification formatter."""

import pytest

from claude_apps.hooks.submodule_auto_updater.formatter import format_update_notification
from claude_apps.hooks.submodule_auto_updater.updater import UpdateResult


class TestFormatUpdateNotification:
    """Tests for format_update_notification function."""

    def test_includes_commit_hashes(self):
        """Test includes old and new commit hashes."""
        result = UpdateResult(
            updated=True,
            old_commit="abc12345",
            new_commit="def67890",
            commits_behind=2,
        )

        formatted = format_update_notification(result)

        assert "abc12345"[:8] in formatted
        assert "def67890"[:8] in formatted

    def test_includes_commits_behind_count(self):
        """Test includes number of commits pulled."""
        result = UpdateResult(
            updated=True,
            old_commit="abc",
            new_commit="def",
            commits_behind=5,
        )

        formatted = format_update_notification(result)

        assert "5" in formatted

    def test_includes_commit_list(self):
        """Test includes list of pulled commits."""
        result = UpdateResult(
            updated=True,
            old_commit="abc",
            new_commit="def",
            commits_behind=2,
            commits_pulled=["abc123 Fix critical bug", "def456 Add new feature"],
        )

        formatted = format_update_notification(result)

        assert "Fix critical bug" in formatted
        assert "Add new feature" in formatted

    def test_truncates_long_commit_list(self):
        """Test truncates commit list over 10 items."""
        commits = [f"commit{i} Message {i}" for i in range(15)]
        result = UpdateResult(
            updated=True,
            old_commit="abc",
            new_commit="def",
            commits_behind=15,
            commits_pulled=commits,
        )

        formatted = format_update_notification(result)

        # Should show first 10 and a count of remaining
        assert "and 5 more" in formatted

    def test_handles_empty_commits_list(self):
        """Test handles empty commits list."""
        result = UpdateResult(
            updated=True,
            old_commit="abc",
            new_commit="def",
            commits_behind=0,
            commits_pulled=[],
        )

        formatted = format_update_notification(result)

        assert "## .claude Submodule Updated" in formatted

    def test_handles_none_commits_list(self):
        """Test handles None commits list."""
        result = UpdateResult(
            updated=True,
            old_commit="abc",
            new_commit="def",
            commits_behind=1,
            commits_pulled=None,
        )

        formatted = format_update_notification(result)

        assert "## .claude Submodule Updated" in formatted

    def test_includes_header(self):
        """Test includes markdown header."""
        result = UpdateResult(
            updated=True,
            old_commit="abc",
            new_commit="def",
            commits_behind=1,
        )

        formatted = format_update_notification(result)

        assert "## .claude Submodule Updated" in formatted

    def test_includes_restart_note(self):
        """Test includes note about restart."""
        result = UpdateResult(
            updated=True,
            old_commit="abc",
            new_commit="def",
            commits_behind=1,
        )

        formatted = format_update_notification(result)

        assert "restart" in formatted.lower()
