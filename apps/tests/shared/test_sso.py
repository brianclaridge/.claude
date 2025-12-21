"""Tests for AWS SSO service functions in shared/aws_utils."""

from unittest.mock import patch, MagicMock

import pytest
from botocore.exceptions import ClientError

from claude_apps.shared.aws_utils.services.sso import (
    get_role_credentials,
    RoleCredentials,
    get_sso_region,
)


class TestGetSsoRegion:
    """Tests for get_sso_region function."""

    def test_returns_env_var(self, monkeypatch):
        """Test returns value from AWS_SSO_REGION."""
        monkeypatch.setenv("AWS_SSO_REGION", "eu-west-1")

        result = get_sso_region()

        assert result == "eu-west-1"

    def test_returns_default(self, monkeypatch):
        """Test returns us-east-1 as default."""
        monkeypatch.delenv("AWS_SSO_REGION", raising=False)

        result = get_sso_region()

        assert result == "us-east-1"


class TestRoleCredentials:
    """Tests for RoleCredentials dataclass."""

    def test_creation(self):
        """Test creating RoleCredentials."""
        creds = RoleCredentials(
            access_key_id="AKIATEST",
            secret_access_key="secret",
            session_token="token",
            expiration=1234567890000,
        )

        assert creds.access_key_id == "AKIATEST"
        assert creds.secret_access_key == "secret"
        assert creds.session_token == "token"
        assert creds.expiration == 1234567890000


class TestGetRoleCredentials:
    """Tests for get_role_credentials function."""

    def test_uses_existing_token(self, monkeypatch):
        """Verify GetRoleCredentials API called with access token."""
        monkeypatch.delenv("AWS_SSO_REGION", raising=False)

        with patch("boto3.client") as mock_client:
            mock_sso = MagicMock()
            mock_sso.get_role_credentials.return_value = {
                "roleCredentials": {
                    "accessKeyId": "AKIATEST123",
                    "secretAccessKey": "secret123",
                    "sessionToken": "token123",
                    "expiration": 1703001600000,
                }
            }
            mock_client.return_value = mock_sso

            result = get_role_credentials(
                access_token="existing-sso-token",
                account_id="123456789012",
                role_name="AdministratorAccess",
            )

            # Verify SSO client was created
            mock_client.assert_called_once_with("sso", region_name="us-east-1")

            # Verify get_role_credentials was called with correct params
            mock_sso.get_role_credentials.assert_called_once_with(
                accessToken="existing-sso-token",
                accountId="123456789012",
                roleName="AdministratorAccess",
            )

            assert result is not None

    def test_returns_credentials(self, monkeypatch):
        """Verify credentials dict returned correctly."""
        monkeypatch.setenv("AWS_SSO_REGION", "eu-west-1")

        with patch("boto3.client") as mock_client:
            mock_sso = MagicMock()
            mock_sso.get_role_credentials.return_value = {
                "roleCredentials": {
                    "accessKeyId": "AKIATEST123",
                    "secretAccessKey": "secret123",
                    "sessionToken": "token123",
                    "expiration": 1703001600000,
                }
            }
            mock_client.return_value = mock_sso

            result = get_role_credentials(
                access_token="token",
                account_id="123456789012",
                role_name="AdministratorAccess",
            )

            assert isinstance(result, RoleCredentials)
            assert result.access_key_id == "AKIATEST123"
            assert result.secret_access_key == "secret123"
            assert result.session_token == "token123"
            assert result.expiration == 1703001600000

    def test_handles_expired_token(self, monkeypatch):
        """Verify graceful handling of expired tokens."""
        monkeypatch.delenv("AWS_SSO_REGION", raising=False)

        with patch("boto3.client") as mock_client:
            mock_sso = MagicMock()
            error_response = {
                "Error": {
                    "Code": "UnauthorizedException",
                    "Message": "The security token included in the request is expired",
                }
            }
            mock_sso.get_role_credentials.side_effect = ClientError(
                error_response, "GetRoleCredentials"
            )
            mock_client.return_value = mock_sso

            result = get_role_credentials(
                access_token="expired-token",
                account_id="123456789012",
                role_name="AdministratorAccess",
            )

            assert result is None

    def test_handles_forbidden(self, monkeypatch):
        """Verify handling when role access is denied."""
        monkeypatch.delenv("AWS_SSO_REGION", raising=False)

        with patch("boto3.client") as mock_client:
            mock_sso = MagicMock()
            error_response = {
                "Error": {
                    "Code": "ForbiddenException",
                    "Message": "User not authorized for this role",
                }
            }
            mock_sso.get_role_credentials.side_effect = ClientError(
                error_response, "GetRoleCredentials"
            )
            mock_client.return_value = mock_sso

            result = get_role_credentials(
                access_token="valid-token",
                account_id="123456789012",
                role_name="RestrictedRole",
            )

            assert result is None

    def test_uses_custom_region(self, monkeypatch):
        """Verify custom region parameter is used."""
        monkeypatch.delenv("AWS_SSO_REGION", raising=False)

        with patch("boto3.client") as mock_client:
            mock_sso = MagicMock()
            mock_sso.get_role_credentials.return_value = {
                "roleCredentials": {
                    "accessKeyId": "AKIATEST",
                    "secretAccessKey": "secret",
                    "sessionToken": "token",
                    "expiration": 1234567890000,
                }
            }
            mock_client.return_value = mock_sso

            get_role_credentials(
                access_token="token",
                account_id="123456789012",
                role_name="AdministratorAccess",
                region="ap-southeast-1",
            )

            mock_client.assert_called_once_with("sso", region_name="ap-southeast-1")

    def test_returns_none_for_empty_credentials(self, monkeypatch):
        """Verify None returned when credentials dict is empty."""
        monkeypatch.delenv("AWS_SSO_REGION", raising=False)

        with patch("boto3.client") as mock_client:
            mock_sso = MagicMock()
            mock_sso.get_role_credentials.return_value = {"roleCredentials": {}}
            mock_client.return_value = mock_sso

            result = get_role_credentials(
                access_token="token",
                account_id="123456789012",
                role_name="AdministratorAccess",
            )

            assert result is None
