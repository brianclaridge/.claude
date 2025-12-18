"""Shared test fixtures for claude-lib tests."""

import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_claude_env(temp_dir, monkeypatch):
    """Set up mock Claude environment variables."""
    config_path = temp_dir / "config.yml"
    config_path.write_text("hooks: {}")

    monkeypatch.setenv("CLAUDE_CONFIG_YML_PATH", str(config_path))
    monkeypatch.setenv("CLAUDE_DATA_PATH", str(temp_dir / ".data"))
    monkeypatch.setenv("CLAUDE_LOGS_PATH", str(temp_dir / ".data/logs"))

    yield {
        "config_path": config_path,
        "temp_dir": temp_dir,
    }


@pytest.fixture
def sample_config_yml(temp_dir):
    """Create a sample config.yml for testing."""
    config_content = """
hooks:
  logger:
    log_base_path: .data/logs/logger
    log_enabled: true
    log_level: DEBUG
  playwright_healer:
    log_enabled: true
    max_recovery_attempts: 5

cloud_providers:
  aws:
    enabled: true
    prompt_at_start: true
"""
    config_path = temp_dir / "config.yml"
    config_path.write_text(config_content)
    return config_path
