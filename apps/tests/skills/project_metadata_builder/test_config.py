"""Tests for project metadata builder configuration."""

from pathlib import Path

import pytest

from claude_apps.skills.project_metadata_builder.config import (
    Config,
    ProjectMetadataConfig,
    get_projects_file_path,
    load_config,
)


class TestProjectMetadataConfig:
    """Tests for ProjectMetadataConfig dataclass."""

    def test_defaults(self):
        """Test default values."""
        config = ProjectMetadataConfig()

        assert config.session_history_limit == 10
        assert config.auto_update_on_session is True
        assert config.periodic_refresh_hours == 24
        assert config.stale_project_days == 30
        assert config.activity_threshold_commits == 5
        assert config.projects_file == "${CLAUDE_PROJECTS_YML_PATH}"
        assert config.log_level == "INFO"

    def test_custom_values(self):
        """Test with custom values."""
        config = ProjectMetadataConfig(
            session_history_limit=20,
            auto_update_on_session=False,
            periodic_refresh_hours=48,
            stale_project_days=60,
            activity_threshold_commits=10,
            projects_file="/custom/path.yml",
            log_level="DEBUG",
        )

        assert config.session_history_limit == 20
        assert config.auto_update_on_session is False
        assert config.periodic_refresh_hours == 48
        assert config.stale_project_days == 60
        assert config.activity_threshold_commits == 10
        assert config.projects_file == "/custom/path.yml"
        assert config.log_level == "DEBUG"


class TestConfig:
    """Tests for Config dataclass."""

    def test_defaults(self):
        """Test default values."""
        config = Config()

        assert isinstance(config.project_metadata, ProjectMetadataConfig)


class TestLoadConfig:
    """Tests for load_config function."""

    def test_returns_default_on_error(self, monkeypatch):
        """Test returns default config on error."""
        # Mock the config helper to raise an error
        def mock_get_global_config():
            raise EnvironmentError("Config not found")

        import claude_apps.skills.project_metadata_builder.config as config_module
        monkeypatch.setattr(
            config_module,
            "get_global_config",
            mock_get_global_config,
        )

        config = load_config()

        assert isinstance(config, Config)
        assert config.project_metadata.session_history_limit == 10

    def test_loads_custom_values(self, monkeypatch):
        """Test loading custom values from config."""
        def mock_get_global_config():
            return {
                "project_metadata": {
                    "session_history_limit": 25,
                    "auto_update_on_session": False,
                    "stale_project_days": 45,
                    "log_level": "DEBUG",
                }
            }

        import claude_apps.skills.project_metadata_builder.config as config_module
        monkeypatch.setattr(
            config_module,
            "get_global_config",
            mock_get_global_config,
        )

        config = load_config()

        assert config.project_metadata.session_history_limit == 25
        assert config.project_metadata.auto_update_on_session is False
        assert config.project_metadata.stale_project_days == 45
        assert config.project_metadata.log_level == "DEBUG"

    def test_handles_empty_config(self, monkeypatch):
        """Test handles empty config section."""
        def mock_get_global_config():
            return {}

        import claude_apps.skills.project_metadata_builder.config as config_module
        monkeypatch.setattr(
            config_module,
            "get_global_config",
            mock_get_global_config,
        )

        config = load_config()

        # Should use defaults
        assert config.project_metadata.session_history_limit == 10


class TestGetProjectsFilePath:
    """Tests for get_projects_file_path function."""

    def test_expands_env_var(self, monkeypatch):
        """Test environment variable expansion."""
        monkeypatch.setenv("CLAUDE_PROJECTS_YML_PATH", "/home/user/projects.yml")

        config = Config(
            project_metadata=ProjectMetadataConfig(
                projects_file="${CLAUDE_PROJECTS_YML_PATH}"
            )
        )

        path = get_projects_file_path(config)

        assert path == Path("/home/user/projects.yml")

    def test_expands_tilde(self, monkeypatch):
        """Test tilde expansion."""
        monkeypatch.setenv("HOME", "/home/testuser")

        config = Config(
            project_metadata=ProjectMetadataConfig(
                projects_file="~/projects.yml"
            )
        )

        path = get_projects_file_path(config)

        assert path == Path("/home/testuser/projects.yml")

    def test_absolute_path(self):
        """Test absolute path unchanged."""
        config = Config(
            project_metadata=ProjectMetadataConfig(
                projects_file="/absolute/path/projects.yml"
            )
        )

        path = get_projects_file_path(config)

        assert path == Path("/absolute/path/projects.yml")
