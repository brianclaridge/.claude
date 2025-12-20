"""Pydantic schemas for rules_loader hook configuration."""

from pydantic import BaseModel, Field


class RuleSettings(BaseModel):
    """Per-rule configuration settings."""

    reinforce: bool = Field(
        default=False,
        description="Whether to include this rule in UserPromptSubmit events",
    )


class RulesLoaderConfig(BaseModel):
    """Configuration schema for rules_loader hook.

    Validates config loaded from hooks.rules_loader in config.yml.
    """

    log_base_path: str = Field(
        default=".data/logs/rules_loader",
        description="Base path for log files",
    )
    rules_path: str = Field(
        default="rules/",
        description="Path to rules directory relative to CLAUDE_PATH",
    )
    log_enabled: bool = Field(
        default=True,
        description="Enable logging of hook events",
    )
    log_level: str = Field(
        default="INFO",
        description="Log level (DEBUG, INFO, WARNING, ERROR)",
    )
    reinforcement_enabled: bool = Field(
        default=False,
        description="Global toggle for rule reinforcement on UserPromptSubmit",
    )
    rules: dict[str, RuleSettings] = Field(
        default={},
        description="Per-rule settings keyed by rule name (e.g., '000-rule-follower')",
    )

    class Config:
        """Pydantic config."""

        extra = "ignore"  # Ignore unknown fields
