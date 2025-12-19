"""Pydantic schemas for playwright_healer hook configuration."""

from pydantic import BaseModel, Field


class PlaywrightHealerConfig(BaseModel):
    """Configuration schema for playwright_healer hook.

    Validates config loaded from hooks.playwright_healer in config.yml.
    """

    log_base_path: str = Field(
        default=".data/logs/playwright_healer",
        description="Base path for log files",
    )
    log_enabled: bool = Field(
        default=True,
        description="Enable logging of hook events",
    )
    log_level: str = Field(
        default="INFO",
        description="Log level (DEBUG, INFO, WARNING, ERROR)",
    )
    max_recovery_attempts: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum browser recovery attempts before giving up",
    )
    recovery_cooldown_seconds: int = Field(
        default=5,
        ge=0,
        le=60,
        description="Cooldown between recovery attempts in seconds",
    )
    error_patterns: list[str] = Field(
        default=[
            "Browser is already in use",
            "browser context is closed",
            "Target page, context or browser has been closed",
        ],
        description="Patterns to detect browser errors in tool responses",
    )
    recoverable_tools: list[str] = Field(
        default=[],
        description="Tool names that support recovery (empty = all playwright tools)",
    )

    class Config:
        """Pydantic config."""

        extra = "ignore"  # Ignore unknown fields
