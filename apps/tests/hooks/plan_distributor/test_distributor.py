"""Tests for plan distributor logic."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from claude_apps.hooks.plan_distributor.distributor import (
    DistributionResult,
    distribute_plan,
    get_distribution_summary,
    get_plans_directory,
)


class TestDistributionResult:
    """Tests for DistributionResult NamedTuple."""

    def test_creation(self):
        """Test creating result."""
        result = DistributionResult(
            source_path="/path/to/plan.md",
            destinations=["/dest/plan.md"],
            success=True,
            message="Distributed successfully",
        )

        assert result.source_path == "/path/to/plan.md"
        assert result.destinations == ["/dest/plan.md"]
        assert result.success is True
        assert result.message == "Distributed successfully"

    def test_failed_result(self):
        """Test creating failed result."""
        result = DistributionResult(
            source_path="/path/to/plan.md",
            destinations=[],
            success=False,
            message="File not found",
        )

        assert result.success is False
        assert result.destinations == []


class TestGetPlansDirectory:
    """Tests for get_plans_directory function."""

    def test_returns_path_from_env(self, monkeypatch):
        """Test returns path from CLAUDE_PLANS_PATH."""
        monkeypatch.setenv("CLAUDE_PLANS_PATH", "/custom/plans")

        result = get_plans_directory()

        assert result == Path("/custom/plans")

    def test_raises_when_env_not_set(self, monkeypatch):
        """Test raises ValueError when env var not set."""
        monkeypatch.delenv("CLAUDE_PLANS_PATH", raising=False)

        with pytest.raises(ValueError, match="CLAUDE_PLANS_PATH environment variable is not set"):
            get_plans_directory()


class TestDistributePlan:
    """Tests for distribute_plan function."""

    def test_returns_error_when_source_not_found(self, tmp_path, monkeypatch):
        """Test returns error when source file doesn't exist."""
        monkeypatch.setenv("CLAUDE_PLANS_PATH", str(tmp_path / "plans"))
        source = str(tmp_path / "nonexistent.md")

        result = distribute_plan(source)

        assert result.success is False
        assert "not found" in result.message
        assert result.destinations == []

    def test_returns_error_when_env_not_set(self, tmp_path, monkeypatch):
        """Test returns error when CLAUDE_PLANS_PATH not set."""
        monkeypatch.delenv("CLAUDE_PLANS_PATH", raising=False)
        source = tmp_path / "plan.md"
        source.write_text("# Plan: Test")

        result = distribute_plan(str(source))

        assert result.success is False
        assert "CLAUDE_PLANS_PATH" in result.message

    def test_creates_destination_directory(self, tmp_path, monkeypatch):
        """Test creates destination directory if not exists."""
        plans_dir = tmp_path / "new_plans"
        monkeypatch.setenv("CLAUDE_PLANS_PATH", str(plans_dir))

        source = tmp_path / "source.md"
        source.write_text("# Plan: Test Topic")

        assert not plans_dir.exists()

        result = distribute_plan(str(source))

        assert result.success is True
        assert plans_dir.exists()

    def test_copies_plan_to_destination(self, tmp_path, monkeypatch):
        """Test copies plan file to destination."""
        plans_dir = tmp_path / "plans"
        plans_dir.mkdir()
        monkeypatch.setenv("CLAUDE_PLANS_PATH", str(plans_dir))

        source = tmp_path / "source.md"
        source.write_text("# Plan: Test Topic\n\nContent here.")

        result = distribute_plan(str(source))

        assert result.success is True
        assert len(result.destinations) == 1

        dest_path = Path(result.destinations[0])
        assert dest_path.exists()
        assert "test-topic" in dest_path.name
        assert dest_path.read_text() == source.read_text()

    def test_generates_proper_filename(self, tmp_path, monkeypatch):
        """Test generates filename with timestamp and topic."""
        plans_dir = tmp_path / "plans"
        plans_dir.mkdir()
        monkeypatch.setenv("CLAUDE_PLANS_PATH", str(plans_dir))

        source = tmp_path / "random-name.md"
        source.write_text("# Plan: User Authentication")

        result = distribute_plan(str(source))

        assert result.success is True
        dest_path = Path(result.destinations[0])
        # Filename format: YYYYMMDD_HHMMSS_topic.md
        assert dest_path.suffix == ".md"
        assert "user-authentication" in dest_path.name

    def test_handles_copy_error(self, tmp_path, monkeypatch):
        """Test handles OS errors during copy."""
        plans_dir = tmp_path / "plans"
        monkeypatch.setenv("CLAUDE_PLANS_PATH", str(plans_dir))

        source = tmp_path / "source.md"
        source.write_text("# Plan: Test")

        with patch("shutil.copy2") as mock_copy:
            mock_copy.side_effect = OSError("Permission denied")

            result = distribute_plan(str(source))

            assert result.success is False
            assert "Permission denied" in result.message

    def test_workspace_root_parameter_unused(self, tmp_path, monkeypatch):
        """Test workspace_root parameter is ignored."""
        plans_dir = tmp_path / "plans"
        plans_dir.mkdir()
        monkeypatch.setenv("CLAUDE_PLANS_PATH", str(plans_dir))

        source = tmp_path / "source.md"
        source.write_text("# Plan: Test")

        # workspace_root should not affect behavior
        result = distribute_plan(str(source), workspace_root="/ignored/path")

        assert result.success is True


class TestGetDistributionSummary:
    """Tests for get_distribution_summary function."""

    def test_formats_success_result(self):
        """Test formats successful distribution."""
        result = DistributionResult(
            source_path="/source/plan.md",
            destinations=["/dest/plan.md"],
            success=True,
            message="Plan distributed successfully",
        )

        summary = get_distribution_summary(result)

        assert "Source: /source/plan.md" in summary
        assert "Status: Success" in summary
        assert "Plan distributed successfully" in summary
        assert "Destinations:" in summary
        assert "/dest/plan.md" in summary

    def test_formats_failure_result(self):
        """Test formats failed distribution."""
        result = DistributionResult(
            source_path="/source/plan.md",
            destinations=[],
            success=False,
            message="File not found",
        )

        summary = get_distribution_summary(result)

        assert "Status: Failed" in summary
        assert "File not found" in summary
        assert "Destinations:" not in summary

    def test_formats_multiple_destinations(self):
        """Test formats multiple destinations."""
        result = DistributionResult(
            source_path="/source/plan.md",
            destinations=["/dest1/plan.md", "/dest2/plan.md"],
            success=True,
            message="Distributed to multiple locations",
        )

        summary = get_distribution_summary(result)

        assert "/dest1/plan.md" in summary
        assert "/dest2/plan.md" in summary
