"""Shared pytest fixtures for all Claude Code hooks.

Import this conftest in individual hook test directories:

    # hooks/logger/tests/conftest.py
    from hooks.tests.conftest import *  # noqa: F401, F403
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pytest


# ============================================================================
# Environment Fixtures
# ============================================================================


@pytest.fixture
def mock_claude_path(tmp_path: Path) -> Path:
    """Create a mock CLAUDE_PATH directory structure."""
    claude_path = tmp_path / ".claude"
    claude_path.mkdir()

    # Create subdirectories
    (claude_path / "rules").mkdir()
    (claude_path / "config").mkdir()
    (claude_path / ".data" / "logs").mkdir(parents=True)

    return claude_path


@pytest.fixture
def mock_env(mock_claude_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    """Set up mock environment variables."""
    env = {
        "CLAUDE_PATH": str(mock_claude_path),
        "WORKSPACE_ROOT": str(mock_claude_path.parent),
    }
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    return env


# ============================================================================
# Hook Event Fixtures
# ============================================================================


@pytest.fixture
def session_start_event() -> dict[str, Any]:
    """Sample SessionStart hook event."""
    return {
        "hook_event_name": "SessionStart",
        "session_id": "test-session-001",
        "cwd": "/workspace/test",
        "timestamp": "2025-01-01T00:00:00Z",
    }


@pytest.fixture
def user_prompt_event() -> dict[str, Any]:
    """Sample UserPromptSubmit hook event."""
    return {
        "hook_event_name": "UserPromptSubmit",
        "session_id": "test-session-001",
        "prompt": "Test prompt content",
        "timestamp": "2025-01-01T00:00:01Z",
    }


@pytest.fixture
def stop_event() -> dict[str, Any]:
    """Sample Stop hook event."""
    return {
        "hook_event_name": "Stop",
        "session_id": "test-session-001",
        "timestamp": "2025-01-01T00:01:00Z",
    }


@pytest.fixture
def stdin_event_factory():
    """Factory for creating stdin event data."""

    def _create(event_name: str, **kwargs) -> str:
        """Create JSON event data for stdin."""
        data = {"hook_event_name": event_name, **kwargs}
        return json.dumps(data)

    return _create


# ============================================================================
# File Content Fixtures
# ============================================================================


@pytest.fixture
def sample_rules_dir(mock_claude_path: Path) -> Path:
    """Create sample rule files."""
    rules_dir = mock_claude_path / "rules"
    rules_dir.mkdir(exist_ok=True)

    rules = [
        ("000-first-rule.md", "# RULE: 000\n\n**CRITICAL** First rule."),
        ("010-second-rule.md", "# RULE: 010\n\n**CRITICAL** Second rule."),
    ]

    for filename, content in rules:
        (rules_dir / filename).write_text(content)

    return rules_dir


@pytest.fixture
def sample_config(mock_claude_path: Path) -> Path:
    """Create a sample config.yml."""
    config_path = mock_claude_path / "config.yml"
    config_path.write_text(
        """
hooks:
  logger:
    enabled: true
    log_level: INFO
  rules_loader:
    reinforcement_enabled: true
"""
    )
    return config_path


# ============================================================================
# Output Capture Fixtures
# ============================================================================


@pytest.fixture
def capture_stdout(capsys: pytest.CaptureFixture) -> pytest.CaptureFixture:
    """Alias for pytest's capsys fixture."""
    return capsys


@pytest.fixture
def capture_logs(tmp_path: Path):
    """Capture log output to a temporary file."""
    log_file = tmp_path / "test.log"

    class LogCapture:
        def __init__(self):
            self.path = log_file

        def read(self) -> str:
            if self.path.exists():
                return self.path.read_text()
            return ""

        def lines(self) -> list[str]:
            return self.read().strip().split("\n") if self.read() else []

    return LogCapture()


# ============================================================================
# Assertion Helpers
# ============================================================================


def assert_valid_json_output(output: str) -> dict[str, Any]:
    """Assert output is valid JSON and return parsed data."""
    try:
        return json.loads(output.strip())
    except json.JSONDecodeError as e:
        pytest.fail(f"Invalid JSON output: {e}\nOutput was: {output[:500]}")


def assert_hook_success(output: dict[str, Any]) -> None:
    """Assert hook output indicates success."""
    assert "error" not in output or output.get("error") is None
    assert output.get("success", True) is True


def assert_hook_failure(output: dict[str, Any], error_substring: str = "") -> None:
    """Assert hook output indicates failure."""
    assert output.get("success", True) is False or "error" in output
    if error_substring:
        error = output.get("error", "")
        assert error_substring in error, f"Expected '{error_substring}' in '{error}'"
