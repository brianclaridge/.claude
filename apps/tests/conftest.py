"""Shared pytest fixtures for all tests."""

import os
from pathlib import Path
from typing import Any, Generator

import pytest


@pytest.fixture
def tmp_workspace(tmp_path: Path) -> Path:
    """Create a temporary workspace directory."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    return workspace


@pytest.fixture
def mock_env(monkeypatch: pytest.MonkeyPatch):
    """Factory for mocking environment variables."""

    def _mock(**env_vars: str) -> None:
        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)

    return _mock


@pytest.fixture
def mock_claude_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create a mock CLAUDE_PATH directory structure."""
    claude_path = tmp_path / ".claude"
    claude_path.mkdir()

    # Create standard subdirectories
    (claude_path / "plans").mkdir()
    (claude_path / "rules").mkdir()
    (claude_path / ".data").mkdir()
    (claude_path / ".data" / "logs").mkdir()

    monkeypatch.setenv("CLAUDE_PATH", str(claude_path))
    return claude_path


@pytest.fixture
def mock_git_repo(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a mock git repository."""
    import subprocess

    repo_path = tmp_path / "repo"
    repo_path.mkdir()

    # Initialize git repo
    subprocess.run(["git", "init"], cwd=repo_path, capture_output=True, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repo_path,
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repo_path,
        capture_output=True,
        check=True,
    )

    # Create initial commit
    readme = repo_path / "README.md"
    readme.write_text("# Test Repo\n")
    subprocess.run(["git", "add", "."], cwd=repo_path, capture_output=True, check=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=repo_path,
        capture_output=True,
        check=True,
    )

    yield repo_path


@pytest.fixture
def sample_yaml_content() -> dict[str, Any]:
    """Sample YAML content for testing."""
    return {
        "schema_version": "1.0",
        "accounts": {
            "sandbox": {
                "id": "123456789012",
                "name": "test-sandbox",
                "sso_role": "AdministratorAccess",
            }
        },
    }


@pytest.fixture(autouse=True)
def reset_env_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reset critical environment variables for test isolation."""
    # Ensure AWS credentials don't leak into tests
    for var in ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN"]:
        monkeypatch.delenv(var, raising=False)
