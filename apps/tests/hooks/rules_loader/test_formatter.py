"""Tests for rules loader output formatter."""

import json

import pytest

from claude_apps.hooks.rules_loader.formatter import format_to_hook_json


class TestFormatToHookJson:
    """Tests for format_to_hook_json function."""

    def test_combines_rule_contents(self):
        """Test combines multiple rule contents."""
        rules = [
            {"name": "rule-1", "content": "First rule content"},
            {"name": "rule-2", "content": "Second rule content"},
        ]

        output = format_to_hook_json(rules)
        parsed = json.loads(output)

        context = parsed["hookSpecificOutput"]["additionalContext"]
        assert "First rule content" in context
        assert "Second rule content" in context

    def test_separates_rules_with_newlines(self):
        """Test separates rules with double newline."""
        rules = [
            {"content": "Rule 1"},
            {"content": "Rule 2"},
        ]

        output = format_to_hook_json(rules)
        parsed = json.loads(output)

        context = parsed["hookSpecificOutput"]["additionalContext"]
        assert "Rule 1\n\nRule 2" == context

    def test_includes_event_name(self):
        """Test includes hook event name."""
        rules = [{"content": "Content"}]

        output = format_to_hook_json(rules, event_name="SessionStart")
        parsed = json.loads(output)

        assert parsed["hookSpecificOutput"]["hookEventName"] == "SessionStart"

    def test_default_event_name(self):
        """Test default event name is UserPromptSubmit."""
        rules = [{"content": "Content"}]

        output = format_to_hook_json(rules)
        parsed = json.loads(output)

        assert parsed["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"

    def test_pretty_format(self):
        """Test pretty format includes indentation."""
        rules = [{"content": "Content"}]

        output = format_to_hook_json(rules, pretty=True)

        # Pretty format should have newlines and indentation
        assert "\n" in output
        assert "  " in output

    def test_compact_format(self):
        """Test compact format has no extra whitespace."""
        rules = [{"content": "Content"}]

        output = format_to_hook_json(rules, pretty=False)

        # Compact format should be single line
        assert "\n" not in output

    def test_skips_empty_content(self):
        """Test skips rules with empty content."""
        rules = [
            {"name": "rule-1", "content": "Has content"},
            {"name": "rule-2", "content": ""},  # Empty
            {"name": "rule-3", "content": "Also has content"},
        ]

        output = format_to_hook_json(rules)
        parsed = json.loads(output)

        context = parsed["hookSpecificOutput"]["additionalContext"]
        assert "Has content" in context
        assert "Also has content" in context

    def test_skips_missing_content(self):
        """Test skips rules without content key."""
        rules = [
            {"name": "rule-1", "content": "Has content"},
            {"name": "rule-2"},  # No content key
        ]

        output = format_to_hook_json(rules)
        parsed = json.loads(output)

        context = parsed["hookSpecificOutput"]["additionalContext"]
        assert context == "Has content"

    def test_empty_rules_list(self):
        """Test handles empty rules list."""
        output = format_to_hook_json([])
        parsed = json.loads(output)

        assert parsed["hookSpecificOutput"]["additionalContext"] == ""

    def test_preserves_unicode(self):
        """Test preserves unicode characters."""
        rules = [{"content": "Unicode: 日本語 emoji: 🚀"}]

        output = format_to_hook_json(rules)
        parsed = json.loads(output)

        assert "日本語" in parsed["hookSpecificOutput"]["additionalContext"]
        assert "🚀" in parsed["hookSpecificOutput"]["additionalContext"]
