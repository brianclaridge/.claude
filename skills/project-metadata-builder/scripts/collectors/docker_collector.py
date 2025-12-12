"""
Docker configuration collector.
"""
from pathlib import Path

import yaml
from loguru import logger

from ..schema import DockerConfig, Runtime


def collect_docker_config(project_path: Path) -> DockerConfig | None:
    """Collect Docker configuration from a project."""
    docker_config = DockerConfig()

    # Look for docker-compose files
    compose_files = [
        "docker-compose.yml",
        "docker-compose.yaml",
        "compose.yml",
        "compose.yaml",
    ]

    compose_path = None
    for filename in compose_files:
        path = project_path / filename
        if path.exists():
            compose_path = path
            docker_config.compose_file = filename
            break

    # Also check .claude subdirectory
    if not compose_path:
        claude_dir = project_path / ".claude"
        for filename in compose_files:
            path = claude_dir / filename
            if path.exists():
                compose_path = path
                docker_config.compose_file = f".claude/{filename}"
                break

    if not compose_path:
        return None

    # Parse compose file for services
    try:
        with open(compose_path) as f:
            data = yaml.safe_load(f)

        if data and "services" in data:
            docker_config.services = list(data["services"].keys())

        logger.info(
            f"Found Docker compose: {docker_config.compose_file}, "
            f"services={docker_config.services}"
        )

    except Exception as e:
        logger.debug(f"Error parsing {compose_path}: {e}")

    return docker_config


def collect_runtime(project_path: Path) -> Runtime:
    """Collect runtime configuration including Docker and MCP."""
    runtime = Runtime()

    # Collect Docker config
    runtime.docker = collect_docker_config(project_path)

    # MCP servers collected separately
    return runtime
