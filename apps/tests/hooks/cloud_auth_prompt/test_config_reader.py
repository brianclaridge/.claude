"""Tests for cloud auth prompt config reader."""

from unittest.mock import patch

import pytest

from claude_apps.hooks.cloud_auth_prompt.config_reader import (
    get_enabled_providers,
    load_cloud_providers,
)


class TestLoadCloudProviders:
    """Tests for load_cloud_providers function."""

    def test_returns_cloud_providers_section(self):
        """Test returns cloud_providers from config."""
        mock_config = {
            "cloud_providers": {
                "aws": {"enabled": True},
                "gcp": {"enabled": False},
            }
        }

        with patch(
            "claude_apps.hooks.cloud_auth_prompt.config_reader.get_global_config",
            return_value=mock_config,
        ):
            result = load_cloud_providers()

            assert "aws" in result
            assert "gcp" in result

    def test_returns_empty_dict_when_not_found(self):
        """Test returns empty dict when cloud_providers not in config."""
        mock_config = {"other_key": "value"}

        with patch(
            "claude_apps.hooks.cloud_auth_prompt.config_reader.get_global_config",
            return_value=mock_config,
        ):
            result = load_cloud_providers()

            assert result == {}

    def test_returns_empty_dict_when_config_empty(self):
        """Test returns empty dict when config is empty."""
        with patch(
            "claude_apps.hooks.cloud_auth_prompt.config_reader.get_global_config",
            return_value={},
        ):
            result = load_cloud_providers()

            assert result == {}


class TestGetEnabledProviders:
    """Tests for get_enabled_providers function."""

    def test_returns_enabled_providers(self):
        """Test returns only enabled providers with prompt_at_start."""
        mock_config = {
            "aws": {"enabled": True, "prompt_at_start": True},
            "gcp": {"enabled": False, "prompt_at_start": True},
            "azure": {"enabled": True, "prompt_at_start": False},
        }

        with patch(
            "claude_apps.hooks.cloud_auth_prompt.config_reader.load_cloud_providers",
            return_value=mock_config,
        ):
            result = get_enabled_providers()

            assert len(result) == 1
            assert result[0]["name"] == "aws"

    def test_returns_empty_when_none_enabled(self):
        """Test returns empty list when no providers enabled."""
        mock_config = {
            "aws": {"enabled": False, "prompt_at_start": True},
            "gcp": {"enabled": False, "prompt_at_start": True},
        }

        with patch(
            "claude_apps.hooks.cloud_auth_prompt.config_reader.load_cloud_providers",
            return_value=mock_config,
        ):
            result = get_enabled_providers()

            assert result == []

    def test_returns_empty_when_no_prompt_at_start(self):
        """Test returns empty when prompt_at_start is False."""
        mock_config = {
            "aws": {"enabled": True, "prompt_at_start": False},
        }

        with patch(
            "claude_apps.hooks.cloud_auth_prompt.config_reader.load_cloud_providers",
            return_value=mock_config,
        ):
            result = get_enabled_providers()

            assert result == []

    def test_adds_name_key(self):
        """Test adds name key from dict key."""
        mock_config = {
            "aws": {"enabled": True, "prompt_at_start": True},
        }

        with patch(
            "claude_apps.hooks.cloud_auth_prompt.config_reader.load_cloud_providers",
            return_value=mock_config,
        ):
            result = get_enabled_providers()

            assert result[0]["name"] == "aws"

    def test_uses_display_name_from_config(self):
        """Test uses display_name from config."""
        mock_config = {
            "aws": {
                "enabled": True,
                "prompt_at_start": True,
                "display_name": "Amazon Web Services",
            },
        }

        with patch(
            "claude_apps.hooks.cloud_auth_prompt.config_reader.load_cloud_providers",
            return_value=mock_config,
        ):
            result = get_enabled_providers()

            assert result[0]["display_name"] == "Amazon Web Services"

    def test_defaults_display_name_to_uppercase(self):
        """Test defaults display_name to uppercase name."""
        mock_config = {
            "aws": {"enabled": True, "prompt_at_start": True},
        }

        with patch(
            "claude_apps.hooks.cloud_auth_prompt.config_reader.load_cloud_providers",
            return_value=mock_config,
        ):
            result = get_enabled_providers()

            assert result[0]["display_name"] == "AWS"

    def test_uses_description_from_config(self):
        """Test uses description from config."""
        mock_config = {
            "aws": {
                "enabled": True,
                "prompt_at_start": True,
                "description": "Custom AWS description",
            },
        }

        with patch(
            "claude_apps.hooks.cloud_auth_prompt.config_reader.load_cloud_providers",
            return_value=mock_config,
        ):
            result = get_enabled_providers()

            assert result[0]["description"] == "Custom AWS description"

    def test_defaults_description(self):
        """Test defaults description."""
        mock_config = {
            "gcp": {"enabled": True, "prompt_at_start": True},
        }

        with patch(
            "claude_apps.hooks.cloud_auth_prompt.config_reader.load_cloud_providers",
            return_value=mock_config,
        ):
            result = get_enabled_providers()

            assert "GCP" in result[0]["description"]

    def test_returns_multiple_providers(self):
        """Test returns multiple enabled providers."""
        mock_config = {
            "aws": {"enabled": True, "prompt_at_start": True},
            "gcp": {"enabled": True, "prompt_at_start": True},
        }

        with patch(
            "claude_apps.hooks.cloud_auth_prompt.config_reader.load_cloud_providers",
            return_value=mock_config,
        ):
            result = get_enabled_providers()

            assert len(result) == 2
            names = [p["name"] for p in result]
            assert "aws" in names
            assert "gcp" in names
