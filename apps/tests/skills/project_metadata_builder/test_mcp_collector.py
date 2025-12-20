"""Tests for MCP server configuration collector."""

import json
from pathlib import Path

import pytest

from claude_apps.skills.project_metadata_builder.collectors.mcp_collector import (
    collect_mcp_servers,
)


class TestCollectMcpServers:
    """Tests for collect_mcp_servers function."""

    def test_returns_empty_for_no_config(self, tmp_path):
        """Test returns empty list when no MCP config exists."""
        result = collect_mcp_servers(tmp_path)

        assert result == []

    def test_parses_root_mcp_json(self, tmp_path):
        """Test parsing .mcp.json in project root."""
        mcp_json = tmp_path / ".mcp.json"
        mcp_json.write_text(json.dumps({
            "mcpServers": {
                "context7": {"command": "npx", "args": ["@context7/server"]},
                "playwright": {"command": "npx", "args": ["@playwright/mcp"]},
            }
        }))

        result = collect_mcp_servers(tmp_path)

        assert "context7" in result
        assert "playwright" in result

    def test_parses_claude_mcp_json(self, tmp_path):
        """Test parsing .claude/.mcp.json."""
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        mcp_json = claude_dir / ".mcp.json"
        mcp_json.write_text(json.dumps({
            "mcpServers": {
                "custom-server": {"command": "python", "args": ["server.py"]},
            }
        }))

        result = collect_mcp_servers(tmp_path)

        assert "custom-server" in result

    def test_parses_servers_key(self, tmp_path):
        """Test parsing 'servers' key as alternative format."""
        mcp_json = tmp_path / ".mcp.json"
        mcp_json.write_text(json.dumps({
            "servers": {
                "alt-server": {"command": "node", "args": ["index.js"]},
            }
        }))

        result = collect_mcp_servers(tmp_path)

        assert "alt-server" in result

    def test_parses_settings_json(self, tmp_path):
        """Test parsing mcpServers from settings.json."""
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        settings = claude_dir / "settings.json"
        settings.write_text(json.dumps({
            "mcpServers": {
                "settings-server": {"command": "bash", "args": ["run.sh"]},
            },
            "otherSetting": "value",
        }))

        result = collect_mcp_servers(tmp_path)

        assert "settings-server" in result

    def test_parses_config_templates_mcp(self, tmp_path):
        """Test parsing config/templates/mcp.json."""
        templates_dir = tmp_path / ".claude" / "config" / "templates"
        templates_dir.mkdir(parents=True)
        mcp_json = templates_dir / "mcp.json"
        mcp_json.write_text(json.dumps({
            "mcpServers": {
                "template-server": {"command": "go", "args": ["run", "."]},
            }
        }))

        result = collect_mcp_servers(tmp_path)

        assert "template-server" in result

    def test_combines_from_all_sources(self, tmp_path):
        """Test combining servers from all config locations."""
        # Root .mcp.json
        (tmp_path / ".mcp.json").write_text(json.dumps({
            "mcpServers": {"root-server": {}}
        }))

        # .claude/.mcp.json
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        (claude_dir / ".mcp.json").write_text(json.dumps({
            "mcpServers": {"claude-server": {}}
        }))

        # settings.json
        (claude_dir / "settings.json").write_text(json.dumps({
            "mcpServers": {"settings-server": {}}
        }))

        result = collect_mcp_servers(tmp_path)

        assert "root-server" in result
        assert "claude-server" in result
        assert "settings-server" in result

    def test_deduplicates_servers(self, tmp_path):
        """Test that duplicate server names are deduplicated."""
        # Same server in multiple files
        (tmp_path / ".mcp.json").write_text(json.dumps({
            "mcpServers": {"context7": {}}
        }))

        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        (claude_dir / ".mcp.json").write_text(json.dumps({
            "mcpServers": {"context7": {}}
        }))

        result = collect_mcp_servers(tmp_path)

        # Should only appear once
        assert result.count("context7") == 1

    def test_handles_malformed_json(self, tmp_path):
        """Test handles malformed JSON gracefully."""
        mcp_json = tmp_path / ".mcp.json"
        mcp_json.write_text("{ invalid json }")

        result = collect_mcp_servers(tmp_path)

        assert result == []

    def test_handles_missing_mcp_servers_key(self, tmp_path):
        """Test handles JSON without mcpServers key."""
        mcp_json = tmp_path / ".mcp.json"
        mcp_json.write_text(json.dumps({
            "someOtherKey": "value"
        }))

        result = collect_mcp_servers(tmp_path)

        assert result == []

    def test_handles_empty_mcp_servers(self, tmp_path):
        """Test handles empty mcpServers object."""
        mcp_json = tmp_path / ".mcp.json"
        mcp_json.write_text(json.dumps({
            "mcpServers": {}
        }))

        result = collect_mcp_servers(tmp_path)

        assert result == []
