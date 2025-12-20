"""
Metadata collectors for project-metadata-builder.
"""
from .deps_collector import collect_dependencies
from .docker_collector import collect_docker_config, collect_runtime
from .git_collector import collect_git_metadata
from .lang_collector import collect_languages
from .mcp_collector import collect_mcp_servers

__all__ = [
    "collect_git_metadata",
    "collect_languages",
    "collect_dependencies",
    "collect_docker_config",
    "collect_runtime",
    "collect_mcp_servers",
]
