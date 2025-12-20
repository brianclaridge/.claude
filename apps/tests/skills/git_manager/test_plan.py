"""Tests for plan file parsing."""

from pathlib import Path

import pytest

from claude_apps.skills.git_manager.plan import (
    PlanInfo,
    extract_plan_info,
    find_active_plan,
)


class TestPlanInfo:
    """Tests for PlanInfo dataclass."""

    def test_defaults(self):
        """Test default values."""
        info = PlanInfo(path=Path("/test"))

        assert info.path == Path("/test")
        assert info.topic == ""
        assert info.objective == ""
        assert info.summary == ""
        assert info.status == ""
        assert info.completed_todos == []
        assert info.pending_todos == []


class TestExtractPlanInfo:
    """Tests for extract_plan_info function."""

    def test_extracts_topic_from_filename(self, tmp_path):
        """Test extracting topic from plan filename."""
        plan_file = tmp_path / "20250115_120000_user-authentication.md"
        plan_file.write_text("# Plan: User Authentication\n")

        info = extract_plan_info(plan_file)

        assert info.topic == "user-authentication"

    def test_extracts_objective_from_title(self, tmp_path):
        """Test extracting objective from title."""
        plan_file = tmp_path / "20250115_120000_feature.md"
        plan_file.write_text("# Plan: Implement OAuth2 Flow\n\nContent here")

        info = extract_plan_info(plan_file)

        assert info.objective == "Implement OAuth2 Flow"

    def test_strips_plan_prefix(self, tmp_path):
        """Test that Plan: prefix is stripped from objective."""
        plan_file = tmp_path / "plan.md"
        plan_file.write_text("# Plan: Add Feature\n")

        info = extract_plan_info(plan_file)

        assert info.objective == "Add Feature"

    def test_extracts_status(self, tmp_path):
        """Test extracting status field."""
        plan_file = tmp_path / "plan.md"
        plan_file.write_text("# Plan\n\n**Status:** In Progress\n")

        info = extract_plan_info(plan_file)

        assert info.status == "In Progress"

    def test_extracts_summary_section(self, tmp_path):
        """Test extracting summary section."""
        plan_file = tmp_path / "plan.md"
        plan_file.write_text(
            "# Plan\n\n"
            "## Summary\n"
            "This is the summary text.\n"
            "Multiple lines work.\n"
            "## Next Section\n"
        )

        info = extract_plan_info(plan_file)

        assert "This is the summary text." in info.summary
        assert "Multiple lines work." in info.summary

    def test_extracts_completed_todos(self, tmp_path):
        """Test extracting completed TODO items."""
        plan_file = tmp_path / "plan.md"
        plan_file.write_text(
            "# Plan\n\n"
            "## TODO\n"
            "- [x] First completed item\n"
            "- [X] Second completed item\n"
            "- [ ] Pending item\n"
        )

        info = extract_plan_info(plan_file)

        assert len(info.completed_todos) == 2
        assert "First completed item" in info.completed_todos
        assert "Second completed item" in info.completed_todos

    def test_extracts_pending_todos(self, tmp_path):
        """Test extracting pending TODO items."""
        plan_file = tmp_path / "plan.md"
        plan_file.write_text(
            "# Plan\n\n"
            "## TODO\n"
            "- [x] Completed\n"
            "- [ ] First pending\n"
            "- [ ] Second pending\n"
        )

        info = extract_plan_info(plan_file)

        assert len(info.pending_todos) == 2
        assert "First pending" in info.pending_todos
        assert "Second pending" in info.pending_todos

    def test_extracts_from_completed_section(self, tmp_path):
        """Test extracting from ## Completed section."""
        plan_file = tmp_path / "plan.md"
        plan_file.write_text(
            "# Plan\n\n"
            "## Completed\n"
            "- [x] Done task one\n"
            "- [x] Done task two\n"
        )

        info = extract_plan_info(plan_file)

        assert len(info.completed_todos) == 2

    def test_handles_missing_sections(self, tmp_path):
        """Test handling file with minimal content."""
        plan_file = tmp_path / "plan.md"
        plan_file.write_text("Just some text\n")

        info = extract_plan_info(plan_file)

        assert info.objective == ""
        assert info.summary == ""
        assert info.completed_todos == []

    def test_topic_with_simple_filename(self, tmp_path):
        """Test topic extraction with simple filename."""
        plan_file = tmp_path / "feature.md"
        plan_file.write_text("# Feature\n")

        info = extract_plan_info(plan_file)

        # Simple filename without timestamp parts
        assert info.topic == ""


class TestFindActivePlan:
    """Tests for find_active_plan function."""

    def test_returns_none_for_nonexistent_dir(self, tmp_path):
        """Test returns None when directory doesn't exist."""
        result = find_active_plan(tmp_path / "nonexistent")
        assert result is None

    def test_returns_none_for_empty_dir(self, tmp_path):
        """Test returns None when directory is empty."""
        result = find_active_plan(tmp_path)
        assert result is None

    def test_skips_completed_plans(self, tmp_path):
        """Test that completed plans are skipped."""
        import os
        import time

        completed = tmp_path / "20250115_120000_old.md"
        completed.write_text("# Old Plan\n\n**Status:** Completed\n")

        active = tmp_path / "20250115_120001_active.md"
        active.write_text("# Active Plan\n\n## TODO\n- [ ] Pending task\n")

        # Ensure active file is more recent
        now = time.time()
        os.utime(completed, (now - 10, now - 10))
        os.utime(active, (now, now))

        result = find_active_plan(tmp_path)

        assert result is not None
        assert result.topic == "active"

    def test_returns_plan_with_pending_todos(self, tmp_path):
        """Test returns plan with pending TODOs."""
        plan = tmp_path / "20250115_120000_feature.md"
        plan.write_text(
            "# Feature Plan\n\n"
            "## TODO\n"
            "- [x] Done\n"
            "- [ ] Still pending\n"
        )

        result = find_active_plan(tmp_path)

        assert result is not None
        assert len(result.pending_todos) == 1

    def test_returns_plan_with_completed_todos(self, tmp_path):
        """Test returns plan with completed TODOs."""
        plan = tmp_path / "20250115_120000_done.md"
        plan.write_text(
            "# Done Plan\n\n"
            "## TODO\n"
            "- [x] All done\n"
        )

        result = find_active_plan(tmp_path)

        assert result is not None
        assert len(result.completed_todos) == 1

    def test_returns_most_recent(self, tmp_path):
        """Test returns most recently modified plan."""
        import time

        old = tmp_path / "20250115_100000_old.md"
        old.write_text("# Old\n\n- [ ] Task\n")
        time.sleep(0.1)

        new = tmp_path / "20250115_110000_new.md"
        new.write_text("# New\n\n- [ ] Task\n")

        result = find_active_plan(tmp_path)

        assert result is not None
        assert result.topic == "new"

    def test_returns_plan_with_objective(self, tmp_path):
        """Test fallback to plan with objective."""
        plan = tmp_path / "20250115_120000_feature.md"
        plan.write_text("# Plan: Important Feature\n")

        result = find_active_plan(tmp_path)

        assert result is not None
        assert "Important Feature" in result.objective
