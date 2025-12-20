"""Tests for session_context_injector schemas."""

import pytest
from pydantic import ValidationError

from claude_apps.hooks.session_context_injector.schemas import (
    GitConfig,
    PlansConfig,
    SessionBehavior,
    SessionContextConfig,
)


class TestSessionBehavior:
    """Tests for SessionBehavior schema."""

    def test_default_values(self):
        """Test default values."""
        behavior = SessionBehavior()

        assert behavior.startup == "full"
        assert behavior.resume == "abbreviated"
        assert behavior.clear == "full"
        assert behavior.compact == "abbreviated"

    def test_custom_values(self):
        """Test custom values."""
        behavior = SessionBehavior(
            startup="abbreviated",
            resume="none",
            clear="none",
            compact="full",
        )

        assert behavior.startup == "abbreviated"
        assert behavior.resume == "none"
        assert behavior.clear == "none"
        assert behavior.compact == "full"

    def test_invalid_value_raises(self):
        """Test invalid value raises ValidationError."""
        with pytest.raises(ValidationError):
            SessionBehavior(startup="invalid")


class TestGitConfig:
    """Tests for GitConfig schema."""

    def test_default_commit_limit(self):
        """Test default commit history limit."""
        config = GitConfig()

        assert config.commit_history_limit == 5

    def test_custom_commit_limit(self):
        """Test custom commit history limit."""
        config = GitConfig(commit_history_limit=10)

        assert config.commit_history_limit == 10

    def test_minimum_limit(self):
        """Test minimum limit enforcement."""
        with pytest.raises(ValidationError):
            GitConfig(commit_history_limit=0)

    def test_maximum_limit(self):
        """Test maximum limit enforcement."""
        with pytest.raises(ValidationError):
            GitConfig(commit_history_limit=100)


class TestPlansConfig:
    """Tests for PlansConfig schema."""

    def test_default_recent_limit(self):
        """Test default recent plans limit."""
        config = PlansConfig()

        assert config.recent_limit == 3

    def test_custom_recent_limit(self):
        """Test custom recent limit."""
        config = PlansConfig(recent_limit=5)

        assert config.recent_limit == 5

    def test_minimum_limit(self):
        """Test minimum limit enforcement."""
        with pytest.raises(ValidationError):
            PlansConfig(recent_limit=0)

    def test_maximum_limit(self):
        """Test maximum limit enforcement."""
        with pytest.raises(ValidationError):
            PlansConfig(recent_limit=20)


class TestSessionContextConfig:
    """Tests for SessionContextConfig schema."""

    def test_default_values(self):
        """Test all defaults."""
        config = SessionContextConfig()

        assert config.auto_invoke_agent is True
        assert config.session_behavior.startup == "full"
        assert config.git.commit_history_limit == 5
        assert config.plans.recent_limit == 3

    def test_custom_values(self):
        """Test custom configuration."""
        config = SessionContextConfig(
            auto_invoke_agent=False,
            session_behavior={"startup": "none", "resume": "full"},
            git={"commit_history_limit": 10},
            plans={"recent_limit": 5},
        )

        assert config.auto_invoke_agent is False
        assert config.session_behavior.startup == "none"
        assert config.session_behavior.resume == "full"
        assert config.git.commit_history_limit == 10
        assert config.plans.recent_limit == 5

    def test_ignores_unknown_fields(self):
        """Test ignores unknown fields per Config.extra = 'ignore'."""
        config = SessionContextConfig(
            unknown_field="should be ignored",
            auto_invoke_agent=True,
        )

        assert config.auto_invoke_agent is True
        assert not hasattr(config, "unknown_field")

    def test_model_dump(self):
        """Test model_dump returns dict."""
        config = SessionContextConfig()
        dumped = config.model_dump()

        assert isinstance(dumped, dict)
        assert "auto_invoke_agent" in dumped
        assert "session_behavior" in dumped
        assert "git" in dumped
        assert "plans" in dumped
