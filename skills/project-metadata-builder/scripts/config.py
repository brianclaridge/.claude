"""
Configuration loading and defaults for project-metadata-builder.
"""
import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from loguru import logger


@dataclass
class ProjectMetadataConfig:
    """Configuration for project metadata builder."""

    session_history_limit: int = 10
    auto_update_on_session: bool = True
    periodic_refresh_hours: int = 24
    stale_project_days: int = 30
    activity_threshold_commits: int = 5
    projects_file: str = "~/.claude/projects.yml"
    log_level: str = "INFO"


@dataclass
class Config:
    """Global configuration."""

    project_metadata: ProjectMetadataConfig = field(default_factory=ProjectMetadataConfig)


def get_config_path() -> Path:
    """Get the config file path from .claude project root."""
    return Path("/workspace/.claude/config.yml")


def load_config() -> Config:
    """Load configuration from /workspace/.claude/config.yml."""
    config_path = get_config_path()

    if not config_path.exists():
        logger.warning(f"Config file not found at {config_path}, using defaults")
        return Config()

    try:
        with open(config_path) as f:
            data = yaml.safe_load(f) or {}

        pm_data = data.get("project_metadata", {})
        pm_config = ProjectMetadataConfig(
            session_history_limit=pm_data.get("session_history_limit", 10),
            auto_update_on_session=pm_data.get("auto_update_on_session", True),
            periodic_refresh_hours=pm_data.get("periodic_refresh_hours", 24),
            stale_project_days=pm_data.get("stale_project_days", 30),
            activity_threshold_commits=pm_data.get("activity_threshold_commits", 5),
            projects_file=pm_data.get("projects_file", "~/.claude/projects.yml"),
            log_level=pm_data.get("log_level", "INFO"),
        )

        logger.info(f"Loaded config from {config_path}")
        return Config(project_metadata=pm_config)

    except Exception as e:
        logger.error(f"Error loading config: {e}, using defaults")
        return Config()


def get_projects_file_path(config: Config) -> Path:
    """Get the projects.yml file path from config."""
    return Path(os.path.expanduser(config.project_metadata.projects_file))
