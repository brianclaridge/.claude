"""Tests for plans collector."""

from pathlib import Path

import pytest

from claude_apps.skills.session_context.collectors.plans_collector import (
    PLAN_FILENAME_PATTERN,
    _check_incomplete_todos,
    _parse_plan_file,
    _scan_plans_directory,
    gather_recent_plans,
)


class TestGatherRecentPlans:
    """Tests for gather_recent_plans function."""

    def test_returns_empty_for_no_plans_dir(self, tmp_path):
        """Test returns empty list when plans dir doesn't exist."""
        nonexistent = tmp_path / "nonexistent"
        result = gather_recent_plans(plans_dir=nonexistent)

        assert result == []

    def test_gathers_plans_from_directory(self, tmp_path):
        """Test gathers plan files from directory."""
        plans_dir = tmp_path / "plans"
        plans_dir.mkdir()
        (plans_dir / "20250115_120000_feature-impl.md").write_text("# Plan: Feature")
        (plans_dir / "20250114_100000_bug-fix.md").write_text("# Plan: Bug Fix")

        result = gather_recent_plans(plans_dir=plans_dir)

        assert len(result) == 2

    def test_sorts_by_date_newest_first(self, tmp_path):
        """Test sorts plans by date, newest first."""
        plans_dir = tmp_path / "plans"
        plans_dir.mkdir()
        (plans_dir / "20250110_100000_old.md").write_text("old")
        (plans_dir / "20250115_120000_new.md").write_text("new")
        (plans_dir / "20250112_150000_mid.md").write_text("mid")

        result = gather_recent_plans(plans_dir=plans_dir)

        assert result[0]["topic"] == "new"
        assert result[1]["topic"] == "mid"
        assert result[2]["topic"] == "old"

    def test_respects_limit(self, tmp_path):
        """Test respects limit parameter."""
        plans_dir = tmp_path / "plans"
        plans_dir.mkdir()
        for i in range(10):
            (plans_dir / f"20250115_{100000 + i}_plan-{i}.md").write_text(f"plan {i}")

        result = gather_recent_plans(limit=3, plans_dir=plans_dir)

        assert len(result) == 3

    def test_skips_non_md_files(self, tmp_path):
        """Test only processes .md files."""
        plans_dir = tmp_path / "plans"
        plans_dir.mkdir()
        (plans_dir / "20250115_120000_plan.md").write_text("plan")
        (plans_dir / "20250115_120000_plan.txt").write_text("not a plan")
        (plans_dir / "notes.json").write_text("{}")

        result = gather_recent_plans(plans_dir=plans_dir)

        assert len(result) == 1
        assert result[0]["filename"] == "20250115_120000_plan.md"


class TestPlanFilenamePattern:
    """Tests for plan filename pattern."""

    def test_matches_valid_pattern(self):
        """Test matches YYYYMMDD_HHMMSS_topic.md pattern."""
        match = PLAN_FILENAME_PATTERN.match("20250115_120000_feature-impl.md")

        assert match is not None
        assert match.group(1) == "20250115"
        assert match.group(2) == "120000"
        assert match.group(3) == "feature-impl"

    def test_matches_topic_with_underscores(self):
        """Test matches topic with underscores."""
        match = PLAN_FILENAME_PATTERN.match("20250115_120000_my_cool_feature.md")

        assert match is not None
        assert match.group(3) == "my_cool_feature"

    def test_no_match_for_invalid_format(self):
        """Test no match for invalid format."""
        assert PLAN_FILENAME_PATTERN.match("random-file.md") is None
        assert PLAN_FILENAME_PATTERN.match("2025-01-15_plan.md") is None
        assert PLAN_FILENAME_PATTERN.match("plan.md") is None


class TestParsePlanFile:
    """Tests for _parse_plan_file function."""

    def test_parses_standard_filename(self, tmp_path):
        """Test parses standard filename pattern."""
        plan_file = tmp_path / "20250115_143052_user-auth.md"
        plan_file.write_text("# Plan: User Auth")

        result = _parse_plan_file(plan_file)

        assert result["filename"] == "20250115_143052_user-auth.md"
        assert result["topic"] == "user-auth"
        assert result["date"] == "2025-01-15"
        assert result["time"] == "14:30:52"
        assert result["sort_key"] == "20250115_143052"

    def test_parses_nonstandard_filename(self, tmp_path):
        """Test parses non-standard filename using mtime."""
        plan_file = tmp_path / "my-random-plan.md"
        plan_file.write_text("# Random Plan")

        result = _parse_plan_file(plan_file)

        assert result["filename"] == "my-random-plan.md"
        assert result["topic"] == "my-random-plan"
        assert "date" in result
        assert "time" in result

    def test_includes_path(self, tmp_path):
        """Test includes full path."""
        plan_file = tmp_path / "20250115_120000_test.md"
        plan_file.write_text("content")

        result = _parse_plan_file(plan_file)

        assert result["path"] == str(plan_file)

    def test_detects_incomplete_todos(self, tmp_path):
        """Test detects incomplete TODO items."""
        plan_file = tmp_path / "20250115_120000_incomplete.md"
        plan_file.write_text("- [ ] Task 1\n- [x] Task 2")

        result = _parse_plan_file(plan_file)

        assert result["has_incomplete_todos"] is True

    def test_no_incomplete_todos(self, tmp_path):
        """Test when all todos are complete."""
        plan_file = tmp_path / "20250115_120000_complete.md"
        plan_file.write_text("- [x] Task 1\n- [x] Task 2")

        result = _parse_plan_file(plan_file)

        assert result["has_incomplete_todos"] is False


class TestScanPlansDirectory:
    """Tests for _scan_plans_directory function."""

    def test_scans_all_md_files(self, tmp_path):
        """Test scans all .md files in directory."""
        plans_dir = tmp_path / "plans"
        plans_dir.mkdir()
        (plans_dir / "plan1.md").write_text("plan 1")
        (plans_dir / "plan2.md").write_text("plan 2")
        (plans_dir / "plan3.md").write_text("plan 3")

        result = _scan_plans_directory(plans_dir)

        assert len(result) == 3

    def test_ignores_subdirectories(self, tmp_path):
        """Test ignores subdirectories."""
        plans_dir = tmp_path / "plans"
        plans_dir.mkdir()
        (plans_dir / "plan.md").write_text("plan")
        subdir = plans_dir / "subdir"
        subdir.mkdir()
        (subdir / "nested.md").write_text("nested")

        result = _scan_plans_directory(plans_dir)

        # Only top-level files
        assert len(result) == 1


class TestCheckIncompleteTodos:
    """Tests for _check_incomplete_todos function."""

    def test_detects_unchecked_checkbox(self, tmp_path):
        """Test detects unchecked markdown checkbox."""
        plan_file = tmp_path / "plan.md"
        plan_file.write_text("- [ ] Unchecked task")

        assert _check_incomplete_todos(plan_file) is True

    def test_detects_pending_status(self, tmp_path):
        """Test detects pending status."""
        plan_file = tmp_path / "plan.md"
        plan_file.write_text("Status: - pending")

        assert _check_incomplete_todos(plan_file) is True

    def test_detects_in_progress_status(self, tmp_path):
        """Test detects in_progress status."""
        plan_file = tmp_path / "plan.md"
        plan_file.write_text("in_progress")

        assert _check_incomplete_todos(plan_file) is True

    def test_detects_todo_marker(self, tmp_path):
        """Test detects TODO: marker."""
        plan_file = tmp_path / "plan.md"
        plan_file.write_text("TODO: Fix this")

        assert _check_incomplete_todos(plan_file) is True

    def test_no_incomplete_todos(self, tmp_path):
        """Test returns False when no incomplete todos."""
        plan_file = tmp_path / "plan.md"
        plan_file.write_text("- [x] All done\nCompleted!")

        assert _check_incomplete_todos(plan_file) is False

    def test_handles_read_error(self, tmp_path):
        """Test handles file read error gracefully."""
        plan_file = tmp_path / "nonexistent.md"

        # Should not raise, returns False
        assert _check_incomplete_todos(plan_file) is False

    def test_case_insensitive(self, tmp_path):
        """Test pattern matching is case insensitive."""
        plan_file = tmp_path / "plan.md"
        plan_file.write_text("todo: lowercase marker")

        assert _check_incomplete_todos(plan_file) is True
