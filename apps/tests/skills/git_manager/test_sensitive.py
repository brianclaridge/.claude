"""Tests for sensitive file detection."""

import pytest

from claude_apps.skills.git_manager.sensitive import (
    SAFE_PATTERNS,
    SENSITIVE_PATTERNS,
    SensitiveFile,
    SensitiveResult,
    is_safe_pattern,
    scan_sensitive,
)


class TestSafePattern:
    """Tests for is_safe_pattern function."""

    def test_env_example_is_safe(self):
        """Test .env.example is safe."""
        assert is_safe_pattern(".env.example") is True

    def test_env_template_is_safe(self):
        """Test .env.template is safe."""
        assert is_safe_pattern(".env.template") is True

    def test_env_sample_is_safe(self):
        """Test .env.sample is safe."""
        assert is_safe_pattern(".env.sample") is True

    def test_env_is_not_safe(self):
        """Test .env is not safe."""
        assert is_safe_pattern(".env") is False

    def test_env_local_is_not_safe(self):
        """Test .env.local is not safe."""
        assert is_safe_pattern(".env.local") is False

    def test_regular_file_is_not_safe(self):
        """Test regular files are not in safe patterns."""
        assert is_safe_pattern("config.py") is False


class TestSensitivePatterns:
    """Tests for sensitive pattern detection logic."""

    def test_env_pattern(self):
        """Test .env files are detected."""
        import re
        patterns = [re.compile(p, re.IGNORECASE) for p in SENSITIVE_PATTERNS]

        env_files = [".env", ".env.local", ".env.production"]
        for f in env_files:
            assert any(p.search(f) for p in patterns), f"{f} should match"

    def test_key_patterns(self):
        """Test key files are detected."""
        import re
        patterns = [re.compile(p, re.IGNORECASE) for p in SENSITIVE_PATTERNS]

        key_files = ["server.pem", "private.key", "cert.p12", "ssl.pfx"]
        for f in key_files:
            assert any(p.search(f) for p in patterns), f"{f} should match"

    def test_credentials_pattern(self):
        """Test credentials files are detected."""
        import re
        patterns = [re.compile(p, re.IGNORECASE) for p in SENSITIVE_PATTERNS]

        cred_files = ["credentials.json", "my-credentials.yaml", "db_credentials"]
        for f in cred_files:
            assert any(p.search(f) for p in patterns), f"{f} should match"

    def test_secret_pattern(self):
        """Test secret files are detected."""
        import re
        patterns = [re.compile(p, re.IGNORECASE) for p in SENSITIVE_PATTERNS]

        secret_files = ["secrets.yaml", "my-secret.json", "app_secrets"]
        for f in secret_files:
            assert any(p.search(f) for p in patterns), f"{f} should match"

    def test_ssh_keys_pattern(self):
        """Test SSH key files are detected."""
        import re
        patterns = [re.compile(p, re.IGNORECASE) for p in SENSITIVE_PATTERNS]

        ssh_files = ["id_rsa", "id_rsa.pub", "id_ed25519", "id_ed25519.pub"]
        for f in ssh_files:
            assert any(p.search(f) for p in patterns), f"{f} should match"

    def test_aws_exports_pattern(self):
        """Test aws-exports.js is detected."""
        import re
        patterns = [re.compile(p, re.IGNORECASE) for p in SENSITIVE_PATTERNS]

        assert any(p.search("aws-exports.js") for p in patterns)

    def test_htpasswd_pattern(self):
        """Test .htpasswd is detected."""
        import re
        patterns = [re.compile(p, re.IGNORECASE) for p in SENSITIVE_PATTERNS]

        assert any(p.search(".htpasswd") for p in patterns)

    def test_kube_config_pattern(self):
        """Test .kube/config is detected."""
        import re
        patterns = [re.compile(p, re.IGNORECASE) for p in SENSITIVE_PATTERNS]

        assert any(p.search(".kube/config") for p in patterns)

    def test_safe_files_not_sensitive(self):
        """Test regular files are not sensitive."""
        import re
        patterns = [re.compile(p, re.IGNORECASE) for p in SENSITIVE_PATTERNS]

        safe_files = ["config.py", "main.go", "package.json", "README.md"]
        for f in safe_files:
            matches = [p.search(f) for p in patterns]
            assert not any(matches), f"{f} should not match sensitive patterns"


class TestSensitiveFile:
    """Tests for SensitiveFile dataclass."""

    def test_creation(self):
        """Test creating SensitiveFile."""
        sf = SensitiveFile(
            path=".env",
            pattern_matched=r"\.env$",
            status="new",
        )

        assert sf.path == ".env"
        assert sf.pattern_matched == r"\.env$"
        assert sf.status == "new"


class TestSensitiveResult:
    """Tests for SensitiveResult dataclass."""

    def test_empty_result(self):
        """Test empty result."""
        result = SensitiveResult()

        assert result.found is False
        assert result.files == []
        assert result.exit_code == 0
        assert result.error is None

    def test_to_dict_empty(self):
        """Test serialization of empty result."""
        result = SensitiveResult()
        d = result.to_dict()

        assert d["found"] is False
        assert d["files"] == []
        assert d["error"] is None

    def test_to_dict_with_files(self):
        """Test serialization with sensitive files."""
        result = SensitiveResult(
            found=True,
            files=[
                SensitiveFile(path=".env", pattern_matched=r"\.env$", status="new"),
                SensitiveFile(path="secrets.yaml", pattern_matched="secret", status="staged"),
            ],
            exit_code=1,
        )

        d = result.to_dict()

        assert d["found"] is True
        assert len(d["files"]) == 2
        assert d["files"][0]["path"] == ".env"
        assert d["files"][1]["status"] == "staged"


class TestScanSensitive:
    """Tests for scan_sensitive function."""

    def test_scan_no_git_repo(self, tmp_path):
        """Test scanning non-git directory."""
        result = scan_sensitive(tmp_path)

        # Should return empty result (no status files)
        assert result.found is False
        assert result.exit_code == 0

    def test_scan_clean_repo(self, tmp_path, monkeypatch):
        """Test scanning clean repo with no sensitive files."""
        # Mock subprocess to return clean status
        import subprocess

        def mock_run(*args, **kwargs):
            class MockResult:
                returncode = 0
                stdout = "M  config.py\nA  main.go\n"
            return MockResult()

        monkeypatch.setattr(subprocess, "run", mock_run)

        result = scan_sensitive(tmp_path)

        assert result.found is False
        assert len(result.files) == 0

    def test_scan_with_env_file(self, tmp_path, monkeypatch):
        """Test scanning repo with .env file."""
        import subprocess

        def mock_run(*args, **kwargs):
            class MockResult:
                returncode = 0
                stdout = "A  .env\nM  config.py\n"
            return MockResult()

        monkeypatch.setattr(subprocess, "run", mock_run)

        result = scan_sensitive(tmp_path)

        assert result.found is True
        assert len(result.files) == 1
        assert result.files[0].path == ".env"
        assert result.exit_code == 1

    def test_scan_with_multiple_sensitive_files(self, tmp_path, monkeypatch):
        """Test scanning repo with multiple sensitive files."""
        import subprocess

        def mock_run(*args, **kwargs):
            class MockResult:
                returncode = 0
                stdout = "A  .env\n?? secrets.yaml\nM  credentials.json\n"
            return MockResult()

        monkeypatch.setattr(subprocess, "run", mock_run)

        result = scan_sensitive(tmp_path)

        assert result.found is True
        assert len(result.files) == 3
        paths = {f.path for f in result.files}
        assert ".env" in paths
        assert "secrets.yaml" in paths
        assert "credentials.json" in paths

    def test_scan_excludes_safe_patterns(self, tmp_path, monkeypatch):
        """Test that .env.example is excluded."""
        import subprocess

        def mock_run(*args, **kwargs):
            class MockResult:
                returncode = 0
                stdout = "A  .env.example\nA  .env\n"
            return MockResult()

        monkeypatch.setattr(subprocess, "run", mock_run)

        result = scan_sensitive(tmp_path)

        assert result.found is True
        assert len(result.files) == 1
        assert result.files[0].path == ".env"

    def test_scan_detects_status_types(self, tmp_path, monkeypatch):
        """Test correct status type detection."""
        import subprocess

        def mock_run(*args, **kwargs):
            class MockResult:
                returncode = 0
                # A = staged, ?? = new, M = staged (index modified)
                # Note: " M" would be working tree modified (not staged)
                stdout = "A  .env\n?? secrets.yaml\nM  credentials.json\n"
            return MockResult()

        monkeypatch.setattr(subprocess, "run", mock_run)

        result = scan_sensitive(tmp_path)

        status_by_path = {f.path: f.status for f in result.files}
        assert status_by_path[".env"] == "staged"
        assert status_by_path["secrets.yaml"] == "new"
        # M with first char not space = staged per source logic
        assert status_by_path["credentials.json"] == "staged"
