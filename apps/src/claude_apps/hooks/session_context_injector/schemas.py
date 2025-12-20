"""Pydantic schemas for session_context_injector hook configuration."""

from typing import Literal

from pydantic import BaseModel, Field


class SessionBehavior(BaseModel):
    """Session behavior settings per source type."""

    startup: Literal["full", "abbreviated", "none"] = Field(
        default="full",
        description="Analysis mode for fresh session starts",
    )
    resume: Literal["full", "abbreviated", "none"] = Field(
        default="abbreviated",
        description="Analysis mode for session resumes",
    )
    clear: Literal["full", "abbreviated", "none"] = Field(
        default="full",
        description="Analysis mode after /clear command",
    )
    compact: Literal["full", "abbreviated", "none"] = Field(
        default="abbreviated",
        description="Analysis mode after context compaction",
    )


class GitConfig(BaseModel):
    """Git-related configuration."""

    commit_history_limit: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Number of recent commits to include in context",
    )


class PlansConfig(BaseModel):
    """Plans-related configuration."""

    recent_limit: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Number of recent plans to include in context",
    )


class SessionContextConfig(BaseModel):
    """Configuration schema for session_context_injector hook.

    Validates config loaded from hooks.session_context in config.yml.
    """

    auto_invoke_agent: bool = Field(
        default=True,
        description="Automatically invoke project-analysis agent on session start",
    )
    session_behavior: SessionBehavior = Field(
        default_factory=SessionBehavior,
        description="Per-source session behavior settings",
    )
    git: GitConfig = Field(
        default_factory=GitConfig,
        description="Git context configuration",
    )
    plans: PlansConfig = Field(
        default_factory=PlansConfig,
        description="Plans context configuration",
    )

    class Config:
        """Pydantic config."""

        extra = "ignore"  # Ignore unknown fields
