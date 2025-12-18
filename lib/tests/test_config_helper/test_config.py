"""Tests for config_helper.config module."""


import pytest

from config_helper import (
    get_claude_root,
    get_config_path,
    get_global_config,
    get_hook_config,
    get_workspace_root,
    resolve_log_path,
)


class TestGetConfigPath:
    """Tests for get_config_path function."""

    def test_returns_path_when_env_set(self, mock_claude_env):
        """Should return Path when CLAUDE_CONFIG_YML_PATH is set."""
        result = get_config_path()
        assert result == mock_claude_env["config_path"]

    def test_raises_when_env_not_set(self, monkeypatch):
        """Should raise EnvironmentError when env var not set."""
        monkeypatch.delenv("CLAUDE_CONFIG_YML_PATH", raising=False)
        with pytest.raises(EnvironmentError):
            get_config_path()


class TestGetClaudeRoot:
    """Tests for get_claude_root function."""

    def test_returns_parent_of_config(self, mock_claude_env):
        """Should return parent directory of config.yml."""
        result = get_claude_root()
        assert result == mock_claude_env["temp_dir"]


class TestGetWorkspaceRoot:
    """Tests for get_workspace_root function."""

    def test_returns_parent_of_claude_root(self, mock_claude_env):
        """Should return parent of .claude directory."""
        result = get_workspace_root()
        assert result == mock_claude_env["temp_dir"].parent


class TestGetGlobalConfig:
    """Tests for get_global_config function."""

    def test_returns_parsed_yaml(self, mock_claude_env, sample_config_yml, monkeypatch):
        """Should return parsed YAML content."""
        monkeypatch.setenv("CLAUDE_CONFIG_YML_PATH", str(sample_config_yml))
        result = get_global_config()
        assert "hooks" in result
        assert "cloud_providers" in result

    def test_returns_empty_dict_for_missing_file(self, mock_claude_env, monkeypatch):
        """Should return empty dict if file doesn't exist."""
        monkeypatch.setenv("CLAUDE_CONFIG_YML_PATH", "/nonexistent/config.yml")
        result = get_global_config()
        assert result == {}


class TestGetHookConfig:
    """Tests for get_hook_config function."""

    def test_returns_hook_config(self, mock_claude_env, sample_config_yml, monkeypatch):
        """Should return specific hook configuration."""
        monkeypatch.setenv("CLAUDE_CONFIG_YML_PATH", str(sample_config_yml))
        result = get_hook_config("logger")
        assert result["log_enabled"] is True
        assert result["log_level"] == "DEBUG"

    def test_returns_empty_dict_for_missing_hook(
        self, mock_claude_env, sample_config_yml, monkeypatch
    ):
        """Should return empty dict for non-existent hook."""
        monkeypatch.setenv("CLAUDE_CONFIG_YML_PATH", str(sample_config_yml))
        result = get_hook_config("nonexistent_hook")
        assert result == {}


class TestResolveLogPath:
    """Tests for resolve_log_path function."""

    def test_returns_configured_path(self, mock_claude_env, sample_config_yml, monkeypatch):
        """Should return configured log path."""
        monkeypatch.setenv("CLAUDE_CONFIG_YML_PATH", str(sample_config_yml))
        result = resolve_log_path("logger")
        assert str(result).endswith(".data/logs/logger")

    def test_returns_default_path(self, mock_claude_env):
        """Should return default path when not configured."""
        result = resolve_log_path("unconfigured_hook")
        assert "unconfigured_hook" in str(result)
