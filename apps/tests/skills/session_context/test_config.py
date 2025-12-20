"""Tests for session_context configuration."""

from unittest.mock import patch

import pytest

from claude_apps.skills.session_context.config import (
    DEFAULT_CONFIG,
    _deep_merge,
    get_git_config,
    get_plans_config,
    get_session_behavior,
    load_config,
)


class TestLoadConfig:
    """Tests for load_config function."""

    def test_returns_defaults_when_env_not_set(self):
        """Test returns defaults when CLAUDE_CONFIG_YML_PATH not set."""
        with patch(
            "claude_apps.skills.session_context.config.get_hook_config"
        ) as mock_get:
            mock_get.side_effect = EnvironmentError("not set")

            result = load_config()

            assert result == DEFAULT_CONFIG["session_context"]

    def test_merges_with_defaults(self):
        """Test merges hook config with defaults."""
        with patch(
            "claude_apps.skills.session_context.config.get_hook_config"
        ) as mock_get:
            mock_get.return_value = {
                "auto_invoke_agent": False,
                "git": {"commit_history_limit": 10},
            }

            result = load_config()

            # Overridden values
            assert result["auto_invoke_agent"] is False
            assert result["git"]["commit_history_limit"] == 10
            # Default values preserved
            assert "session_behavior" in result
            assert result["plans"]["recent_limit"] == 3

    def test_handles_exception(self):
        """Test handles exception gracefully."""
        with patch(
            "claude_apps.skills.session_context.config.get_hook_config"
        ) as mock_get:
            mock_get.side_effect = Exception("unexpected error")

            result = load_config()

            assert result == DEFAULT_CONFIG["session_context"]


class TestGetSessionBehavior:
    """Tests for get_session_behavior function."""

    def test_returns_startup_behavior(self):
        """Test returns behavior for startup session."""
        config = {"session_behavior": {"startup": "full", "resume": "abbreviated"}}

        result = get_session_behavior(config, "startup")

        assert result == "full"

    def test_returns_resume_behavior(self):
        """Test returns behavior for resume session."""
        config = {"session_behavior": {"startup": "full", "resume": "abbreviated"}}

        result = get_session_behavior(config, "resume")

        assert result == "abbreviated"

    def test_returns_full_for_unknown_session(self):
        """Test returns 'full' for unknown session type."""
        config = {"session_behavior": {"startup": "full"}}

        result = get_session_behavior(config, "unknown")

        assert result == "full"

    def test_handles_missing_session_behavior(self):
        """Test handles missing session_behavior key."""
        config = {}

        result = get_session_behavior(config, "startup")

        assert result == "full"


class TestGetGitConfig:
    """Tests for get_git_config function."""

    def test_returns_git_config(self):
        """Test returns git configuration."""
        config = {"git": {"commit_history_limit": 10, "include_diff": True}}

        result = get_git_config(config)

        assert result["commit_history_limit"] == 10
        assert result["include_diff"] is True

    def test_returns_default_for_missing(self):
        """Test returns default for missing git key."""
        config = {}

        result = get_git_config(config)

        assert result["commit_history_limit"] == 5


class TestGetPlansConfig:
    """Tests for get_plans_config function."""

    def test_returns_plans_config(self):
        """Test returns plans configuration."""
        config = {"plans": {"recent_limit": 10, "include_content": True}}

        result = get_plans_config(config)

        assert result["recent_limit"] == 10
        assert result["include_content"] is True

    def test_returns_default_for_missing(self):
        """Test returns default for missing plans key."""
        config = {}

        result = get_plans_config(config)

        assert result["recent_limit"] == 3


class TestDeepMerge:
    """Tests for _deep_merge function."""

    def test_merges_flat_dicts(self):
        """Test merges flat dictionaries."""
        base = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}

        result = _deep_merge(base, override)

        assert result == {"a": 1, "b": 3, "c": 4}

    def test_merges_nested_dicts(self):
        """Test merges nested dictionaries."""
        base = {"a": {"x": 1, "y": 2}, "b": 3}
        override = {"a": {"y": 5, "z": 6}}

        result = _deep_merge(base, override)

        assert result["a"] == {"x": 1, "y": 5, "z": 6}
        assert result["b"] == 3

    def test_override_replaces_non_dict(self):
        """Test override replaces non-dict with dict."""
        base = {"a": 1}
        override = {"a": {"nested": True}}

        result = _deep_merge(base, override)

        assert result["a"] == {"nested": True}

    def test_base_unchanged(self):
        """Test original base dict is unchanged."""
        base = {"a": 1, "b": {"x": 2}}
        override = {"b": {"x": 3}}
        original_base = {"a": 1, "b": {"x": 2}}

        _deep_merge(base, override)

        assert base == original_base

    def test_empty_override(self):
        """Test empty override returns base copy."""
        base = {"a": 1, "b": 2}
        override = {}

        result = _deep_merge(base, override)

        assert result == {"a": 1, "b": 2}

    def test_empty_base(self):
        """Test empty base returns override values."""
        base = {}
        override = {"a": 1, "b": 2}

        result = _deep_merge(base, override)

        assert result == {"a": 1, "b": 2}

    def test_deeply_nested(self):
        """Test deeply nested merge."""
        base = {"a": {"b": {"c": {"d": 1}}}}
        override = {"a": {"b": {"c": {"e": 2}}}}

        result = _deep_merge(base, override)

        assert result["a"]["b"]["c"] == {"d": 1, "e": 2}


class TestDefaultConfig:
    """Tests for DEFAULT_CONFIG structure."""

    def test_has_session_context_key(self):
        """Test DEFAULT_CONFIG has session_context key."""
        assert "session_context" in DEFAULT_CONFIG

    def test_has_auto_invoke_agent(self):
        """Test has auto_invoke_agent setting."""
        assert DEFAULT_CONFIG["session_context"]["auto_invoke_agent"] is True

    def test_has_session_behaviors(self):
        """Test has session_behavior settings."""
        behaviors = DEFAULT_CONFIG["session_context"]["session_behavior"]
        assert behaviors["startup"] == "full"
        assert behaviors["resume"] == "abbreviated"
        assert behaviors["clear"] == "full"
        assert behaviors["compact"] == "abbreviated"

    def test_has_git_settings(self):
        """Test has git settings."""
        git = DEFAULT_CONFIG["session_context"]["git"]
        assert git["commit_history_limit"] == 5

    def test_has_plans_settings(self):
        """Test has plans settings."""
        plans = DEFAULT_CONFIG["session_context"]["plans"]
        assert plans["recent_limit"] == 3
