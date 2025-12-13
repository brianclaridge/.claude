"""Shared pytest fixtures for rules_loader tests."""
import json
import pytest
from pathlib import Path
from typing import Any


@pytest.fixture
def sample_rules_dir(tmp_path: Path) -> Path:
    """Create a temporary directory with sample rule files."""
    rules_dir = tmp_path / "rules"
    rules_dir.mkdir()

    rules = [
        ("000-first-rule.md", "# RULE: 000\n\n**CRITICAL** First rule content."),
        ("010-second-rule.md", "# RULE: 010\n\n**IMPORTANT** Second rule content."),
        ("020-third-rule.md", "# RULE: 020\n\nThird rule content with no emphasis."),
    ]

    for filename, content in rules:
        (rules_dir / filename).write_text(content, encoding="utf-8")

    return rules_dir


@pytest.fixture
def empty_rules_dir(tmp_path: Path) -> Path:
    """Create an empty rules directory."""
    rules_dir = tmp_path / "empty_rules"
    rules_dir.mkdir()
    return rules_dir


@pytest.fixture
def nonexistent_rules_dir(tmp_path: Path) -> Path:
    """Return a path to a directory that does not exist."""
    return tmp_path / "nonexistent"


@pytest.fixture
def sample_rules() -> list[dict[str, str]]:
    """Return sample rule dictionaries as would be returned by load_rules."""
    return [
        {
            "filename": "000-first-rule.md",
            "name": "000-first-rule",
            "content": "# RULE: 000\n\n**CRITICAL** First rule content.",
        },
        {
            "filename": "010-second-rule.md",
            "name": "010-second-rule",
            "content": "# RULE: 010\n\n**IMPORTANT** Second rule content.",
        },
        {
            "filename": "020-third-rule.md",
            "name": "020-third-rule",
            "content": "# RULE: 020\n\nThird rule content with no emphasis.",
        },
    ]


@pytest.fixture
def config_reinforce_all() -> dict[str, Any]:
    """Config with global reinforcement enabled."""
    return {
        "rules_loader": {
            "reinforcement_enabled": True,
            "rules_path": "rules/",
            "rules": {},
        }
    }


@pytest.fixture
def config_reinforce_none() -> dict[str, Any]:
    """Config with global reinforcement disabled and no per-rule overrides."""
    return {
        "rules_loader": {
            "reinforcement_enabled": False,
            "rules_path": "rules/",
            "rules": {},
        }
    }


@pytest.fixture
def config_reinforce_selective() -> dict[str, Any]:
    """Config with selective per-rule reinforcement."""
    return {
        "rules_loader": {
            "reinforcement_enabled": False,
            "rules_path": "rules/",
            "rules": {
                "000-first-rule": {"reinforce": True},
                "020-third-rule": {"reinforce": True},
                # 010-second-rule not listed, inherits global (False)
            },
        }
    }


@pytest.fixture
def session_start_event() -> dict[str, Any]:
    """Sample SessionStart hook event."""
    return {
        "hook_event_name": "SessionStart",
        "session_id": "test-session-001",
        "cwd": "/workspace/test",
    }


@pytest.fixture
def user_prompt_event() -> dict[str, Any]:
    """Sample UserPromptSubmit hook event."""
    return {
        "hook_event_name": "UserPromptSubmit",
        "session_id": "test-session-001",
        "prompt": "Test prompt content",
    }


@pytest.fixture
def mock_hook_config(tmp_path: Path) -> dict[str, Any]:
    """Create mock hook config."""
    return {
        "log_base_path": str(tmp_path / "logs"),
        "rules_path": str(tmp_path / "rules"),
        "log_enabled": False,
        "log_level": "INFO",
    }
