"""Tests for pending work detection."""

from pathlib import Path
from unittest.mock import patch

import pytest

from claude_apps.skills.session_context.collectors.pending_work import (
    _build_summary,
    detect_pending_work,
)


class TestDetectPendingWork:
    """Tests for detect_pending_work function."""

    def test_no_pending_work(self, tmp_path):
        """Test when no pending work exists."""
        plans_dir = tmp_path / "plans"
        plans_dir.mkdir()
        # Create complete plan
        (plans_dir / "20250115_120000_done.md").write_text("- [x] Complete")

        with patch(
            "claude_apps.skills.session_context.collectors.pending_work.gather_git_context"
        ) as mock_git:
            mock_git.return_value = {
                "has_pending_work": False,
                "uncommitted_changes": {"staged": 0, "unstaged": 0, "untracked": 0},
            }

            result = detect_pending_work(tmp_path, plans_dir)

            assert result["has_pending_work"] is False
            assert result["git_pending"]["has_changes"] is False
            assert result["plans_pending"]["count"] == 0

    def test_detects_git_pending_work(self, tmp_path):
        """Test detects pending work from git."""
        with patch(
            "claude_apps.skills.session_context.collectors.pending_work.gather_git_context"
        ) as mock_git:
            mock_git.return_value = {
                "has_pending_work": True,
                "uncommitted_changes": {"staged": 2, "unstaged": 1, "untracked": 3},
            }
            with patch(
                "claude_apps.skills.session_context.collectors.pending_work.gather_recent_plans"
            ) as mock_plans:
                mock_plans.return_value = []

                result = detect_pending_work(tmp_path)

                assert result["has_pending_work"] is True
                assert result["git_pending"]["has_changes"] is True
                assert result["git_pending"]["staged"] == 2
                assert result["git_pending"]["unstaged"] == 1
                assert result["git_pending"]["untracked"] == 3

    def test_detects_plans_pending_work(self, tmp_path):
        """Test detects pending work from plans."""
        plans_dir = tmp_path / "plans"
        plans_dir.mkdir()

        with patch(
            "claude_apps.skills.session_context.collectors.pending_work.gather_git_context"
        ) as mock_git:
            mock_git.return_value = {
                "has_pending_work": False,
                "uncommitted_changes": {"staged": 0, "unstaged": 0, "untracked": 0},
            }
            with patch(
                "claude_apps.skills.session_context.collectors.pending_work.gather_recent_plans"
            ) as mock_plans:
                mock_plans.return_value = [
                    {"filename": "plan1.md", "has_incomplete_todos": True},
                    {"filename": "plan2.md", "has_incomplete_todos": False},
                    {"filename": "plan3.md", "has_incomplete_todos": True},
                ]

                result = detect_pending_work(tmp_path, plans_dir)

                assert result["has_pending_work"] is True
                assert result["plans_pending"]["count"] == 2
                assert "plan1.md" in result["plans_pending"]["files"]
                assert "plan3.md" in result["plans_pending"]["files"]

    def test_detects_both_git_and_plans(self, tmp_path):
        """Test detects pending work from both sources."""
        with patch(
            "claude_apps.skills.session_context.collectors.pending_work.gather_git_context"
        ) as mock_git:
            mock_git.return_value = {
                "has_pending_work": True,
                "uncommitted_changes": {"staged": 1, "unstaged": 0, "untracked": 0},
            }
            with patch(
                "claude_apps.skills.session_context.collectors.pending_work.gather_recent_plans"
            ) as mock_plans:
                mock_plans.return_value = [
                    {"filename": "plan.md", "has_incomplete_todos": True},
                ]

                result = detect_pending_work(tmp_path)

                assert result["has_pending_work"] is True
                assert result["git_pending"]["has_changes"] is True
                assert result["plans_pending"]["count"] == 1

    def test_includes_summary(self, tmp_path):
        """Test includes human-readable summary."""
        with patch(
            "claude_apps.skills.session_context.collectors.pending_work.gather_git_context"
        ) as mock_git:
            mock_git.return_value = {
                "has_pending_work": True,
                "uncommitted_changes": {"staged": 2, "unstaged": 0, "untracked": 0},
            }
            with patch(
                "claude_apps.skills.session_context.collectors.pending_work.gather_recent_plans"
            ) as mock_plans:
                mock_plans.return_value = []

                result = detect_pending_work(tmp_path)

                assert "summary" in result
                assert "staged" in result["summary"].lower()


class TestBuildSummary:
    """Tests for _build_summary function."""

    def test_no_pending_work(self):
        """Test summary when no pending work."""
        result = _build_summary(False, {}, [])

        assert result == "No pending work detected"

    def test_staged_files_only(self):
        """Test summary with staged files only."""
        uncommitted = {"staged": 3, "unstaged": 0, "untracked": 0}
        result = _build_summary(True, uncommitted, [])

        assert "3 staged" in result
        assert "Git:" in result

    def test_unstaged_files_only(self):
        """Test summary with unstaged files only."""
        uncommitted = {"staged": 0, "unstaged": 2, "untracked": 0}
        result = _build_summary(True, uncommitted, [])

        assert "2 unstaged" in result

    def test_untracked_files_only(self):
        """Test summary with untracked files only."""
        uncommitted = {"staged": 0, "unstaged": 0, "untracked": 5}
        result = _build_summary(True, uncommitted, [])

        assert "5 untracked" in result

    def test_all_git_changes(self):
        """Test summary with all types of git changes."""
        uncommitted = {"staged": 1, "unstaged": 2, "untracked": 3}
        result = _build_summary(True, uncommitted, [])

        assert "1 staged" in result
        assert "2 unstaged" in result
        assert "3 untracked" in result

    def test_plans_pending(self):
        """Test summary with pending plans."""
        plans = [{"filename": "p1"}, {"filename": "p2"}]
        result = _build_summary(False, {}, plans)

        assert "2 with incomplete TODOs" in result
        assert "Plans:" in result

    def test_combined_summary(self):
        """Test summary with both git and plans."""
        uncommitted = {"staged": 2, "unstaged": 0, "untracked": 0}
        plans = [{"filename": "p1"}]
        result = _build_summary(True, uncommitted, plans)

        assert "Git:" in result
        assert "Plans:" in result
        assert ";" in result  # Separator

    def test_git_pending_false_but_has_untracked(self):
        """Test when git_pending is False but has untracked files."""
        # This case shouldn't happen in practice, but test behavior
        uncommitted = {"staged": 0, "unstaged": 0, "untracked": 5}
        result = _build_summary(False, uncommitted, [])

        # git_pending=False means no changes section
        assert result == "No pending work detected"
