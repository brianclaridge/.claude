"""Tests for git identity detection."""

from pathlib import Path

import pytest

from claude_apps.skills.git_manager.identity import (
    IdentityResult,
    derive_noreply_email,
    detect_from_git_config,
    detect_from_gh,
    detect_from_ssh,
    detect_identity,
    load_from_env,
)


class TestLoadFromEnv:
    """Tests for load_from_env function."""

    def test_load_from_environment(self, monkeypatch):
        """Test loading from environment variables."""
        monkeypatch.setenv("GIT_USER_NAME", "testuser")
        monkeypatch.setenv("GIT_USER_EMAIL", "test@example.com")

        name, email = load_from_env(None)

        assert name == "testuser"
        assert email == "test@example.com"

    def test_load_from_env_file(self, tmp_path, monkeypatch):
        """Test loading from .env file."""
        monkeypatch.delenv("GIT_USER_NAME", raising=False)
        monkeypatch.delenv("GIT_USER_EMAIL", raising=False)

        env_file = tmp_path / ".env"
        env_file.write_text('GIT_USER_NAME=fileuser\nGIT_USER_EMAIL=file@example.com')

        name, email = load_from_env(env_file)

        assert name == "fileuser"
        assert email == "file@example.com"

    def test_env_file_with_quotes(self, tmp_path, monkeypatch):
        """Test parsing env file with quoted values."""
        monkeypatch.delenv("GIT_USER_NAME", raising=False)
        monkeypatch.delenv("GIT_USER_EMAIL", raising=False)

        env_file = tmp_path / ".env"
        env_file.write_text('GIT_USER_NAME="quoted user"\nGIT_USER_EMAIL=\'quoted@example.com\'')

        name, email = load_from_env(env_file)

        assert name == "quoted user"
        assert email == "quoted@example.com"

    def test_file_overrides_environment(self, tmp_path, monkeypatch):
        """Test that file values override environment."""
        monkeypatch.setenv("GIT_USER_NAME", "envuser")
        monkeypatch.setenv("GIT_USER_EMAIL", "env@example.com")

        env_file = tmp_path / ".env"
        env_file.write_text('GIT_USER_NAME=fileuser\nGIT_USER_EMAIL=file@example.com')

        name, email = load_from_env(env_file)

        # File overwrites env values when present
        assert name == "fileuser"
        assert email == "file@example.com"

    def test_no_env_returns_none(self, tmp_path, monkeypatch):
        """Test returns None when no env found."""
        monkeypatch.delenv("GIT_USER_NAME", raising=False)
        monkeypatch.delenv("GIT_USER_EMAIL", raising=False)

        name, email = load_from_env(None)

        assert name is None
        assert email is None

    def test_nonexistent_env_file(self, tmp_path, monkeypatch):
        """Test with nonexistent env file."""
        monkeypatch.delenv("GIT_USER_NAME", raising=False)
        monkeypatch.delenv("GIT_USER_EMAIL", raising=False)

        name, email = load_from_env(tmp_path / "nonexistent.env")

        assert name is None
        assert email is None


class TestDeriveNoreplyEmail:
    """Tests for derive_noreply_email function."""

    def test_derives_email(self):
        """Test deriving GitHub noreply email."""
        email = derive_noreply_email("testuser")
        assert email == "testuser@users.noreply.github.com"

    def test_preserves_case(self):
        """Test that username case is preserved."""
        email = derive_noreply_email("TestUser")
        assert email == "TestUser@users.noreply.github.com"


class TestDetectFromSsh:
    """Tests for detect_from_ssh function."""

    def test_successful_ssh_auth(self, monkeypatch):
        """Test successful SSH authentication."""
        import subprocess

        def mock_run(*args, **kwargs):
            class MockResult:
                returncode = 1  # SSH returns 1 even on success
                stdout = ""
                stderr = "Hi testuser! You've successfully authenticated, but GitHub does not provide shell access."
            return MockResult()

        monkeypatch.setattr(subprocess, "run", mock_run)

        username, authenticated = detect_from_ssh()

        assert username == "testuser"
        assert authenticated is True

    def test_failed_ssh_auth(self, monkeypatch):
        """Test failed SSH authentication."""
        import subprocess

        def mock_run(*args, **kwargs):
            class MockResult:
                returncode = 255
                stdout = ""
                stderr = "Permission denied (publickey)."
            return MockResult()

        monkeypatch.setattr(subprocess, "run", mock_run)

        username, authenticated = detect_from_ssh()

        assert username is None
        assert authenticated is False

    def test_timeout(self, monkeypatch):
        """Test SSH timeout handling."""
        import subprocess

        def mock_run(*args, **kwargs):
            raise subprocess.TimeoutExpired("ssh", 10)

        monkeypatch.setattr(subprocess, "run", mock_run)

        username, authenticated = detect_from_ssh()

        assert username is None
        assert authenticated is False


class TestDetectFromGh:
    """Tests for detect_from_gh function."""

    def test_successful_gh_auth(self, monkeypatch):
        """Test successful gh CLI authentication."""
        import subprocess

        call_count = [0]

        def mock_run(*args, **kwargs):
            call_count[0] += 1
            class MockResult:
                returncode = 0
                stdout = "testuser\n" if call_count[0] == 1 else "test@example.com\n"
            return MockResult()

        monkeypatch.setattr(subprocess, "run", mock_run)

        login, email = detect_from_gh()

        assert login == "testuser"
        assert email == "test@example.com"

    def test_gh_auth_null_email(self, monkeypatch):
        """Test gh CLI with null email."""
        import subprocess

        call_count = [0]

        def mock_run(*args, **kwargs):
            call_count[0] += 1
            class MockResult:
                returncode = 0
                stdout = "testuser\n" if call_count[0] == 1 else "null\n"
            return MockResult()

        monkeypatch.setattr(subprocess, "run", mock_run)

        login, email = detect_from_gh()

        assert login == "testuser"
        assert email is None

    def test_gh_not_installed(self, monkeypatch):
        """Test when gh CLI is not installed."""
        import subprocess

        def mock_run(*args, **kwargs):
            raise FileNotFoundError("gh not found")

        monkeypatch.setattr(subprocess, "run", mock_run)

        login, email = detect_from_gh()

        assert login is None
        assert email is None


class TestDetectFromGitConfig:
    """Tests for detect_from_git_config function."""

    def test_successful_config(self, monkeypatch):
        """Test reading from git config."""
        import subprocess

        call_count = [0]

        def mock_run(*args, **kwargs):
            call_count[0] += 1
            class MockResult:
                returncode = 0
                # First call is for name, second for email
                stdout = "Git User\n" if call_count[0] == 1 else "git@example.com\n"
            return MockResult()

        monkeypatch.setattr(subprocess, "run", mock_run)

        name, email = detect_from_git_config()

        assert name == "Git User"
        assert email == "git@example.com"

    def test_no_config(self, monkeypatch):
        """Test when git config is not set."""
        import subprocess

        def mock_run(*args, **kwargs):
            class MockResult:
                returncode = 1
                stdout = ""
            return MockResult()

        monkeypatch.setattr(subprocess, "run", mock_run)

        name, email = detect_from_git_config()

        assert name is None
        assert email is None


class TestIdentityResult:
    """Tests for IdentityResult dataclass."""

    def test_defaults(self):
        """Test default values."""
        result = IdentityResult()

        assert result.name is None
        assert result.email is None
        assert result.source is None
        assert result.detected is False
        assert result.needs_input is False
        assert result.exit_code == 0
        assert result.error is None

    def test_to_dict(self):
        """Test serialization."""
        result = IdentityResult(
            name="testuser",
            email="test@example.com",
            source="env",
            detected=True,
            needs_input=False,
        )

        d = result.to_dict()

        assert d["name"] == "testuser"
        assert d["email"] == "test@example.com"
        assert d["source"] == "env"
        assert d["detected"] is True
        assert d["needs_input"] is False


class TestDetectIdentity:
    """Tests for detect_identity function."""

    def test_detects_from_env(self, tmp_path, monkeypatch):
        """Test detection from environment."""
        monkeypatch.setenv("GIT_USER_NAME", "envuser")
        monkeypatch.setenv("GIT_USER_EMAIL", "env@example.com")

        result = detect_identity()

        assert result.detected is True
        assert result.source == "env"
        assert result.name == "envuser"
        assert result.email == "env@example.com"
        assert result.needs_input is False
        assert result.exit_code == 0

    def test_detects_from_env_file(self, tmp_path, monkeypatch):
        """Test detection from .env file."""
        monkeypatch.delenv("GIT_USER_NAME", raising=False)
        monkeypatch.delenv("GIT_USER_EMAIL", raising=False)

        env_file = tmp_path / ".env"
        env_file.write_text('GIT_USER_NAME=fileuser\nGIT_USER_EMAIL=file@example.com')

        result = detect_identity(env_path=env_file)

        assert result.detected is True
        assert result.source == "env"
        assert result.name == "fileuser"
        assert result.email == "file@example.com"

    def test_detects_from_gh(self, monkeypatch):
        """Test detection from gh CLI."""
        monkeypatch.delenv("GIT_USER_NAME", raising=False)
        monkeypatch.delenv("GIT_USER_EMAIL", raising=False)

        import subprocess
        call_count = [0]

        def mock_run(*args, **kwargs):
            call_count[0] += 1
            cmd = args[0]

            # gh api user calls
            if "gh" in cmd:
                class MockResult:
                    returncode = 0
                    # Login first, then email
                    stdout = "ghuser\n" if "login" in str(cmd) else "gh@example.com\n"
                return MockResult()

            # git config calls
            class MockResult:
                returncode = 1
                stdout = ""
            return MockResult()

        monkeypatch.setattr(subprocess, "run", mock_run)

        result = detect_identity(check_ssh=False)

        assert result.detected is True
        assert result.source == "gh"
        assert result.name == "ghuser"
        assert result.needs_input is True
        assert result.exit_code == 2

    def test_falls_back_to_git_config(self, monkeypatch):
        """Test fallback to git config."""
        monkeypatch.delenv("GIT_USER_NAME", raising=False)
        monkeypatch.delenv("GIT_USER_EMAIL", raising=False)

        import subprocess
        call_count = [0]

        def mock_run(*args, **kwargs):
            call_count[0] += 1
            cmd = args[0]

            # gh and ssh fail
            if "gh" in cmd or "ssh" in cmd:
                class MockResult:
                    returncode = 1
                    stdout = ""
                    stderr = ""
                return MockResult()

            # git config succeeds
            class MockResult:
                returncode = 0
                stdout = "Git User\n" if "user.name" in cmd else "git@example.com\n"
            return MockResult()

        monkeypatch.setattr(subprocess, "run", mock_run)

        result = detect_identity(check_ssh=False, check_gh=False)

        assert result.detected is True
        assert result.source == "git-config"
        assert result.name == "Git User"
        assert result.email == "git@example.com"

    def test_no_identity_found(self, monkeypatch):
        """Test when no identity can be found."""
        monkeypatch.delenv("GIT_USER_NAME", raising=False)
        monkeypatch.delenv("GIT_USER_EMAIL", raising=False)

        import subprocess

        def mock_run(*args, **kwargs):
            class MockResult:
                returncode = 1
                stdout = ""
                stderr = ""
            return MockResult()

        monkeypatch.setattr(subprocess, "run", mock_run)

        result = detect_identity(check_ssh=False, check_gh=False)

        assert result.detected is False
        assert result.needs_input is True
        assert result.exit_code == 2
        assert "No git identity" in result.error
