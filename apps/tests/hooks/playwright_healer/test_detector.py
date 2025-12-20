"""Tests for playwright_healer hook error detector."""

from unittest.mock import patch

import pytest

from claude_apps.hooks.playwright_healer.detector import (
    categorize_error,
    detect_browser_error,
    extract_response_text,
    is_playwright_tool,
)


class TestIsPlaywrightTool:
    """Tests for is_playwright_tool function."""

    def test_returns_true_for_playwright_tool(self):
        """Test returns True for Playwright MCP tools."""
        assert is_playwright_tool("mcp__playwright__browser_click") is True
        assert is_playwright_tool("mcp__playwright__browser_navigate") is True
        assert is_playwright_tool("mcp__playwright__browser_snapshot") is True

    def test_returns_false_for_non_playwright(self):
        """Test returns False for non-Playwright tools."""
        assert is_playwright_tool("bash") is False
        assert is_playwright_tool("read") is False
        assert is_playwright_tool("mcp__other__tool") is False

    def test_returns_false_for_empty(self):
        """Test returns False for empty string."""
        assert is_playwright_tool("") is False


class TestExtractResponseText:
    """Tests for extract_response_text function."""

    def test_returns_string_as_is(self):
        """Test returns string input as is."""
        result = extract_response_text("error message")
        assert result == "error message"

    def test_extracts_text_from_dict(self):
        """Test extracts 'text' key from dict."""
        result = extract_response_text({"text": "error content"})
        assert result == "error content"

    def test_extracts_error_from_dict(self):
        """Test extracts 'error' key from dict."""
        result = extract_response_text({"error": "error message"})
        assert result == "error message"

    def test_combines_stdout_stderr(self):
        """Test combines stdout and stderr."""
        result = extract_response_text({"stdout": "out", "stderr": "err"})
        assert "out" in result
        assert "err" in result

    def test_extracts_from_list(self):
        """Test extracts text from list of items."""
        result = extract_response_text([
            {"type": "text", "text": "first"},
            {"type": "text", "text": "second"},
        ])
        assert "first" in result
        assert "second" in result

    def test_extracts_error_from_list(self):
        """Test extracts error from list items."""
        result = extract_response_text([
            {"error": "error message"},
        ])
        assert "error message" in result

    def test_handles_empty_dict(self):
        """Test handles empty dict."""
        result = extract_response_text({})
        assert result == "{}"

    def test_handles_none(self):
        """Test handles None."""
        result = extract_response_text(None)
        assert result == "None"


class TestCategorizeError:
    """Tests for categorize_error function."""

    def test_categorizes_browser_lock(self):
        """Test categorizes 'already in use' as browser_lock."""
        result = categorize_error("Browser is already in use")
        assert result == "browser_lock"

    def test_categorizes_browser_closed(self):
        """Test categorizes 'closed' as browser_closed."""
        result = categorize_error("browser context is closed")
        assert result == "browser_closed"

    def test_categorizes_connection_lost(self):
        """Test categorizes 'connection' as connection_lost."""
        result = categorize_error("Connection refused")
        assert result == "connection_lost"

    def test_categorizes_unknown(self):
        """Test categorizes unrecognized patterns as unknown."""
        result = categorize_error("Some other error")
        assert result == "unknown"

    def test_case_insensitive(self):
        """Test pattern matching is case insensitive."""
        result = categorize_error("ALREADY IN USE")
        assert result == "browser_lock"


class TestDetectBrowserError:
    """Tests for detect_browser_error function."""

    def test_detects_browser_lock_error(self):
        """Test detects browser lock error."""
        config = {"error_patterns": ["Browser is already in use"]}

        with patch(
            "claude_apps.hooks.playwright_healer.detector.get_config",
            return_value=config,
        ):
            result = detect_browser_error("Browser is already in use by another process")

            assert result["detected"] is True
            assert result["pattern"] == "Browser is already in use"
            assert result["error_type"] == "browser_lock"

    def test_detects_browser_closed_error(self):
        """Test detects browser closed error."""
        config = {"error_patterns": ["browser context is closed"]}

        with patch(
            "claude_apps.hooks.playwright_healer.detector.get_config",
            return_value=config,
        ):
            result = detect_browser_error("The browser context is closed")

            assert result["detected"] is True
            assert result["error_type"] == "browser_closed"

    def test_returns_not_detected_for_no_match(self):
        """Test returns not detected when no patterns match."""
        config = {"error_patterns": ["Browser is already in use"]}

        with patch(
            "claude_apps.hooks.playwright_healer.detector.get_config",
            return_value=config,
        ):
            result = detect_browser_error("Operation completed successfully")

            assert result["detected"] is False
            assert result["pattern"] is None
            assert result["error_type"] is None

    def test_case_insensitive_matching(self):
        """Test pattern matching is case insensitive."""
        config = {"error_patterns": ["browser is already in use"]}

        with patch(
            "claude_apps.hooks.playwright_healer.detector.get_config",
            return_value=config,
        ):
            result = detect_browser_error("BROWSER IS ALREADY IN USE")

            assert result["detected"] is True

    def test_truncates_long_messages(self):
        """Test truncates long error messages."""
        config = {"error_patterns": ["error"]}
        long_message = "error " + "x" * 1000

        with patch(
            "claude_apps.hooks.playwright_healer.detector.get_config",
            return_value=config,
        ):
            result = detect_browser_error(long_message)

            assert len(result["message"]) <= 500

    def test_handles_empty_patterns(self):
        """Test handles empty patterns list."""
        config = {"error_patterns": []}

        with patch(
            "claude_apps.hooks.playwright_healer.detector.get_config",
            return_value=config,
        ):
            result = detect_browser_error("Some error")

            assert result["detected"] is False

    def test_handles_list_response(self):
        """Test handles list-format tool response."""
        config = {"error_patterns": ["Browser is already in use"]}

        with patch(
            "claude_apps.hooks.playwright_healer.detector.get_config",
            return_value=config,
        ):
            result = detect_browser_error([
                {"type": "text", "text": "Browser is already in use"}
            ])

            assert result["detected"] is True
