"""Unit tests for formatter.py - JSON output formatting."""
import json
import sys
from pathlib import Path

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from formatter import format_to_hook_json


class TestFormatToHookJson:
    """Tests for format_to_hook_json function."""

    def test_returns_valid_json(self, sample_rules: list) -> None:
        """Verify output is valid JSON."""
        result = format_to_hook_json(sample_rules, "SessionStart")
        parsed = json.loads(result)
        assert isinstance(parsed, dict)

    def test_structure_has_hook_specific_output(self, sample_rules: list) -> None:
        """Verify required hookSpecificOutput key exists."""
        result = format_to_hook_json(sample_rules, "SessionStart")
        parsed = json.loads(result)

        assert "hookSpecificOutput" in parsed
        assert "hookEventName" in parsed["hookSpecificOutput"]
        assert "additionalContext" in parsed["hookSpecificOutput"]

    def test_event_name_in_output(self, sample_rules: list) -> None:
        """Verify event name is included in output."""
        result = format_to_hook_json(sample_rules, "UserPromptSubmit")
        parsed = json.loads(result)

        assert parsed["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"

    def test_combines_rule_contents(self, sample_rules: list) -> None:
        """Verify all rule contents are combined."""
        result = format_to_hook_json(sample_rules, "SessionStart")
        parsed = json.loads(result)

        context = parsed["hookSpecificOutput"]["additionalContext"]
        assert "First rule content" in context
        assert "Second rule content" in context
        assert "Third rule content" in context

    def test_double_newline_separator(self, sample_rules: list) -> None:
        """Verify rules are separated by double newlines."""
        result = format_to_hook_json(sample_rules, "SessionStart")
        parsed = json.loads(result)

        context = parsed["hookSpecificOutput"]["additionalContext"]
        # Content should be joined with \n\n
        assert "\n\n" in context

    def test_empty_rules_list(self) -> None:
        """Verify empty rules produce empty additionalContext."""
        result = format_to_hook_json([], "SessionStart")
        parsed = json.loads(result)

        assert parsed["hookSpecificOutput"]["additionalContext"] == ""

    def test_rules_with_empty_content_skipped(self) -> None:
        """Verify rules with empty content are skipped."""
        rules = [
            {"filename": "a.md", "name": "a", "content": "Valid content"},
            {"filename": "b.md", "name": "b", "content": ""},
            {"filename": "c.md", "name": "c", "content": "More content"},
        ]
        result = format_to_hook_json(rules, "SessionStart")
        parsed = json.loads(result)

        context = parsed["hookSpecificOutput"]["additionalContext"]
        assert "Valid content" in context
        assert "More content" in context

    def test_pretty_print_option(self, sample_rules: list) -> None:
        """Verify pretty=True adds indentation."""
        compact = format_to_hook_json(sample_rules, "SessionStart", pretty=False)
        pretty = format_to_hook_json(sample_rules, "SessionStart", pretty=True)

        assert len(pretty) > len(compact)
        assert "\n" in pretty
        assert "  " in pretty  # Indentation

    def test_preserves_unicode(self) -> None:
        """Verify Unicode characters are preserved (ensure_ascii=False)."""
        rules = [{"filename": "u.md", "name": "u", "content": "Check: \u2713"}]
        result = format_to_hook_json(rules, "SessionStart")

        assert "\u2713" in result
        assert "\\u2713" not in result  # Not escaped

    def test_default_event_name(self) -> None:
        """Verify default event name is UserPromptSubmit."""
        rules = [{"filename": "r.md", "name": "r", "content": "content"}]
        result = format_to_hook_json(rules)  # No event_name argument
        parsed = json.loads(result)

        assert parsed["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"

    def test_session_start_event_name(self) -> None:
        """Verify SessionStart event name is correctly set."""
        rules = [{"filename": "r.md", "name": "r", "content": "content"}]
        result = format_to_hook_json(rules, "SessionStart")
        parsed = json.loads(result)

        assert parsed["hookSpecificOutput"]["hookEventName"] == "SessionStart"
