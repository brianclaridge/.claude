"""Tests for remote authentication checking."""

from pathlib import Path

import pytest

from claude_apps.skills.git_manager.auth import (
    AuthResult,
    GH_AUTH_COMMAND,
    check_auth,
    check_gh_auth,
    check_ssh_auth,
    detect_remote_type,
    get_remote_url,
)


class TestDetectRemoteType:
    """Tests for detect_remote_type function."""

    def test_https_url(self):
        """Test detecting HTTPS remote."""
        assert detect_remote_type("https://github.com/user/repo.git") == "https"
        assert detect_remote_type("https://gitlab.com/user/repo.git") == "https"

    def test_ssh_git_url(self):
        """Test detecting SSH git@ URL."""
        assert detect_remote_type("git@github.com:user/repo.git") == "ssh"
        assert detect_remote_type("git@gitlab.com:user/repo.git") == "ssh"

    def test_ssh_protocol_url(self):
        """Test detecting ssh:// protocol URL."""
        assert detect_remote_type("ssh://git@github.com/user/repo.git") == "ssh"

    def test_local_path(self):
        """Test detecting local paths."""
        assert detect_remote_type("/path/to/repo") == "local"
        assert detect_remote_type("file:///path/to/repo") == "local"

    def test_unknown_url(self):
        """Test unknown URL type."""
        assert detect_remote_type("ftp://example.com/repo") == "unknown"
        assert detect_remote_type("something-weird") == "unknown"


class TestGetRemoteUrl:
    """Tests for get_remote_url function."""

    def test_returns_url(self, tmp_path, monkeypatch):
        """Test getting remote URL."""
        import subprocess

        def mock_run(*args, **kwargs):
            class MockResult:
                returncode = 0
                stdout = "https://github.com/user/repo.git\n"
            return MockResult()

        monkeypatch.setattr(subprocess, "run", mock_run)

        url = get_remote_url(tmp_path)

        assert url == "https://github.com/user/repo.git"

    def test_returns_none_on_failure(self, tmp_path, monkeypatch):
        """Test returns None when no remote."""
        import subprocess

        def mock_run(*args, **kwargs):
            class MockResult:
                returncode = 1
                stdout = ""
            return MockResult()

        monkeypatch.setattr(subprocess, "run", mock_run)

        url = get_remote_url(tmp_path)

        assert url is None


class TestCheckGhAuth:
    """Tests for check_gh_auth function."""

    def test_authenticated(self, monkeypatch):
        """Test when gh is authenticated."""
        import subprocess

        def mock_run(*args, **kwargs):
            class MockResult:
                returncode = 0
            return MockResult()

        monkeypatch.setattr(subprocess, "run", mock_run)

        assert check_gh_auth() is True

    def test_not_authenticated(self, monkeypatch):
        """Test when gh is not authenticated."""
        import subprocess

        def mock_run(*args, **kwargs):
            class MockResult:
                returncode = 1
            return MockResult()

        monkeypatch.setattr(subprocess, "run", mock_run)

        assert check_gh_auth() is False

    def test_gh_not_installed(self, monkeypatch):
        """Test when gh is not installed."""
        import subprocess

        def mock_run(*args, **kwargs):
            raise FileNotFoundError("gh not found")

        monkeypatch.setattr(subprocess, "run", mock_run)

        assert check_gh_auth() is False


class TestCheckSshAuth:
    """Tests for check_ssh_auth function."""

    def test_authenticated(self, monkeypatch):
        """Test when SSH is authenticated."""
        import subprocess

        def mock_run(*args, **kwargs):
            class MockResult:
                returncode = 1
                stdout = ""
                stderr = "Hi testuser! You've successfully authenticated, but GitHub does not provide shell access."
            return MockResult()

        monkeypatch.setattr(subprocess, "run", mock_run)

        assert check_ssh_auth() is True

    def test_not_authenticated(self, monkeypatch):
        """Test when SSH is not authenticated."""
        import subprocess

        def mock_run(*args, **kwargs):
            class MockResult:
                returncode = 255
                stdout = ""
                stderr = "Permission denied (publickey)."
            return MockResult()

        monkeypatch.setattr(subprocess, "run", mock_run)

        assert check_ssh_auth() is False


class TestAuthResult:
    """Tests for AuthResult dataclass."""

    def test_defaults(self):
        """Test default values."""
        result = AuthResult()

        assert result.remote_url is None
        assert result.remote_type == "unknown"
        assert result.authenticated is False
        assert result.auth_method is None
        assert result.needs_auth is False
        assert result.exit_code == 0
        assert result.error is None
        assert result.guidance is None

    def test_to_dict(self):
        """Test serialization."""
        result = AuthResult(
            remote_url="https://github.com/user/repo.git",
            remote_type="https",
            authenticated=True,
            auth_method="gh",
            needs_auth=False,
        )

        d = result.to_dict()

        assert d["remote_url"] == "https://github.com/user/repo.git"
        assert d["remote_type"] == "https"
        assert d["authenticated"] is True
        assert d["auth_method"] == "gh"
        assert d["needs_auth"] is False


class TestCheckAuth:
    """Tests for check_auth function."""

    def test_no_remote(self, tmp_path, monkeypatch):
        """Test when no remote is configured."""
        import subprocess

        def mock_run(*args, **kwargs):
            class MockResult:
                returncode = 1
                stdout = ""
            return MockResult()

        monkeypatch.setattr(subprocess, "run", mock_run)

        result = check_auth(tmp_path)

        assert result.exit_code == 1
        assert "No remote" in result.error

    def test_ssh_authenticated(self, tmp_path, monkeypatch):
        """Test SSH remote with valid auth."""
        import subprocess

        def mock_run(*args, **kwargs):
            cmd = args[0]

            if "get-url" in cmd:
                class MockResult:
                    returncode = 0
                    stdout = "git@github.com:user/repo.git\n"
                return MockResult()

            # SSH check
            class MockResult:
                returncode = 1
                stdout = ""
                stderr = "Hi testuser! You've successfully authenticated"
            return MockResult()

        monkeypatch.setattr(subprocess, "run", mock_run)

        result = check_auth(tmp_path)

        assert result.remote_type == "ssh"
        assert result.authenticated is True
        assert result.auth_method == "ssh-key"
        assert result.exit_code == 0

    def test_ssh_not_authenticated(self, tmp_path, monkeypatch):
        """Test SSH remote without auth."""
        import subprocess

        def mock_run(*args, **kwargs):
            cmd = args[0]

            if "get-url" in cmd:
                class MockResult:
                    returncode = 0
                    stdout = "git@github.com:user/repo.git\n"
                return MockResult()

            # SSH check fails
            class MockResult:
                returncode = 255
                stdout = ""
                stderr = "Permission denied"
            return MockResult()

        monkeypatch.setattr(subprocess, "run", mock_run)

        result = check_auth(tmp_path)

        assert result.remote_type == "ssh"
        assert result.authenticated is False
        assert result.needs_auth is True
        assert result.exit_code == 1
        assert "SSH authentication failed" in result.error

    def test_https_github_authenticated(self, tmp_path, monkeypatch):
        """Test HTTPS GitHub remote with gh auth."""
        import subprocess

        def mock_run(*args, **kwargs):
            cmd = args[0]

            if "get-url" in cmd:
                class MockResult:
                    returncode = 0
                    stdout = "https://github.com/user/repo.git\n"
                return MockResult()

            if "gh" in cmd and "auth" in cmd:
                class MockResult:
                    returncode = 0
                return MockResult()

            class MockResult:
                returncode = 1
            return MockResult()

        monkeypatch.setattr(subprocess, "run", mock_run)

        result = check_auth(tmp_path)

        assert result.remote_type == "https"
        assert result.authenticated is True
        assert result.auth_method == "gh"
        assert result.exit_code == 0

    def test_https_github_not_authenticated(self, tmp_path, monkeypatch):
        """Test HTTPS GitHub remote without gh auth."""
        import subprocess

        def mock_run(*args, **kwargs):
            cmd = args[0]

            if "get-url" in cmd:
                class MockResult:
                    returncode = 0
                    stdout = "https://github.com/user/repo.git\n"
                return MockResult()

            # gh auth status fails
            class MockResult:
                returncode = 1
            return MockResult()

        monkeypatch.setattr(subprocess, "run", mock_run)

        result = check_auth(tmp_path)

        assert result.remote_type == "https"
        assert result.authenticated is False
        assert result.needs_auth is True
        assert result.exit_code == 1
        assert "GitHub CLI not authenticated" in result.error
        assert GH_AUTH_COMMAND in result.guidance

    def test_https_non_github(self, tmp_path, monkeypatch):
        """Test HTTPS non-GitHub remote."""
        import subprocess

        def mock_run(*args, **kwargs):
            cmd = args[0]

            if "get-url" in cmd:
                class MockResult:
                    returncode = 0
                    stdout = "https://gitlab.com/user/repo.git\n"
                return MockResult()

            class MockResult:
                returncode = 1
            return MockResult()

        monkeypatch.setattr(subprocess, "run", mock_run)

        result = check_auth(tmp_path)

        assert result.remote_type == "https"
        assert result.authenticated is True  # Optimistic for non-GitHub
        assert result.auth_method == "credential-helper"

    def test_local_remote(self, tmp_path, monkeypatch):
        """Test local file remote."""
        import subprocess

        def mock_run(*args, **kwargs):
            cmd = args[0]

            if "get-url" in cmd:
                class MockResult:
                    returncode = 0
                    stdout = "/path/to/local/repo\n"
                return MockResult()

            class MockResult:
                returncode = 1
            return MockResult()

        monkeypatch.setattr(subprocess, "run", mock_run)

        result = check_auth(tmp_path)

        assert result.remote_type == "local"
        assert result.authenticated is True
        assert result.auth_method == "none"
        assert result.exit_code == 0

    def test_unknown_remote_type(self, tmp_path, monkeypatch):
        """Test unknown remote type."""
        import subprocess

        def mock_run(*args, **kwargs):
            cmd = args[0]

            if "get-url" in cmd:
                class MockResult:
                    returncode = 0
                    stdout = "ftp://weird/url\n"
                return MockResult()

            class MockResult:
                returncode = 1
            return MockResult()

        monkeypatch.setattr(subprocess, "run", mock_run)

        result = check_auth(tmp_path)

        assert result.exit_code == 1
        assert "Unknown remote type" in result.error
