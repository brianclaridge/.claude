"""Tests for playwright_healer hook schemas."""

import pytest
from pydantic import ValidationError

from claude_apps.hooks.playwright_healer.schemas import PlaywrightHealerConfig


class TestPlaywrightHealerConfig:
    """Tests for PlaywrightHealerConfig schema."""

    def test_default_values(self):
        """Test default values are applied."""
        config = PlaywrightHealerConfig()

        assert config.log_enabled is True
        assert config.log_level == "INFO"
        assert config.max_recovery_attempts == 3
        assert config.recovery_cooldown_seconds == 5

    def test_default_error_patterns(self):
        """Test default error patterns."""
        config = PlaywrightHealerConfig()

        assert "Browser is already in use" in config.error_patterns
        assert "browser context is closed" in config.error_patterns

    def test_custom_values(self):
        """Test custom values override defaults."""
        config = PlaywrightHealerConfig(
            log_enabled=False,
            log_level="DEBUG",
            max_recovery_attempts=5,
        )

        assert config.log_enabled is False
        assert config.log_level == "DEBUG"
        assert config.max_recovery_attempts == 5

    def test_max_recovery_attempts_minimum(self):
        """Test max_recovery_attempts minimum validation."""
        with pytest.raises(ValidationError):
            PlaywrightHealerConfig(max_recovery_attempts=0)

    def test_max_recovery_attempts_maximum(self):
        """Test max_recovery_attempts maximum validation."""
        with pytest.raises(ValidationError):
            PlaywrightHealerConfig(max_recovery_attempts=11)

    def test_cooldown_minimum(self):
        """Test cooldown minimum is 0."""
        config = PlaywrightHealerConfig(recovery_cooldown_seconds=0)
        assert config.recovery_cooldown_seconds == 0

    def test_cooldown_maximum(self):
        """Test cooldown maximum validation."""
        with pytest.raises(ValidationError):
            PlaywrightHealerConfig(recovery_cooldown_seconds=61)

    def test_ignores_extra_fields(self):
        """Test ignores unknown fields."""
        config = PlaywrightHealerConfig(unknown_field="value")
        assert not hasattr(config, "unknown_field")

    def test_custom_error_patterns(self):
        """Test custom error patterns."""
        patterns = ["Custom error 1", "Custom error 2"]
        config = PlaywrightHealerConfig(error_patterns=patterns)

        assert config.error_patterns == patterns

    def test_empty_recoverable_tools_default(self):
        """Test empty recoverable_tools default."""
        config = PlaywrightHealerConfig()
        assert config.recoverable_tools == []

    def test_custom_recoverable_tools(self):
        """Test custom recoverable_tools."""
        tools = ["mcp__playwright__browser_click"]
        config = PlaywrightHealerConfig(recoverable_tools=tools)

        assert config.recoverable_tools == tools

    def test_model_dump(self):
        """Test model_dump returns dict."""
        config = PlaywrightHealerConfig()
        dumped = config.model_dump()

        assert isinstance(dumped, dict)
        assert "log_enabled" in dumped
        assert "max_recovery_attempts" in dumped
