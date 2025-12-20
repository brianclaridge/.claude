"""Tests for GCP login CLI entry point."""

from unittest.mock import MagicMock, patch

import pytest

from claude_apps.skills.gcp_login.__main__ import main, setup_logging
from claude_apps.skills.gcp_login.auth import AuthResult


@pytest.fixture(autouse=True)
def mock_logger_success():
    """Mock logger.success since structlog doesn't have it by default."""
    with patch("claude_apps.skills.gcp_login.__main__.logger") as mock_logger:
        # Make logger behave like a real logger for all standard methods
        mock_logger.info = MagicMock()
        mock_logger.debug = MagicMock()
        mock_logger.error = MagicMock()
        mock_logger.success = MagicMock()
        yield mock_logger


class TestSetupLogging:
    """Tests for setup_logging function."""

    def test_configures_debug_level_when_verbose(self):
        """Test configures DEBUG level when verbose=True."""
        with patch("structlog.configure") as mock_configure:
            with patch("structlog.make_filtering_bound_logger") as mock_make_logger:
                setup_logging(verbose=True)

                mock_make_logger.assert_called_once_with(10)  # DEBUG=10

    def test_configures_info_level_when_not_verbose(self):
        """Test configures INFO level when verbose=False."""
        with patch("structlog.configure") as mock_configure:
            with patch("structlog.make_filtering_bound_logger") as mock_make_logger:
                setup_logging(verbose=False)

                mock_make_logger.assert_called_once_with(20)  # INFO=20


class TestMain:
    """Tests for main CLI function."""

    def test_exits_with_error_when_gcloud_not_installed(self):
        """Test exits with error when gcloud CLI not found."""
        with patch("claude_apps.skills.gcp_login.__main__.check_gcloud_installed") as mock_check:
            mock_check.return_value = False
            with patch("sys.argv", ["gcp-auth"]):
                result = main()

                assert result == 1

    def test_exits_success_when_already_authenticated(self):
        """Test exits 0 when already authenticated and not forced."""
        with patch("claude_apps.skills.gcp_login.__main__.check_gcloud_installed") as mock_gcloud:
            mock_gcloud.return_value = True
            with patch("claude_apps.skills.gcp_login.__main__.get_current_account") as mock_account:
                mock_account.return_value = "user@example.com"
                with patch("claude_apps.skills.gcp_login.__main__.get_current_project") as mock_project:
                    mock_project.return_value = "my-project"
                    with patch("sys.argv", ["gcp-auth"]):
                        result = main()

                        assert result == 0

    def test_runs_auth_when_forced(self):
        """Test runs auth when --force is specified."""
        with patch("claude_apps.skills.gcp_login.__main__.check_gcloud_installed") as mock_gcloud:
            mock_gcloud.return_value = True
            with patch("claude_apps.skills.gcp_login.__main__.get_current_account") as mock_account:
                mock_account.return_value = "user@example.com"
                with patch("claude_apps.skills.gcp_login.__main__.get_current_project") as mock_project:
                    mock_project.return_value = "my-project"
                    with patch("claude_apps.skills.gcp_login.__main__.run_auth") as mock_auth:
                        mock_auth.return_value = AuthResult(success=True)
                        with patch("sys.argv", ["gcp-auth", "--force"]):
                            result = main()

                            mock_auth.assert_called_once()

    def test_runs_auth_when_not_authenticated(self):
        """Test runs auth when no current account."""
        with patch("claude_apps.skills.gcp_login.__main__.check_gcloud_installed") as mock_gcloud:
            mock_gcloud.return_value = True
            with patch("claude_apps.skills.gcp_login.__main__.get_current_account") as mock_account:
                mock_account.return_value = None
                with patch("claude_apps.skills.gcp_login.__main__.get_current_project") as mock_project:
                    mock_project.return_value = None
                    with patch("claude_apps.skills.gcp_login.__main__.run_auth") as mock_auth:
                        mock_auth.return_value = AuthResult(success=True)
                        with patch("sys.argv", ["gcp-auth"]):
                            result = main()

                            mock_auth.assert_called_once()

    def test_sets_project_from_environment(self, monkeypatch):
        """Test sets project from GOOGLE_CLOUD_PROJECT env var."""
        monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "env-project")

        with patch("claude_apps.skills.gcp_login.__main__.check_gcloud_installed") as mock_gcloud:
            mock_gcloud.return_value = True
            with patch("claude_apps.skills.gcp_login.__main__.get_current_account") as mock_account:
                mock_account.return_value = None
                with patch("claude_apps.skills.gcp_login.__main__.get_current_project") as mock_project:
                    mock_project.return_value = None
                    with patch("claude_apps.skills.gcp_login.__main__.set_project") as mock_set_project:
                        with patch("claude_apps.skills.gcp_login.__main__.set_quota_project") as mock_set_quota:
                            with patch("claude_apps.skills.gcp_login.__main__.run_auth") as mock_auth:
                                mock_auth.return_value = AuthResult(success=True)
                                with patch("sys.argv", ["gcp-auth"]):
                                    main()

                                    mock_set_project.assert_called_once_with("env-project")
                                    mock_set_quota.assert_called_once_with("env-project")

    def test_returns_zero_on_auth_success(self):
        """Test returns 0 on successful auth."""
        with patch("claude_apps.skills.gcp_login.__main__.check_gcloud_installed") as mock_gcloud:
            mock_gcloud.return_value = True
            with patch("claude_apps.skills.gcp_login.__main__.get_current_account") as mock_account:
                # First call: not authenticated, second call: after auth
                mock_account.side_effect = [None, "user@example.com"]
                with patch("claude_apps.skills.gcp_login.__main__.get_current_project") as mock_project:
                    mock_project.side_effect = [None, "my-project"]
                    with patch("claude_apps.skills.gcp_login.__main__.run_auth") as mock_auth:
                        mock_auth.return_value = AuthResult(success=True)
                        with patch("sys.argv", ["gcp-auth"]):
                            result = main()

                            assert result == 0

    def test_returns_one_on_auth_failure(self):
        """Test returns 1 on auth failure."""
        with patch("claude_apps.skills.gcp_login.__main__.check_gcloud_installed") as mock_gcloud:
            mock_gcloud.return_value = True
            with patch("claude_apps.skills.gcp_login.__main__.get_current_account") as mock_account:
                mock_account.return_value = None
                with patch("claude_apps.skills.gcp_login.__main__.get_current_project") as mock_project:
                    mock_project.return_value = None
                    with patch("claude_apps.skills.gcp_login.__main__.run_auth") as mock_auth:
                        mock_auth.return_value = AuthResult(success=False, error="Failed")
                        with patch("sys.argv", ["gcp-auth"]):
                            result = main()

                            assert result == 1

    def test_force_flag_short_form(self):
        """Test -f short form for --force."""
        with patch("claude_apps.skills.gcp_login.__main__.check_gcloud_installed") as mock_gcloud:
            mock_gcloud.return_value = True
            with patch("claude_apps.skills.gcp_login.__main__.get_current_account") as mock_account:
                mock_account.return_value = "user@example.com"
                with patch("claude_apps.skills.gcp_login.__main__.get_current_project") as mock_project:
                    mock_project.return_value = "project"
                    with patch("claude_apps.skills.gcp_login.__main__.run_auth") as mock_auth:
                        mock_auth.return_value = AuthResult(success=True)
                        with patch("sys.argv", ["gcp-auth", "-f"]):
                            main()

                            mock_auth.assert_called_once()

    def test_verbose_flag_enables_debug(self):
        """Test --verbose enables debug logging."""
        with patch("claude_apps.skills.gcp_login.__main__.setup_logging") as mock_logging:
            with patch("claude_apps.skills.gcp_login.__main__.check_gcloud_installed") as mock_gcloud:
                mock_gcloud.return_value = False
                with patch("sys.argv", ["gcp-auth", "--verbose"]):
                    main()

                    mock_logging.assert_called_once_with(True)

    def test_verbose_flag_short_form(self):
        """Test -v short form for --verbose."""
        with patch("claude_apps.skills.gcp_login.__main__.setup_logging") as mock_logging:
            with patch("claude_apps.skills.gcp_login.__main__.check_gcloud_installed") as mock_gcloud:
                mock_gcloud.return_value = False
                with patch("sys.argv", ["gcp-auth", "-v"]):
                    main()

                    mock_logging.assert_called_once_with(True)

    def test_exits_success_without_project(self):
        """Test exits 0 when authenticated without project."""
        with patch("claude_apps.skills.gcp_login.__main__.check_gcloud_installed") as mock_gcloud:
            mock_gcloud.return_value = True
            with patch("claude_apps.skills.gcp_login.__main__.get_current_account") as mock_account:
                mock_account.return_value = "user@example.com"
                with patch("claude_apps.skills.gcp_login.__main__.get_current_project") as mock_project:
                    mock_project.return_value = None  # No project set
                    with patch("sys.argv", ["gcp-auth"]):
                        result = main()

                        assert result == 0

    def test_does_not_set_project_when_env_not_set(self, monkeypatch):
        """Test does not call set_project when env var not set."""
        monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)

        with patch("claude_apps.skills.gcp_login.__main__.check_gcloud_installed") as mock_gcloud:
            mock_gcloud.return_value = True
            with patch("claude_apps.skills.gcp_login.__main__.get_current_account") as mock_account:
                mock_account.return_value = None
                with patch("claude_apps.skills.gcp_login.__main__.get_current_project") as mock_project:
                    mock_project.return_value = None
                    with patch("claude_apps.skills.gcp_login.__main__.set_project") as mock_set_project:
                        with patch("claude_apps.skills.gcp_login.__main__.run_auth") as mock_auth:
                            mock_auth.return_value = AuthResult(success=True)
                            with patch("sys.argv", ["gcp-auth"]):
                                main()

                                mock_set_project.assert_not_called()
