"""
Configuration loading and defaults for project-metadata-builder.
"""
import os
from dataclasses import dataclass, field
from pathlib import Path

import structlog

from claude_apps.shared.config_helper import get_global_config

logger = structlog.get_logger()


@dataclass
class ProjectMetadataConfig:
    """Configuration for project metadata builder."""

    session_history_limit: int = 10
    auto_update_on_session: bool = True
    periodic_refresh_hours: int = 24
    stale_project_days: int = 30
    activity_threshold_commits: int = 5
    projects_file: str = "${CLAUDE_PROJECTS_YML_PATH}"
    log_level: str = "INFO"


@dataclass
class Config:
    """Global configuration."""

    project_metadata: ProjectMetadataConfig = field(default_factory=ProjectMetadataConfig)


def load_config() -> Config:
    """Load configuration from config.yml via shared module."""
    try:
        global_config = get_global_config()
        pm_data = global_config.get("project_metadata", {})

        pm_config = ProjectMetadataConfig(
            session_history_limit=pm_data.get("session_history_limit", 10),
            auto_update_on_session=pm_data.get("auto_update_on_session", True),
            periodic_refresh_hours=pm_data.get("periodic_refresh_hours", 24),
            stale_project_days=pm_data.get("stale_project_days", 30),
            activity_threshold_commits=pm_data.get("activity_threshold_commits", 5),
            projects_file=pm_data.get("projects_file", "${CLAUDE_PROJECTS_YML_PATH}"),
            log_level=pm_data.get("log_level", "INFO"),
        )

        logger.info("Loaded config via shared module")
        return Config(project_metadata=pm_config)

    except EnvironmentError as e:
        logger.error(f"Config error: {e}, using defaults")
        return Config()

    except Exception as e:
        logger.error(f"Error loading config: {e}, using defaults")
        return Config()


def get_projects_file_path(config: Config) -> Path:
    """Get the projects.yml file path from config."""
    # expandvars first to handle ${CLAUDE_PROJECTS_YML_PATH}, then expanduser for ~
    return Path(os.path.expanduser(os.path.expandvars(config.project_metadata.projects_file)))
