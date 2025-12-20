"""Tests for AWS SSO login operations."""

from unittest.mock import patch, MagicMock
import subprocess

import pytest

from claude_apps.skills.aws_login.sso import (
    DEVICE_CODE_PATTERN,
    SSO_URL_PATTERN,
    SSOResult,
    check_credentials_valid,
    format_sso_prompt,
    run_sso_login,
)


class TestSSOResult:
    """Tests for SSOResult dataclass."""

    def test_creation_success(self):
        """Test creating successful result."""
        result = SSOResult(
            success=True,
            sso_url="https://test.awsapps.com/start",
            device_code="ABCD-EFGH",
            output="Logged in successfully",
        )

        assert result.success is True
        assert result.sso_url == "https://test.awsapps.com/start"
        assert result.device_code == "ABCD-EFGH"
        assert result.error is None

    def test_creation_failure(self):
        """Test creating failure result."""
        result = SSOResult(
            success=False,
            error="Connection refused",
        )

        assert result.success is False
        assert result.error == "Connection refused"


class TestPatterns:
    """Tests for regex patterns."""

    def test_sso_url_pattern_matches(self):
        """Test SSO URL pattern matches valid URLs."""
        test_cases = [
            "https://my-org.awsapps.com/start",
            "https://d-abc123.awsapps.com/start#/",
            "https://test.awsapps.com/start?user_code=XXXX-YYYY",
        ]

        for url in test_cases:
            match = SSO_URL_PATTERN.search(url)
            assert match is not None, f"Should match: {url}"

    def test_sso_url_pattern_no_match(self):
        """Test SSO URL pattern doesn't match invalid URLs."""
        test_cases = [
            "https://google.com",
            "https://aws.amazon.com",
            "not a url",
        ]

        for url in test_cases:
            match = SSO_URL_PATTERN.search(url)
            assert match is None, f"Should not match: {url}"

    def test_device_code_pattern_matches(self):
        """Test device code pattern matches valid codes."""
        test_cases = [
            "ABCD-EFGH",
            "WXYZ-MNOP",
            "Enter code: QRST-UVWX",
        ]

        for text in test_cases:
            match = DEVICE_CODE_PATTERN.search(text)
            assert match is not None, f"Should match: {text}"

    def test_device_code_pattern_no_match(self):
        """Test device code pattern doesn't match invalid codes."""
        test_cases = [
            "abcd-efgh",  # lowercase
            "ABCD1234",   # no hyphen
            "ABC-DEF",    # wrong length
        ]

        for text in test_cases:
            match = DEVICE_CODE_PATTERN.search(text)
            assert match is None, f"Should not match: {text}"


class TestCheckCredentialsValid:
    """Tests for check_credentials_valid function."""

    def test_returns_true_when_valid(self):
        """Test returns True when credentials are valid."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="")

            result = check_credentials_valid("test-profile")

            assert result is True
            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert "--profile" in call_args
            assert "test-profile" in call_args

    def test_returns_false_when_invalid(self):
        """Test returns False when credentials are invalid."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stderr="ExpiredToken: The security token included in the request is expired",
            )

            result = check_credentials_valid("expired-profile")

            assert result is False

    def test_returns_false_on_error(self):
        """Test returns False on execution error."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=255,
                stderr="Unable to locate credentials",
            )

            result = check_credentials_valid("missing-profile")

            assert result is False


class TestRunSsoLogin:
    """Tests for run_sso_login function."""

    def test_captures_url_and_code(self):
        """Test captures SSO URL and device code from output."""
        mock_output = [
            "Attempting to automatically open the SSO authorization page\n",
            "If the browser does not open, visit:\n",
            "https://device.sso.us-east-1.amazonaws.com/\n",
            "Then enter the code: ABCD-EFGH\n",
            "Successfully logged in\n",
        ]

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.stdout = iter(mock_output)
            mock_process.returncode = 0
            mock_process.wait.return_value = 0
            mock_popen.return_value = mock_process

            result = run_sso_login("test-profile", no_browser=True)

            assert result.success is True
            assert result.device_code == "ABCD-EFGH"

    def test_returns_failure_on_error(self):
        """Test returns failure when login fails."""
        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.stdout = iter(["Error: Profile not configured\n"])
            mock_process.returncode = 1
            mock_process.wait.return_value = 1
            mock_popen.return_value = mock_process

            result = run_sso_login("invalid-profile")

            assert result.success is False

    def test_handles_exception(self):
        """Test handles subprocess exception."""
        with patch("subprocess.Popen") as mock_popen:
            mock_popen.side_effect = Exception("Command not found")

            result = run_sso_login("test-profile")

            assert result.success is False
            assert result.error == "Command not found"

    def test_uses_no_browser_flag(self):
        """Test uses --no-browser flag when specified."""
        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.stdout = iter([])
            mock_process.returncode = 0
            mock_process.wait.return_value = 0
            mock_popen.return_value = mock_process

            run_sso_login("test", no_browser=True)

            call_args = mock_popen.call_args[0][0]
            assert "--no-browser" in call_args

    def test_omits_no_browser_flag(self):
        """Test omits --no-browser flag when False."""
        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.stdout = iter([])
            mock_process.returncode = 0
            mock_process.wait.return_value = 0
            mock_popen.return_value = mock_process

            run_sso_login("test", no_browser=False)

            call_args = mock_popen.call_args[0][0]
            assert "--no-browser" not in call_args


class TestFormatSsoPrompt:
    """Tests for format_sso_prompt function."""

    def test_formats_full_prompt(self):
        """Test formats prompt with URL and code."""
        result = SSOResult(
            success=True,
            sso_url="https://device.sso.us-east-1.amazonaws.com/",
            device_code="WXYZ-MNOP",
        )

        formatted = format_sso_prompt(result)

        assert "**AWS SSO Authentication Required**" in formatted
        assert "https://device.sso.us-east-1.amazonaws.com/" in formatted
        assert "WXYZ-MNOP" in formatted
        assert "| URL |" in formatted
        assert "| Code |" in formatted

    def test_formats_url_only(self):
        """Test formats prompt with URL only."""
        result = SSOResult(
            success=True,
            sso_url="https://test.awsapps.com/start",
        )

        formatted = format_sso_prompt(result)

        assert "https://test.awsapps.com/start" in formatted
        # No code row when device_code is None
        assert "| Code |" not in formatted

    def test_returns_empty_for_no_url(self):
        """Test returns empty string when no URL."""
        result = SSOResult(success=False, error="Failed")

        formatted = format_sso_prompt(result)

        assert formatted == ""
