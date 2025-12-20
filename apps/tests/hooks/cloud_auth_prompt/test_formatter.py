"""Tests for cloud auth prompt formatter."""

import json

import pytest

from claude_apps.hooks.cloud_auth_prompt.formatter import format_hook_output


class TestFormatHookOutput:
    """Tests for format_hook_output function."""

    def test_returns_valid_json(self):
        """Test returns valid JSON string."""
        providers = [{"name": "aws", "display_name": "AWS", "description": "Login to AWS"}]

        result = format_hook_output(providers)

        # Should be valid JSON
        parsed = json.loads(result)
        assert "hookSpecificOutput" in parsed

    def test_includes_hook_event_name(self):
        """Test includes hook event name."""
        providers = [{"name": "aws", "display_name": "AWS", "description": "Login"}]

        result = format_hook_output(providers, event_name="SessionStart")
        parsed = json.loads(result)

        assert parsed["hookSpecificOutput"]["hookEventName"] == "SessionStart"

    def test_default_event_name(self):
        """Test default event name is SessionStart."""
        providers = [{"name": "aws", "display_name": "AWS", "description": "Login"}]

        result = format_hook_output(providers)
        parsed = json.loads(result)

        assert parsed["hookSpecificOutput"]["hookEventName"] == "SessionStart"

    def test_empty_context_for_no_providers(self):
        """Test returns empty context when no providers."""
        result = format_hook_output([])
        parsed = json.loads(result)

        assert parsed["hookSpecificOutput"]["additionalContext"] == ""

    def test_includes_aws_command(self):
        """Test includes AWS slash command."""
        providers = [{"name": "aws", "display_name": "AWS", "description": "Login"}]

        result = format_hook_output(providers)
        parsed = json.loads(result)

        context = parsed["hookSpecificOutput"]["additionalContext"]
        assert "/auth-aws" in context

    def test_includes_gcp_command(self):
        """Test includes GCP slash command."""
        providers = [{"name": "gcp", "display_name": "GCP", "description": "Login"}]

        result = format_hook_output(providers)
        parsed = json.loads(result)

        context = parsed["hookSpecificOutput"]["additionalContext"]
        assert "/auth-gcp" in context

    def test_includes_both_commands(self):
        """Test includes both AWS and GCP commands."""
        providers = [
            {"name": "aws", "display_name": "AWS", "description": "Login"},
            {"name": "gcp", "display_name": "GCP", "description": "Login"},
        ]

        result = format_hook_output(providers)
        parsed = json.loads(result)

        context = parsed["hookSpecificOutput"]["additionalContext"]
        assert "/auth-aws" in context
        assert "/auth-gcp" in context

    def test_does_not_include_unknown_provider(self):
        """Test does not include commands for unknown providers."""
        providers = [{"name": "azure", "display_name": "Azure", "description": "Login"}]

        result = format_hook_output(providers)
        parsed = json.loads(result)

        context = parsed["hookSpecificOutput"]["additionalContext"]
        # Azure is not in the list of supported commands
        assert "/auth-azure" not in context

    def test_context_includes_header(self):
        """Test context includes informative header."""
        providers = [{"name": "aws", "display_name": "AWS", "description": "Login"}]

        result = format_hook_output(providers)
        parsed = json.loads(result)

        context = parsed["hookSpecificOutput"]["additionalContext"]
        assert "Cloud authentication" in context

    def test_custom_event_name(self):
        """Test custom event name is used."""
        providers = [{"name": "aws", "display_name": "AWS", "description": "Login"}]

        result = format_hook_output(providers, event_name="CustomEvent")
        parsed = json.loads(result)

        assert parsed["hookSpecificOutput"]["hookEventName"] == "CustomEvent"

    def test_commands_are_bulleted(self):
        """Test commands are in bullet list format."""
        providers = [{"name": "aws", "display_name": "AWS", "description": "Login"}]

        result = format_hook_output(providers)
        parsed = json.loads(result)

        context = parsed["hookSpecificOutput"]["additionalContext"]
        assert "- " in context
