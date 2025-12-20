"""Tests for plan parser utilities."""

import re
from datetime import datetime
from unittest.mock import patch

import pytest

from claude_apps.hooks.plan_distributor.parser import (
    _to_kebab_case,
    extract_plan_topic,
    generate_plan_filename,
)


class TestToKebabCase:
    """Tests for _to_kebab_case function."""

    def test_lowercase_conversion(self):
        """Test converts to lowercase."""
        assert _to_kebab_case("Hello World") == "hello-world"

    def test_space_to_hyphen(self):
        """Test converts spaces to hyphens."""
        assert _to_kebab_case("hello world") == "hello-world"

    def test_underscore_removed_as_markdown(self):
        """Test underscores are removed (treated as markdown formatting)."""
        # Underscores are removed by the markdown cleanup regex before conversion
        assert _to_kebab_case("hello_world") == "helloworld"

    def test_removes_markdown_formatting(self):
        """Test removes markdown characters."""
        assert _to_kebab_case("`code` and *bold*") == "code-and-bold"

    def test_removes_brackets(self):
        """Test removes square brackets and parens."""
        assert _to_kebab_case("[link](url)") == "linkurl"

    def test_removes_special_characters(self):
        """Test removes non-alphanumeric characters."""
        assert _to_kebab_case("hello@world!") == "helloworld"

    def test_collapses_multiple_hyphens(self):
        """Test collapses consecutive hyphens."""
        assert _to_kebab_case("hello   world") == "hello-world"
        assert _to_kebab_case("hello---world") == "hello-world"

    def test_trims_leading_trailing_hyphens(self):
        """Test removes leading/trailing hyphens."""
        assert _to_kebab_case("  hello  ") == "hello"
        assert _to_kebab_case("-hello-") == "hello"

    def test_limits_length(self):
        """Test limits to 50 characters."""
        long_text = "a" * 100
        result = _to_kebab_case(long_text)
        assert len(result) <= 50

    def test_empty_returns_untitled(self):
        """Test empty string returns untitled."""
        assert _to_kebab_case("") == "untitled"

    def test_special_chars_only_returns_untitled(self):
        """Test string with only special chars returns untitled."""
        assert _to_kebab_case("@#$%^") == "untitled"


class TestExtractPlanTopic:
    """Tests for extract_plan_topic function."""

    def test_extracts_plan_header(self):
        """Test extracts topic from Plan: header."""
        content = """# Plan: User Authentication

**Affects:** `/src/auth/`

## Summary
Add user login."""

        result = extract_plan_topic(content)
        assert result == "user-authentication"

    def test_extracts_h1_header(self):
        """Test extracts topic from any H1 header."""
        content = """# Add New Feature

This is the plan content."""

        result = extract_plan_topic(content)
        assert result == "add-new-feature"

    def test_fallback_to_first_line(self):
        """Test falls back to first line when no headers."""
        content = """This is a plan without headers.

More content here."""

        result = extract_plan_topic(content)
        assert result == "this-is-a-plan-without-headers"

    def test_empty_content_returns_untitled(self):
        """Test empty content returns untitled."""
        assert extract_plan_topic("") == "untitled"

    def test_prefers_plan_header_over_h1(self):
        """Test Plan: header takes precedence."""
        content = """# Random H1 Header

# Plan: The Real Topic

More content."""

        result = extract_plan_topic(content)
        # Actually Plan: pattern only matches if it's the H1
        # Based on regex, it checks Plan: first then any H1
        assert result == "the-real-topic"

    def test_handles_markdown_in_topic(self):
        """Test handles markdown formatting in topic."""
        content = "# Plan: `Code` *Implementation*"

        result = extract_plan_topic(content)
        assert result == "code-implementation"

    def test_limits_fallback_length(self):
        """Test limits first line fallback to 50 chars."""
        long_line = "a" * 100 + "\nSecond line"
        result = extract_plan_topic(long_line)
        assert len(result) <= 50


class TestGeneratePlanFilename:
    """Tests for generate_plan_filename function."""

    def test_format_includes_timestamp(self):
        """Test filename includes timestamp pattern."""
        content = "# Plan: Test Topic"

        result = generate_plan_filename(content)

        # Should start with YYYYMMDD_HHMMSS pattern
        import re
        assert re.match(r"^\d{8}_\d{6}_", result), f"'{result}' doesn't start with timestamp"

    def test_format_includes_topic(self):
        """Test filename includes topic."""
        content = "# Plan: User Authentication"

        result = generate_plan_filename(content)

        assert "user-authentication" in result

    def test_format_ends_with_md(self):
        """Test filename ends with .md extension."""
        content = "# Plan: Some Topic"

        result = generate_plan_filename(content)

        assert result.endswith(".md")

    def test_format_pattern(self):
        """Test filename matches expected pattern."""
        content = "# Plan: API Refactor"

        result = generate_plan_filename(content)

        # Pattern: YYYYMMDD_HHMMSS_<topic>.md
        pattern = r"^\d{8}_\d{6}_[\w-]+\.md$"
        assert re.match(pattern, result), f"'{result}' doesn't match pattern"

    def test_untitled_for_empty_content(self):
        """Test uses 'untitled' for empty content."""
        result = generate_plan_filename("")

        assert "untitled.md" in result
