"""Tests for GCP authentication operations."""

from unittest.mock import MagicMock, patch

import pytest

from claude_apps.skills.gcp_login.auth import (
    GCP_ALT_URL_PATTERN,
    GCP_URL_PATTERN,
    AuthResult,
    check_gcloud_installed,
    format_auth_prompt,
    get_current_account,
    get_current_project,
    run_auth,
    set_project,
    set_quota_project,
)


class TestAuthResult:
    """Tests for AuthResult dataclass."""

    def test_creation_success(self):
        """Test creating successful result."""
        result = AuthResult(
            success=True,
            auth_url="https://accounts.google.com/o/oauth2/auth?code=ABC",
            output="Authenticated successfully",
        )

        assert result.success is True
        assert result.auth_url == "https://accounts.google.com/o/oauth2/auth?code=ABC"
        assert result.output == "Authenticated successfully"
        assert result.error is None

    def test_creation_failure(self):
        """Test creating failure result."""
        result = AuthResult(
            success=False,
            error="gcloud not found",
        )

        assert result.success is False
        assert result.auth_url is None
        assert result.output == ""
        assert result.error == "gcloud not found"

    def test_defaults(self):
        """Test default values."""
        result = AuthResult(success=True)

        assert result.auth_url is None
        assert result.output == ""
        assert result.error is None


class TestUrlPatterns:
    """Tests for GCP URL regex patterns."""

    def test_gcp_url_pattern_matches_oauth(self):
        """Test GCP URL pattern matches OAuth URLs."""
        test_cases = [
            "https://accounts.google.com/o/oauth2/auth",
            "https://accounts.google.com/o/oauth2/auth?client_id=xyz",
            "https://accounts.google.com/o/oauth2/auth?response_type=code&scope=openid",
        ]

        for url in test_cases:
            match = GCP_URL_PATTERN.search(url)
            assert match is not None, f"Should match: {url}"
            assert match.group(1) == url

    def test_gcp_url_pattern_no_match(self):
        """Test GCP URL pattern doesn't match non-GCP URLs."""
        test_cases = [
            "https://google.com",
            "https://aws.amazon.com/oauth",
            "https://accounts.amazon.com/o/oauth2/auth",
            "not a url",
        ]

        for url in test_cases:
            match = GCP_URL_PATTERN.search(url)
            assert match is None, f"Should not match: {url}"

    def test_gcp_url_pattern_extracts_from_text(self):
        """Test extracts URL from surrounding text."""
        text = "Go to this URL: https://accounts.google.com/o/oauth2/auth?code=XYZ to authenticate"
        match = GCP_URL_PATTERN.search(text)

        assert match is not None
        assert match.group(1) == "https://accounts.google.com/o/oauth2/auth?code=XYZ"

    def test_alt_url_pattern_matches_google_domains(self):
        """Test alt URL pattern matches various Google domains."""
        # Pattern is r"(https://[\w.-]+\.google\.com/[^\s]*)"
        # Only matches *.google.com, not googleapis.com
        test_cases = [
            "https://cloud.google.com/auth",
            "https://api.google.com/oauth",
            "https://console.cloud.google.com/token",
        ]

        for url in test_cases:
            match = GCP_ALT_URL_PATTERN.search(url)
            assert match is not None, f"Should match: {url}"

    def test_alt_url_pattern_no_match_non_google(self):
        """Test alt URL pattern doesn't match non-Google URLs."""
        test_cases = [
            "https://aws.amazon.com",
            "https://github.com",
        ]

        for url in test_cases:
            match = GCP_ALT_URL_PATTERN.search(url)
            assert match is None, f"Should not match: {url}"


class TestCheckGcloudInstalled:
    """Tests for check_gcloud_installed function."""

    def test_returns_true_when_installed(self):
        """Test returns True when gcloud is found."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            result = check_gcloud_installed()

            assert result is True
            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert "which" in call_args
            assert "gcloud" in call_args

    def test_returns_false_when_not_installed(self):
        """Test returns False when gcloud is not found."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1)

            result = check_gcloud_installed()

            assert result is False

    def test_returns_false_on_exception(self):
        """Test returns False on subprocess exception."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("which not found")

            result = check_gcloud_installed()

            assert result is False


class TestGetCurrentAccount:
    """Tests for get_current_account function."""

    def test_returns_account_when_authenticated(self):
        """Test returns account email when authenticated."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="user@example.com\n",
            )

            result = get_current_account()

            assert result == "user@example.com"
            call_args = mock_run.call_args[0][0]
            assert "gcloud" in call_args
            assert "auth" in call_args
            assert "list" in call_args

    def test_returns_none_when_not_authenticated(self):
        """Test returns None when no active account."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="",
            )

            result = get_current_account()

            assert result is None

    def test_returns_none_on_error(self):
        """Test returns None on command error."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="")

            result = get_current_account()

            assert result is None

    def test_returns_none_on_exception(self):
        """Test returns None on exception."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = Exception("Command failed")

            result = get_current_account()

            assert result is None


class TestGetCurrentProject:
    """Tests for get_current_project function."""

    def test_returns_project_when_set(self):
        """Test returns project ID when configured."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="my-project-123\n",
            )

            result = get_current_project()

            assert result == "my-project-123"
            call_args = mock_run.call_args[0][0]
            assert "gcloud" in call_args
            assert "config" in call_args
            assert "get-value" in call_args
            assert "project" in call_args

    def test_returns_none_when_unset(self):
        """Test returns None when project is unset."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="(unset)\n",
            )

            result = get_current_project()

            assert result is None

    def test_returns_none_when_empty(self):
        """Test returns None when output is empty."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="",
            )

            result = get_current_project()

            assert result is None

    def test_returns_none_on_error(self):
        """Test returns None on command error."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="")

            result = get_current_project()

            assert result is None

    def test_returns_none_on_exception(self):
        """Test returns None on exception."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = Exception("Command failed")

            result = get_current_project()

            assert result is None


class TestSetProject:
    """Tests for set_project function."""

    def test_sets_project_successfully(self):
        """Test sets project and returns True."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            result = set_project("my-project")

            assert result is True
            call_args = mock_run.call_args[0][0]
            assert "gcloud" in call_args
            assert "config" in call_args
            assert "set" in call_args
            assert "project" in call_args
            assert "my-project" in call_args

    def test_returns_false_on_error(self):
        """Test returns False on command error."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1)

            result = set_project("invalid-project")

            assert result is False

    def test_returns_false_on_exception(self):
        """Test returns False on exception."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = Exception("Command failed")

            result = set_project("my-project")

            assert result is False


class TestSetQuotaProject:
    """Tests for set_quota_project function."""

    def test_sets_quota_project_successfully(self):
        """Test sets quota project and returns True."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            result = set_quota_project("quota-project")

            assert result is True
            call_args = mock_run.call_args[0][0]
            assert "gcloud" in call_args
            assert "auth" in call_args
            assert "application-default" in call_args
            assert "set-quota-project" in call_args
            assert "quota-project" in call_args

    def test_returns_false_on_error(self):
        """Test returns False on command error."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1)

            result = set_quota_project("invalid-project")

            assert result is False

    def test_returns_false_on_exception(self):
        """Test returns False on exception."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = Exception("Command failed")

            result = set_quota_project("project")

            assert result is False


class TestRunAuth:
    """Tests for run_auth function."""

    def test_captures_auth_url_from_output(self):
        """Test captures GCP auth URL from output."""
        mock_output = [
            "Go to the following link in your browser:\n",
            "https://accounts.google.com/o/oauth2/auth?client_id=xyz\n",
            "Enter authorization code:\n",
            "You are now logged in\n",
        ]

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.stdout = iter(mock_output)
            mock_process.returncode = 0
            mock_process.wait.return_value = 0
            mock_popen.return_value = mock_process

            result = run_auth(no_browser=True)

            assert result.success is True
            assert result.auth_url == "https://accounts.google.com/o/oauth2/auth?client_id=xyz"
            assert "logged in" in result.output

    def test_uses_no_launch_browser_flag(self):
        """Test uses --no-launch-browser when no_browser=True."""
        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.stdout = iter([])
            mock_process.returncode = 0
            mock_process.wait.return_value = 0
            mock_popen.return_value = mock_process

            run_auth(no_browser=True)

            call_args = mock_popen.call_args[0][0]
            assert "--no-launch-browser" in call_args

    def test_omits_no_browser_flag_when_false(self):
        """Test omits --no-launch-browser when no_browser=False."""
        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.stdout = iter([])
            mock_process.returncode = 0
            mock_process.wait.return_value = 0
            mock_popen.return_value = mock_process

            run_auth(no_browser=False)

            call_args = mock_popen.call_args[0][0]
            assert "--no-launch-browser" not in call_args

    def test_includes_update_adc_flag(self):
        """Test includes --update-adc flag."""
        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.stdout = iter([])
            mock_process.returncode = 0
            mock_process.wait.return_value = 0
            mock_popen.return_value = mock_process

            run_auth()

            call_args = mock_popen.call_args[0][0]
            assert "--update-adc" in call_args

    def test_returns_failure_on_nonzero_exit(self):
        """Test returns failure when auth fails."""
        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.stdout = iter(["Error: Authentication failed\n"])
            mock_process.returncode = 1
            mock_process.wait.return_value = 1
            mock_popen.return_value = mock_process

            result = run_auth()

            assert result.success is False

    def test_returns_failure_on_exception(self):
        """Test returns failure on exception."""
        with patch("subprocess.Popen") as mock_popen:
            mock_popen.side_effect = Exception("Command not found")

            result = run_auth()

            assert result.success is False
            assert result.error == "Command not found"

    def test_captures_alt_url_pattern_with_oauth(self):
        """Test captures alt URL pattern when oauth in context."""
        mock_output = [
            "oauth authentication required\n",
            "Visit: https://cloud.google.com/auth/oauth2\n",
        ]

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.stdout = iter(mock_output)
            mock_process.returncode = 0
            mock_process.wait.return_value = 0
            mock_popen.return_value = mock_process

            result = run_auth()

            assert result.success is True
            assert result.auth_url == "https://cloud.google.com/auth/oauth2"


class TestFormatAuthPrompt:
    """Tests for format_auth_prompt function."""

    def test_formats_full_prompt_with_url(self):
        """Test formats prompt with URL."""
        result = AuthResult(
            success=True,
            auth_url="https://accounts.google.com/o/oauth2/auth?code=ABC",
        )

        formatted = format_auth_prompt(result)

        assert "**GCP Authentication Required**" in formatted
        assert "https://accounts.google.com/o/oauth2/auth?code=ABC" in formatted
        assert "| URL |" in formatted

    def test_returns_empty_when_no_url(self):
        """Test returns empty string when no URL."""
        result = AuthResult(success=True)

        formatted = format_auth_prompt(result)

        assert formatted == ""

    def test_returns_empty_for_failed_result(self):
        """Test returns empty for failed result without URL."""
        result = AuthResult(success=False, error="Failed")

        formatted = format_auth_prompt(result)

        assert formatted == ""
