"""Tests for session prompt builder."""

import pytest

from claude_apps.hooks.session_context_injector.prompt_builder import (
    build_agent_prompt,
)


class TestBuildAgentPrompt:
    """Tests for build_agent_prompt function."""

    def test_startup_prompt_contains_session_type(self):
        """Test startup prompt includes session type."""
        config = {"session_behavior": {"startup": "full"}}

        prompt = build_agent_prompt("startup", config)

        assert "Session Type:" in prompt
        assert "startup" in prompt.lower()

    def test_startup_prompt_contains_analysis_mode(self):
        """Test startup prompt includes analysis mode."""
        config = {"session_behavior": {"startup": "abbreviated"}}

        prompt = build_agent_prompt("startup", config)

        assert "abbreviated" in prompt

    def test_resume_prompt_focuses_on_changes(self):
        """Test resume prompt focuses on recent changes."""
        config = {"session_behavior": {"resume": "abbreviated"}}

        prompt = build_agent_prompt("resume", config)

        assert "resume" in prompt.lower()
        assert "recent" in prompt.lower() or "changed" in prompt.lower()

    def test_compact_prompt_mentions_compaction(self):
        """Test compact prompt mentions compaction."""
        config = {"session_behavior": {"compact": "abbreviated"}}

        prompt = build_agent_prompt("compact", config)

        assert "compact" in prompt.lower()

    def test_clear_prompt_mentions_fresh_start(self):
        """Test clear prompt mentions fresh start."""
        config = {"session_behavior": {"clear": "full"}}

        prompt = build_agent_prompt("clear", config)

        assert "clear" in prompt.lower()
        assert "fresh" in prompt.lower() or "full" in prompt.lower()

    def test_unknown_source_defaults_to_startup(self):
        """Test unknown source falls back to startup behavior."""
        config = {"session_behavior": {"startup": "full"}}

        prompt = build_agent_prompt("unknown_source", config)

        # Should use startup prompt behavior
        assert "full" in prompt

    def test_uses_default_behavior_when_not_in_config(self):
        """Test uses 'full' when source not in config."""
        config = {"session_behavior": {}}  # No behaviors defined

        prompt = build_agent_prompt("startup", config)

        # Default is 'full'
        assert "full" in prompt

    def test_empty_config(self):
        """Test handles empty config."""
        config = {}

        prompt = build_agent_prompt("startup", config)

        # Should still produce a prompt with default behavior
        assert "## Session Context Injection" in prompt

    def test_prompt_includes_agent_instruction(self):
        """Test prompt includes project-analysis agent instruction."""
        config = {"session_behavior": {"startup": "full"}}

        prompt = build_agent_prompt("startup", config)

        assert "project-analysis" in prompt
        assert "INSTRUCTION" in prompt

    def test_prompt_includes_skill_invocation(self):
        """Test prompt includes session-context skill reference."""
        config = {"session_behavior": {"startup": "full"}}

        prompt = build_agent_prompt("startup", config)

        assert "session-context" in prompt

    def test_all_source_types_produce_prompts(self):
        """Test all valid source types produce non-empty prompts."""
        config = {
            "session_behavior": {
                "startup": "full",
                "resume": "abbreviated",
                "clear": "full",
                "compact": "abbreviated",
            }
        }

        for source in ["startup", "resume", "clear", "compact"]:
            prompt = build_agent_prompt(source, config)
            assert len(prompt) > 50, f"Prompt for {source} is too short"
            assert "##" in prompt, f"Prompt for {source} missing header"
