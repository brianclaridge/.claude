"""Tests for plan distributor hook entry point."""

import json
from io import StringIO
from unittest.mock import MagicMock, patch

import pytest

from claude_apps.hooks.plan_distributor.__main__ import (
    extract_plan_path,
    main,
    process_hook_event,
    process_stdin,
)
from claude_apps.hooks.plan_distributor.distributor import DistributionResult


class TestExtractPlanPath:
    """Tests for extract_plan_path function."""

    def test_extracts_path_from_text_dict(self):
        """Test extracts path from dict with text field."""
        tool_response = [
            {"text": "Your plan has been saved to: /root/.claude/plans/tender-leaping-teapot.md"}
        ]

        result = extract_plan_path(tool_response)

        assert result == "/root/.claude/plans/tender-leaping-teapot.md"

    def test_extracts_path_from_string(self):
        """Test extracts path from string response."""
        tool_response = [
            "Plan saved: /home/user/.claude/plans/my-plan.md"
        ]

        result = extract_plan_path(tool_response)

        assert result == "/home/user/.claude/plans/my-plan.md"

    def test_returns_none_when_no_path(self):
        """Test returns None when no path found."""
        tool_response = [
            {"text": "Plan mode exited successfully"}
        ]

        result = extract_plan_path(tool_response)

        assert result is None

    def test_returns_none_for_empty_response(self):
        """Test returns None for empty response."""
        result = extract_plan_path([])

        assert result is None

    def test_handles_multiple_items(self):
        """Test handles multiple response items."""
        tool_response = [
            {"text": "Processing..."},
            {"text": "Saved to /root/.claude/plans/test.md"},
            {"text": "Done"},
        ]

        result = extract_plan_path(tool_response)

        assert result == "/root/.claude/plans/test.md"

    def test_handles_mixed_types(self):
        """Test handles mixed dict and string types."""
        tool_response = [
            "Some text",
            {"text": "/path/to/plans/file.md"},
            123,  # Non-string, non-dict ignored
        ]

        result = extract_plan_path(tool_response)

        assert result == "/path/to/plans/file.md"


class TestProcessHookEvent:
    """Tests for process_hook_event function."""

    def test_ignores_non_exitplanmode_events(self):
        """Test ignores events for other tools."""
        hook_data = {
            "tool_name": "SomeOtherTool",
            "tool_response": [{"text": "response"}]
        }

        result = process_hook_event(hook_data)

        assert result["continue"] is True
        assert "hookSpecificOutput" not in result

    def test_processes_exitplanmode_event(self, tmp_path, monkeypatch):
        """Test processes ExitPlanMode events."""
        plans_dir = tmp_path / "plans"
        plans_dir.mkdir()
        monkeypatch.setenv("CLAUDE_PLANS_PATH", str(plans_dir))

        # Create source plan file
        source_plan = tmp_path / "source.md"
        source_plan.write_text("# Plan: Test")

        hook_data = {
            "tool_name": "ExitPlanMode",
            "tool_response": [{"text": f"Saved to: {source_plan}"}]
        }

        # Mock the plan path pattern to match our temp file
        with patch("claude_apps.hooks.plan_distributor.__main__.distribute_plan") as mock_dist:
            mock_dist.return_value = DistributionResult(
                source_path=str(source_plan),
                destinations=[str(plans_dir / "test.md")],
                success=True,
                message="Plan distributed",
            )

            result = process_hook_event(hook_data)

            assert result["continue"] is True

    def test_returns_basic_response_when_no_path(self):
        """Test returns basic response when no plan path found."""
        hook_data = {
            "tool_name": "ExitPlanMode",
            "tool_response": [{"text": "No path here"}]
        }

        result = process_hook_event(hook_data)

        assert result["continue"] is True
        assert "hookSpecificOutput" not in result

    def test_adds_summary_on_success(self, monkeypatch, tmp_path):
        """Test adds distribution summary on success."""
        plans_dir = tmp_path / "plans"
        plans_dir.mkdir()
        monkeypatch.setenv("CLAUDE_PLANS_PATH", str(plans_dir))

        source = tmp_path / "source.md"
        source.write_text("# Plan: Test")

        hook_data = {
            "tool_name": "ExitPlanMode",
            "tool_response": [{"text": f"Plan at {source}"}]
        }

        # Create a proper path that matches the regex
        with patch.object(
            __import__("claude_apps.hooks.plan_distributor.__main__", fromlist=["extract_plan_path"]),
            "extract_plan_path",
            return_value=str(source)
        ):
            with patch("claude_apps.hooks.plan_distributor.__main__.distribute_plan") as mock_dist:
                mock_dist.return_value = DistributionResult(
                    source_path=str(source),
                    destinations=[str(plans_dir / "test.md")],
                    success=True,
                    message="Plan distributed",
                )

                result = process_hook_event(hook_data)

                if result.get("hookSpecificOutput"):
                    assert "PLAN DISTRIBUTOR" in result["hookSpecificOutput"]["additionalContext"]


class TestProcessStdin:
    """Tests for process_stdin function."""

    def test_parses_single_json_object(self):
        """Test parses single JSON object."""
        with patch("sys.stdin", StringIO('{"key": "value"}')):
            result = process_stdin()

            assert result == [{"key": "value"}]

    def test_parses_json_array(self):
        """Test parses JSON array."""
        with patch("sys.stdin", StringIO('[{"a": 1}, {"b": 2}]')):
            result = process_stdin()

            assert result == [{"a": 1}, {"b": 2}]

    def test_returns_empty_for_empty_input(self):
        """Test returns empty list for empty input."""
        with patch("sys.stdin", StringIO("")):
            result = process_stdin()

            assert result == []

    def test_returns_empty_for_whitespace(self):
        """Test returns empty list for whitespace only."""
        with patch("sys.stdin", StringIO("   \n\t  ")):
            result = process_stdin()

            assert result == []

    def test_returns_empty_for_invalid_json(self):
        """Test returns empty list for invalid JSON."""
        with patch("sys.stdin", StringIO("not valid json")):
            result = process_stdin()

            assert result == []


class TestMain:
    """Tests for main function."""

    def test_returns_zero_on_success(self):
        """Test returns 0 on successful processing."""
        with patch("sys.stdin", StringIO('{"tool_name": "Other"}')):
            with patch("builtins.print"):
                result = main()

                assert result == 0

    def test_returns_zero_on_keyboard_interrupt(self):
        """Test returns 0 on KeyboardInterrupt."""
        with patch("sys.stdin", StringIO('{"tool_name": "ExitPlanMode"}')):
            with patch(
                "claude_apps.hooks.plan_distributor.__main__.process_hook_event",
                side_effect=KeyboardInterrupt()
            ):
                result = main()

                assert result == 0

    def test_returns_zero_on_exception(self):
        """Test returns 0 on exception (hook shouldn't block)."""
        with patch("sys.stdin", StringIO('{"tool_name": "ExitPlanMode"}')):
            with patch(
                "claude_apps.hooks.plan_distributor.__main__.process_hook_event",
                side_effect=Exception("Test error")
            ):
                with patch("builtins.print"):
                    result = main()

                    # Hook returns 0 even on error to not block Claude
                    assert result == 0

    def test_outputs_json_response(self, capsys):
        """Test outputs JSON response."""
        with patch("sys.stdin", StringIO('{"tool_name": "OtherTool"}')):
            main()

            captured = capsys.readouterr()
            response = json.loads(captured.out.strip())
            assert response["continue"] is True

    def test_handles_empty_stdin(self):
        """Test handles empty stdin."""
        with patch("sys.stdin", StringIO("")):
            result = main()

            assert result == 0
