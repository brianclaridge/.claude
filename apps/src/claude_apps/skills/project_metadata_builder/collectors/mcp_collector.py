"""
MCP server configuration collector.
"""
import json
from pathlib import Path

from loguru import logger


def collect_mcp_servers(project_path: Path) -> list[str]:
    """Collect MCP server names from project configuration."""
    servers: list[str] = []

    # Check for .mcp.json in project root
    mcp_json = project_path / ".mcp.json"
    servers.extend(_parse_mcp_json(mcp_json))

    # Check for .claude/.mcp.json
    claude_mcp = project_path / ".claude" / ".mcp.json"
    servers.extend(_parse_mcp_json(claude_mcp))

    # Check settings.json for mcpServers
    settings = project_path / ".claude" / "settings.json"
    servers.extend(_parse_settings_json(settings))

    # Also check config/templates/mcp.json
    template_mcp = project_path / ".claude" / "config" / "templates" / "mcp.json"
    servers.extend(_parse_mcp_json(template_mcp))

    # Deduplicate
    servers = list(dict.fromkeys(servers))

    if servers:
        logger.info(f"Found MCP servers: {servers}")

    return servers


def _parse_mcp_json(path: Path) -> list[str]:
    """Parse MCP server names from .mcp.json file."""
    servers: list[str] = []

    if not path.exists():
        return servers

    try:
        data = json.loads(path.read_text())

        # Handle mcpServers key (common format)
        if "mcpServers" in data:
            servers.extend(data["mcpServers"].keys())

        # Handle servers key (alternative format)
        if "servers" in data:
            servers.extend(data["servers"].keys())

    except Exception as e:
        logger.debug(f"Error parsing {path}: {e}")

    return servers


def _parse_settings_json(path: Path) -> list[str]:
    """Parse MCP server names from settings.json."""
    servers: list[str] = []

    if not path.exists():
        return servers

    try:
        data = json.loads(path.read_text())

        # Check for mcpServers in settings
        if "mcpServers" in data:
            servers.extend(data["mcpServers"].keys())

    except Exception as e:
        logger.debug(f"Error parsing {path}: {e}")

    return servers
