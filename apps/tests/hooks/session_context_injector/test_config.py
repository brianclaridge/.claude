"""Tests for session_context_injector config loading."""

from unittest.mock import patch

import pytest

from claude_apps.hooks.session_context_injector.config import load_session_config


class TestLoadSessionConfig:
    """Tests for load_session_config function."""

    def test_returns_validated_config(self):
        """Test returns validated config dict."""
        mock_config = {
            "auto_invoke_agent": True,
            "session_behavior": {"startup": "full"},
        }

        with patch(
            "claude_apps.hooks.session_context_injector.config.get_hook_config"
        ) as mock_get:
            mock_get.return_value = mock_config

            result = load_session_config()

            assert isinstance(result, dict)
            assert result["auto_invoke_agent"] is True

    def test_applies_defaults(self):
        """Test applies schema defaults."""
        with patch(
            "claude_apps.hooks.session_context_injector.config.get_hook_config"
        ) as mock_get:
            mock_get.return_value = {}

            result = load_session_config()

            # Schema defaults should be applied
            assert result["auto_invoke_agent"] is True
            assert result["session_behavior"]["startup"] == "full"
            assert result["git"]["commit_history_limit"] == 5
            assert result["plans"]["recent_limit"] == 3

    def test_handles_partial_config(self):
        """Test handles partial configuration."""
        mock_config = {
            "auto_invoke_agent": False,
            # Other fields use defaults
        }

        with patch(
            "claude_apps.hooks.session_context_injector.config.get_hook_config"
        ) as mock_get:
            mock_get.return_value = mock_config

            result = load_session_config()

            assert result["auto_invoke_agent"] is False
            # Defaults for missing fields
            assert result["session_behavior"]["startup"] == "full"

    def test_ignores_extra_fields(self):
        """Test ignores extra unknown fields."""
        mock_config = {
            "auto_invoke_agent": True,
            "unknown_field": "should be ignored",
        }

        with patch(
            "claude_apps.hooks.session_context_injector.config.get_hook_config"
        ) as mock_get:
            mock_get.return_value = mock_config

            result = load_session_config()

            assert "unknown_field" not in result
