"""Tests for AWS background discovery and quick auth functions."""

import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from claude_apps.skills.aws_login.__main__ import (
    spawn_background_discovery,
    quick_auth_for_account,
    _cache_credentials_for_cli,
    discover_single_account,
)


class TestSpawnBackgroundDiscovery:
    """Tests for spawn_background_discovery function."""

    def test_creates_subprocess(self, monkeypatch, tmp_path):
        """Verify background process is spawned with correct args."""
        monkeypatch.setenv("CLAUDE_PATH", str(tmp_path))
        monkeypatch.setenv("CLAUDE_DATA_PATH", str(tmp_path / ".data"))

        log_dir = tmp_path / ".data" / "logs"

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.pid = 12345
            mock_popen.return_value = mock_process

            spawn_background_discovery(["--login"])

            mock_popen.assert_called_once()
            call_args = mock_popen.call_args[0][0]
            assert "uv" in call_args
            assert "--login" in call_args

    def test_logs_to_file(self, monkeypatch, tmp_path):
        """Verify output redirected to log file."""
        monkeypatch.setenv("CLAUDE_PATH", str(tmp_path))
        monkeypatch.setenv("CLAUDE_DATA_PATH", str(tmp_path / ".data"))

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.pid = 12345
            mock_popen.return_value = mock_process

            spawn_background_discovery(["--login"])

            # Log file should be created
            log_file = tmp_path / ".data" / "logs" / "aws-discovery.log"
            assert log_file.exists()

    def test_creates_pid_file(self, monkeypatch, tmp_path):
        """Verify PID file is created for tracking."""
        monkeypatch.setenv("CLAUDE_PATH", str(tmp_path))
        monkeypatch.setenv("CLAUDE_DATA_PATH", str(tmp_path / ".data"))

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.pid = 12345
            mock_popen.return_value = mock_process

            spawn_background_discovery(["--login"])

            pid_file = tmp_path / ".data" / "logs" / "aws-discovery.pid"
            assert pid_file.exists()
            assert pid_file.read_text() == "12345"

    def test_handles_missing_claude_path(self, monkeypatch, capsys):
        """Verify graceful handling when CLAUDE_PATH not set."""
        monkeypatch.delenv("CLAUDE_PATH", raising=False)

        spawn_background_discovery(["--login"])

        # Should log error but not raise (structlog outputs to stdout)
        captured = capsys.readouterr()
        assert "CLAUDE_PATH not set" in captured.out

    def test_passes_skip_flags(self, monkeypatch, tmp_path):
        """Verify skip flags are passed to background process."""
        monkeypatch.setenv("CLAUDE_PATH", str(tmp_path))
        monkeypatch.setenv("CLAUDE_DATA_PATH", str(tmp_path / ".data"))

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.pid = 12345
            mock_popen.return_value = mock_process

            spawn_background_discovery(["--login", "--skip-vpc", "--skip-resources"])

            call_args = mock_popen.call_args[0][0]
            assert "--skip-vpc" in call_args
            assert "--skip-resources" in call_args


class TestQuickAuthForAccount:
    """Tests for quick_auth_for_account function."""

    def test_single_device_flow(self, monkeypatch, tmp_path):
        """Verify only one SSO auth is performed."""
        monkeypatch.setenv("CLAUDE_PATH", str(tmp_path))
        monkeypatch.setenv("AWS_SSO_START_URL", "https://test.awsapps.com/start")

        mock_account = MagicMock()
        mock_account.account_id = "123456789012"
        mock_account.account_name = "Sandbox"

        with patch("claude_apps.skills.aws_login.__main__.check_credentials_valid") as mock_check:
            mock_check.return_value = False  # Force full auth flow

            with patch("claude_apps.skills.aws_login.__main__.poll_for_token") as mock_poll:
                mock_poll.return_value = MagicMock(
                    success=True, access_token="test-token"
                )

                with patch("claude_apps.skills.aws_login.__main__.discover_sso_accounts") as mock_discover:
                    mock_discover.return_value = [mock_account]

                    with patch("claude_apps.skills.aws_login.__main__.discover_account_roles") as mock_roles:
                        mock_roles.return_value = ["AdministratorAccess"]

                        with patch("claude_apps.skills.aws_login.__main__.get_role_credentials") as mock_creds:
                            mock_creds.return_value = MagicMock(
                                access_key_id="AKIATEST",
                                secret_access_key="secret",
                                session_token="token",
                                expiration=1234567890000,
                            )

                            with patch("claude_apps.skills.aws_login.__main__.ensure_profile"):
                                with patch("claude_apps.skills.aws_login.__main__.set_default_profile"):
                                    result = quick_auth_for_account("sandbox")

                            # Only one poll_for_token call (single device flow)
                            assert mock_poll.call_count == 1
                            assert result is True

    def test_creates_profile(self, monkeypatch, tmp_path):
        """Verify profile is created for target account."""
        monkeypatch.setenv("CLAUDE_PATH", str(tmp_path))
        monkeypatch.setenv("AWS_SSO_START_URL", "https://test.awsapps.com/start")

        mock_account = MagicMock()
        mock_account.account_id = "123456789012"
        mock_account.account_name = "Sandbox"

        with patch("claude_apps.skills.aws_login.__main__.check_credentials_valid") as mock_check:
            mock_check.return_value = False  # Force full auth flow

            with patch("claude_apps.skills.aws_login.__main__.poll_for_token") as mock_poll:
                mock_poll.return_value = MagicMock(success=True, access_token="test-token")

                with patch("claude_apps.skills.aws_login.__main__.discover_sso_accounts") as mock_discover:
                    mock_discover.return_value = [mock_account]

                    with patch("claude_apps.skills.aws_login.__main__.discover_account_roles") as mock_roles:
                        mock_roles.return_value = ["AdministratorAccess"]

                        with patch("claude_apps.skills.aws_login.__main__.get_role_credentials") as mock_creds:
                            mock_creds.return_value = MagicMock(
                                access_key_id="AKIATEST",
                                secret_access_key="secret",
                                session_token="token",
                                expiration=1234567890000,
                            )

                            with patch("claude_apps.skills.aws_login.__main__.ensure_profile") as mock_ensure:
                                with patch("claude_apps.skills.aws_login.__main__.set_default_profile"):
                                    quick_auth_for_account("sandbox")

                                mock_ensure.assert_called_once_with(
                                    profile_name="sandbox",
                                    account_id="123456789012",
                                    account_name="Sandbox",
                                    sso_role="AdministratorAccess",
                                )

    def test_sets_default(self, monkeypatch, tmp_path):
        """Verify default profile is set correctly."""
        monkeypatch.setenv("CLAUDE_PATH", str(tmp_path))
        monkeypatch.setenv("AWS_SSO_START_URL", "https://test.awsapps.com/start")

        mock_account = MagicMock()
        mock_account.account_id = "123456789012"
        mock_account.account_name = "Sandbox"

        with patch("claude_apps.skills.aws_login.__main__.check_credentials_valid") as mock_check:
            mock_check.return_value = False  # Force full auth flow

            with patch("claude_apps.skills.aws_login.__main__.poll_for_token") as mock_poll:
                mock_poll.return_value = MagicMock(success=True, access_token="test-token")

                with patch("claude_apps.skills.aws_login.__main__.discover_sso_accounts") as mock_discover:
                    mock_discover.return_value = [mock_account]

                    with patch("claude_apps.skills.aws_login.__main__.discover_account_roles") as mock_roles:
                        mock_roles.return_value = ["AdministratorAccess"]

                        with patch("claude_apps.skills.aws_login.__main__.get_role_credentials") as mock_creds:
                            mock_creds.return_value = MagicMock(
                                access_key_id="AKIATEST",
                                secret_access_key="secret",
                                session_token="token",
                                expiration=1234567890000,
                            )

                            with patch("claude_apps.skills.aws_login.__main__.ensure_profile"):
                                with patch("claude_apps.skills.aws_login.__main__.set_default_profile") as mock_default:
                                    quick_auth_for_account("sandbox")

                                    mock_default.assert_called_once_with("sandbox")

    def test_account_not_found(self, monkeypatch, tmp_path):
        """Verify error when account alias not found."""
        monkeypatch.setenv("CLAUDE_PATH", str(tmp_path))
        monkeypatch.setenv("AWS_SSO_START_URL", "https://test.awsapps.com/start")

        mock_account = MagicMock()
        mock_account.account_id = "123456789012"
        mock_account.account_name = "Production"

        with patch("claude_apps.skills.aws_login.__main__.check_credentials_valid") as mock_check:
            mock_check.return_value = False  # Force full auth flow

            with patch("claude_apps.skills.aws_login.__main__.poll_for_token") as mock_poll:
                mock_poll.return_value = MagicMock(success=True, access_token="test-token")

                with patch("claude_apps.skills.aws_login.__main__.discover_sso_accounts") as mock_discover:
                    mock_discover.return_value = [mock_account]

                    result = quick_auth_for_account("sandbox")

                    assert result is False

    def test_skips_auth_when_credentials_valid(self, monkeypatch, tmp_path):
        """Verify auth is skipped when credentials are still valid."""
        monkeypatch.setenv("CLAUDE_PATH", str(tmp_path))

        with patch("claude_apps.skills.aws_login.__main__.check_credentials_valid") as mock_check:
            mock_check.return_value = True  # Credentials are valid

            with patch("claude_apps.skills.aws_login.__main__.set_default_profile") as mock_default:
                with patch("claude_apps.skills.aws_login.__main__.poll_for_token") as mock_poll:
                    result = quick_auth_for_account("sandbox")

                    # Should not call poll_for_token since creds are valid
                    mock_poll.assert_not_called()
                    mock_default.assert_called_once_with("sandbox")
                    assert result is True

    def test_force_reauth_ignores_valid_credentials(self, monkeypatch, tmp_path):
        """Verify force=True ignores valid credentials."""
        monkeypatch.setenv("CLAUDE_PATH", str(tmp_path))
        monkeypatch.setenv("AWS_SSO_START_URL", "https://test.awsapps.com/start")

        mock_account = MagicMock()
        mock_account.account_id = "123456789012"
        mock_account.account_name = "Sandbox"

        with patch("claude_apps.skills.aws_login.__main__.check_credentials_valid") as mock_check:
            mock_check.return_value = True  # Credentials are valid

            with patch("claude_apps.skills.aws_login.__main__.poll_for_token") as mock_poll:
                mock_poll.return_value = MagicMock(success=True, access_token="test-token")

                with patch("claude_apps.skills.aws_login.__main__.discover_sso_accounts") as mock_discover:
                    mock_discover.return_value = [mock_account]

                    with patch("claude_apps.skills.aws_login.__main__.discover_account_roles") as mock_roles:
                        mock_roles.return_value = ["AdministratorAccess"]

                        with patch("claude_apps.skills.aws_login.__main__.get_role_credentials") as mock_creds:
                            mock_creds.return_value = MagicMock(
                                access_key_id="AKIATEST",
                                secret_access_key="secret",
                                session_token="token",
                                expiration=1234567890000,
                            )

                            with patch("claude_apps.skills.aws_login.__main__.ensure_profile"):
                                with patch("claude_apps.skills.aws_login.__main__.set_default_profile"):
                                    result = quick_auth_for_account("sandbox", force=True)

                            # Should call poll_for_token even though creds are valid
                            mock_poll.assert_called_once()
                            assert result is True


class TestCacheCredentialsForCli:
    """Tests for _cache_credentials_for_cli function."""

    def test_creates_cache_file(self, tmp_path, monkeypatch):
        """Verify cache file is created in correct location."""
        # Mock home directory
        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        mock_creds = MagicMock()
        mock_creds.access_key_id = "AKIATEST123"
        mock_creds.secret_access_key = "secret123"
        mock_creds.session_token = "token123"
        mock_creds.expiration = 1703001600000  # Unix timestamp in ms

        _cache_credentials_for_cli("test-profile", mock_creds)

        cache_file = tmp_path / ".aws" / "cli" / "cache" / "test-profile.json"
        assert cache_file.exists()

    def test_cache_file_format(self, tmp_path, monkeypatch):
        """Verify cache file has correct JSON structure."""
        import json

        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        mock_creds = MagicMock()
        mock_creds.access_key_id = "AKIATEST123"
        mock_creds.secret_access_key = "secret123"
        mock_creds.session_token = "token123"
        mock_creds.expiration = 1703001600000

        _cache_credentials_for_cli("test-profile", mock_creds)

        cache_file = tmp_path / ".aws" / "cli" / "cache" / "test-profile.json"
        data = json.loads(cache_file.read_text())

        assert "Credentials" in data
        assert data["Credentials"]["AccessKeyId"] == "AKIATEST123"
        assert data["Credentials"]["SecretAccessKey"] == "secret123"
        assert data["Credentials"]["SessionToken"] == "token123"
        assert "Expiration" in data["Credentials"]


class TestDiscoverSingleAccount:
    """Tests for discover_single_account function."""

    def test_returns_false_for_unknown_account(self, monkeypatch, tmp_path):
        """Verify False returned when account not found."""
        monkeypatch.setenv("CLAUDE_PATH", str(tmp_path))
        data_dir = tmp_path / ".data" / "aws"
        data_dir.mkdir(parents=True)
        (data_dir / "accounts.yml").write_text("""
accounts:
  production:
    id: '123456789012'
    name: Production
""")

        result = discover_single_account("unknown-account")

        assert result is False

    def test_returns_true_with_skip_vpc(self, monkeypatch, tmp_path):
        """Verify True returned when skip_vpc=True (auth only mode)."""
        monkeypatch.setenv("CLAUDE_PATH", str(tmp_path))
        data_dir = tmp_path / ".data" / "aws"
        data_dir.mkdir(parents=True)
        (data_dir / "accounts.yml").write_text("""
organization_id: o-test123
accounts:
  sandbox:
    id: '987654321098'
    name: Sandbox
    ou_path: root
""")

        result = discover_single_account("sandbox", skip_vpc=True)

        assert result is True

    def test_calls_discovery_functions(self, monkeypatch, tmp_path):
        """Verify discovery functions are called with correct params."""
        monkeypatch.setenv("CLAUDE_PATH", str(tmp_path))
        data_dir = tmp_path / ".data" / "aws"
        data_dir.mkdir(parents=True)
        (data_dir / "accounts.yml").write_text("""
organization_id: o-test123
accounts:
  sandbox:
    id: '987654321098'
    name: Sandbox
    ou_path: root
""")

        mock_inventory = MagicMock()
        mock_inventory.vpcs = []
        mock_inventory.s3_buckets = []
        mock_inventory.lambda_functions = []
        mock_inventory.rds_instances = []
        mock_inventory.rds_clusters = []
        mock_inventory.dynamodb_tables = []
        mock_inventory.ecs_clusters = []
        mock_inventory.eks_clusters = []

        with patch("claude_apps.skills.aws_login.discovery.discover_account_inventory") as mock_discover:
            mock_discover.return_value = mock_inventory

            with patch("claude_apps.shared.aws_utils.inventory.writer.save_inventory") as mock_save:
                with patch("claude_apps.shared.aws_utils.inventory.writer.get_relative_inventory_path") as mock_path:
                    mock_path.return_value = "o-test123/root/sandbox.yml"

                    result = discover_single_account("sandbox")

                    mock_discover.assert_called_once_with(
                        profile_name="sandbox",
                        region=None,
                        skip_resources=False,
                        is_mgmt_account=None,
                    )
                    mock_save.assert_called_once()
                    assert result is True
