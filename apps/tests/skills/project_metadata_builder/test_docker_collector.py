"""Tests for Docker configuration collector."""

from pathlib import Path

import pytest

from claude_apps.skills.project_metadata_builder.collectors.docker_collector import (
    collect_docker_config,
    collect_runtime,
)


class TestCollectDockerConfig:
    """Tests for collect_docker_config function."""

    def test_returns_none_for_no_compose(self, tmp_path):
        """Test returns None when no compose file exists."""
        result = collect_docker_config(tmp_path)

        assert result is None

    def test_finds_docker_compose_yml(self, tmp_path):
        """Test finds docker-compose.yml."""
        compose = tmp_path / "docker-compose.yml"
        compose.write_text("version: '3'\nservices:\n  app:\n    image: python")

        result = collect_docker_config(tmp_path)

        assert result is not None
        assert result.compose_file == "docker-compose.yml"
        assert "app" in result.services

    def test_finds_docker_compose_yaml(self, tmp_path):
        """Test finds docker-compose.yaml."""
        compose = tmp_path / "docker-compose.yaml"
        compose.write_text("version: '3'\nservices:\n  web:\n    image: nginx")

        result = collect_docker_config(tmp_path)

        assert result is not None
        assert result.compose_file == "docker-compose.yaml"
        assert "web" in result.services

    def test_finds_compose_yml(self, tmp_path):
        """Test finds compose.yml (new style)."""
        compose = tmp_path / "compose.yml"
        compose.write_text("services:\n  api:\n    image: node")

        result = collect_docker_config(tmp_path)

        assert result is not None
        assert result.compose_file == "compose.yml"
        assert "api" in result.services

    def test_finds_compose_yaml(self, tmp_path):
        """Test finds compose.yaml (new style)."""
        compose = tmp_path / "compose.yaml"
        compose.write_text("services:\n  db:\n    image: postgres")

        result = collect_docker_config(tmp_path)

        assert result is not None
        assert result.compose_file == "compose.yaml"
        assert "db" in result.services

    def test_prefers_docker_compose_over_compose(self, tmp_path):
        """Test docker-compose.yml takes precedence over compose.yml."""
        (tmp_path / "docker-compose.yml").write_text("services:\n  app:\n    image: a")
        (tmp_path / "compose.yml").write_text("services:\n  other:\n    image: b")

        result = collect_docker_config(tmp_path)

        assert result.compose_file == "docker-compose.yml"
        assert "app" in result.services

    def test_finds_in_claude_directory(self, tmp_path):
        """Test finds compose file in .claude subdirectory."""
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        compose = claude_dir / "docker-compose.yml"
        compose.write_text("services:\n  claude:\n    image: claude")

        result = collect_docker_config(tmp_path)

        assert result is not None
        assert result.compose_file == ".claude/docker-compose.yml"
        assert "claude" in result.services

    def test_prefers_root_over_claude_dir(self, tmp_path):
        """Test root compose file takes precedence over .claude."""
        (tmp_path / "docker-compose.yml").write_text("services:\n  root:\n    image: a")

        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        (claude_dir / "docker-compose.yml").write_text("services:\n  claude:\n    image: b")

        result = collect_docker_config(tmp_path)

        assert result.compose_file == "docker-compose.yml"
        assert "root" in result.services

    def test_extracts_multiple_services(self, tmp_path):
        """Test extracting multiple services."""
        compose = tmp_path / "docker-compose.yml"
        compose.write_text("""
services:
  app:
    image: python
  db:
    image: postgres
  cache:
    image: redis
""")

        result = collect_docker_config(tmp_path)

        assert len(result.services) == 3
        assert "app" in result.services
        assert "db" in result.services
        assert "cache" in result.services

    def test_handles_malformed_yaml(self, tmp_path):
        """Test handles malformed YAML gracefully."""
        compose = tmp_path / "docker-compose.yml"
        compose.write_text("{ invalid yaml: [")

        result = collect_docker_config(tmp_path)

        # Should return config with file but empty services
        assert result is not None
        assert result.compose_file == "docker-compose.yml"
        assert result.services == []

    def test_handles_compose_without_services(self, tmp_path):
        """Test handles compose file without services key."""
        compose = tmp_path / "docker-compose.yml"
        compose.write_text("version: '3'\nnetworks:\n  default:\n")

        result = collect_docker_config(tmp_path)

        assert result is not None
        assert result.services == []


class TestCollectRuntime:
    """Tests for collect_runtime function."""

    def test_returns_runtime_with_docker(self, tmp_path):
        """Test returns runtime with docker config."""
        compose = tmp_path / "docker-compose.yml"
        compose.write_text("services:\n  app:\n    image: python")

        result = collect_runtime(tmp_path)

        assert result.docker is not None
        assert result.docker.compose_file == "docker-compose.yml"

    def test_returns_runtime_without_docker(self, tmp_path):
        """Test returns runtime without docker when no compose file."""
        result = collect_runtime(tmp_path)

        assert result.docker is None
        assert result.mcp_servers == []  # Empty by default
