"""Tests for AWS SSO configuration."""

import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import yaml

from claude_apps.skills.aws_login.config import (
    clear_aws_data,
    config_exists,
    get_account,
    get_accounts_path,
    get_aws_data_path,
    get_claude_path,
    get_default_region,
    get_global_config,
    get_management_account_id,
    get_manager_account,
    get_root_account_id,
    get_root_account_name,
    get_sso_region,
    get_sso_role_name,
    get_sso_start_url,
    inventory_exists,
    list_accounts,
    load_accounts,
    load_config,
    save_config,
)


class TestGetClaudePath:
    """Tests for get_claude_path function."""

    def test_returns_env_var_path(self, monkeypatch, tmp_path):
        """Test returns path from CLAUDE_PATH env var."""
        monkeypatch.setenv("CLAUDE_PATH", str(tmp_path))

        result = get_claude_path()

        assert result == tmp_path

    def test_returns_fallback_path(self, monkeypatch):
        """Test returns fallback path when env var not set."""
        monkeypatch.delenv("CLAUDE_PATH", raising=False)

        result = get_claude_path()

        # Fallback is relative to source file
        assert isinstance(result, Path)


class TestGetGlobalConfig:
    """Tests for get_global_config function."""

    def test_loads_config_from_file(self, monkeypatch, tmp_path):
        """Test loads config.yml."""
        monkeypatch.setenv("CLAUDE_PATH", str(tmp_path))
        config_file = tmp_path / "config.yml"
        config_file.write_text("cloud_providers:\n  aws:\n    data_path: custom/path")

        result = get_global_config()

        assert result["cloud_providers"]["aws"]["data_path"] == "custom/path"

    def test_returns_empty_for_missing_file(self, monkeypatch, tmp_path):
        """Test returns empty dict when config.yml doesn't exist."""
        monkeypatch.setenv("CLAUDE_PATH", str(tmp_path))

        result = get_global_config()

        assert result == {}


class TestGetAwsDataPath:
    """Tests for get_aws_data_path function."""

    def test_uses_config_path(self, monkeypatch, tmp_path):
        """Test uses path from config.yml."""
        monkeypatch.setenv("CLAUDE_PATH", str(tmp_path))
        config_file = tmp_path / "config.yml"
        config_file.write_text("cloud_providers:\n  aws:\n    data_path: custom/aws")

        result = get_aws_data_path()

        assert result == tmp_path / "custom/aws"

    def test_uses_default_path(self, monkeypatch, tmp_path):
        """Test uses default .data/aws when not configured."""
        monkeypatch.setenv("CLAUDE_PATH", str(tmp_path))

        result = get_aws_data_path()

        assert result == tmp_path / ".data/aws"


class TestEnvironmentVariables:
    """Tests for environment variable getters."""

    def test_get_sso_start_url(self, monkeypatch):
        """Test gets SSO URL from env."""
        monkeypatch.setenv("AWS_SSO_START_URL", "https://my-org.awsapps.com/start")

        result = get_sso_start_url()

        assert result == "https://my-org.awsapps.com/start"

    def test_get_sso_start_url_adds_https(self, monkeypatch):
        """Test adds https prefix if missing."""
        monkeypatch.setenv("AWS_SSO_START_URL", "my-org.awsapps.com/start")

        result = get_sso_start_url()

        assert result == "https://my-org.awsapps.com/start"

    def test_get_sso_start_url_raises_when_missing(self, monkeypatch):
        """Test raises ValueError when SSO URL not set."""
        monkeypatch.delenv("AWS_SSO_START_URL", raising=False)

        with pytest.raises(ValueError, match="AWS_SSO_START_URL not set"):
            get_sso_start_url()

    def test_get_root_account_id(self, monkeypatch):
        """Test gets root account ID from env."""
        monkeypatch.setenv("AWS_ROOT_ACCOUNT_ID", "123456789012")

        result = get_root_account_id()

        assert result == "123456789012"

    def test_get_root_account_id_returns_none(self, monkeypatch):
        """Test returns None when not set."""
        monkeypatch.delenv("AWS_ROOT_ACCOUNT_ID", raising=False)

        result = get_root_account_id()

        assert result is None

    def test_get_root_account_name(self, monkeypatch):
        """Test gets root account name from env."""
        monkeypatch.setenv("AWS_ROOT_ACCOUNT_NAME", "Management")

        result = get_root_account_name()

        assert result == "Management"

    def test_get_default_region(self, monkeypatch):
        """Test gets default region from env."""
        monkeypatch.setenv("AWS_DEFAULT_REGION", "eu-west-1")

        result = get_default_region()

        assert result == "eu-west-1"

    def test_get_default_region_uses_default(self, monkeypatch):
        """Test uses us-east-1 as default."""
        monkeypatch.delenv("AWS_DEFAULT_REGION", raising=False)

        result = get_default_region()

        assert result == "us-east-1"

    def test_get_sso_region(self, monkeypatch):
        """Test gets SSO region from env."""
        monkeypatch.setenv("AWS_SSO_REGION", "eu-west-1")

        result = get_sso_region()

        assert result == "eu-west-1"

    def test_get_sso_role_name(self, monkeypatch):
        """Test gets SSO role from env."""
        monkeypatch.setenv("AWS_SSO_ROLE_NAME", "PowerUserAccess")

        result = get_sso_role_name()

        assert result == "PowerUserAccess"

    def test_get_sso_role_name_default(self, monkeypatch):
        """Test uses AdministratorAccess as default."""
        monkeypatch.delenv("AWS_SSO_ROLE_NAME", raising=False)

        result = get_sso_role_name()

        assert result == "AdministratorAccess"


class TestConfigIO:
    """Tests for configuration I/O functions."""

    def test_config_exists_true(self, monkeypatch, tmp_path):
        """Test config_exists returns True when file exists."""
        monkeypatch.setenv("CLAUDE_PATH", str(tmp_path))
        data_dir = tmp_path / ".data" / "aws"
        data_dir.mkdir(parents=True)
        (data_dir / "accounts.yml").write_text("schema_version: '1.0'")

        assert config_exists() is True

    def test_config_exists_false(self, monkeypatch, tmp_path):
        """Test config_exists returns False when file missing."""
        monkeypatch.setenv("CLAUDE_PATH", str(tmp_path))

        assert config_exists() is False

    def test_load_config(self, monkeypatch, tmp_path):
        """Test loading accounts.yml."""
        monkeypatch.setenv("CLAUDE_PATH", str(tmp_path))
        data_dir = tmp_path / ".data" / "aws"
        data_dir.mkdir(parents=True)
        (data_dir / "accounts.yml").write_text("""
schema_version: '1.0'
organization_id: o-abc123
accounts:
  root:
    id: '123456789012'
    name: Management
""")

        result = load_config()

        assert result["schema_version"] == "1.0"
        assert result["organization_id"] == "o-abc123"
        assert "root" in result["accounts"]

    def test_load_config_raises_when_missing(self, monkeypatch, tmp_path):
        """Test raises FileNotFoundError when file missing."""
        monkeypatch.setenv("CLAUDE_PATH", str(tmp_path))

        with pytest.raises(FileNotFoundError):
            load_config()

    def test_save_config(self, monkeypatch, tmp_path):
        """Test saving accounts.yml."""
        monkeypatch.setenv("CLAUDE_PATH", str(tmp_path))
        monkeypatch.setenv("AWS_SSO_START_URL", "https://test.awsapps.com/start")
        monkeypatch.setenv("AWS_DEFAULT_REGION", "us-west-2")

        accounts = {
            "sandbox": {
                "id": "987654321098",
                "name": "Sandbox",
            }
        }

        save_config(accounts, "o-test123", "123456789012")

        saved = yaml.safe_load((tmp_path / ".data" / "aws" / "accounts.yml").read_text())
        assert saved["organization_id"] == "o-test123"
        assert saved["management_account_id"] == "123456789012"
        assert "sandbox" in saved["accounts"]


class TestAccountOperations:
    """Tests for account operations."""

    def test_load_accounts(self, monkeypatch, tmp_path):
        """Test loading accounts dict."""
        monkeypatch.setenv("CLAUDE_PATH", str(tmp_path))
        data_dir = tmp_path / ".data" / "aws"
        data_dir.mkdir(parents=True)
        (data_dir / "accounts.yml").write_text("""
accounts:
  root:
    id: '123'
  sandbox:
    id: '456'
""")

        result = load_accounts()

        assert len(result) == 2
        assert result["root"]["id"] == "123"

    def test_load_accounts_returns_empty(self, monkeypatch, tmp_path):
        """Test returns empty dict when no config."""
        monkeypatch.setenv("CLAUDE_PATH", str(tmp_path))

        result = load_accounts()

        assert result == {}

    def test_get_account(self, monkeypatch, tmp_path):
        """Test getting account by alias."""
        monkeypatch.setenv("CLAUDE_PATH", str(tmp_path))
        data_dir = tmp_path / ".data" / "aws"
        data_dir.mkdir(parents=True)
        (data_dir / "accounts.yml").write_text("""
accounts:
  sandbox:
    id: '456'
    name: Sandbox Account
""")

        result = get_account("sandbox")

        assert result["id"] == "456"
        assert result["name"] == "Sandbox Account"

    def test_get_account_raises_for_unknown(self, monkeypatch, tmp_path):
        """Test raises ValueError for unknown alias."""
        monkeypatch.setenv("CLAUDE_PATH", str(tmp_path))
        data_dir = tmp_path / ".data" / "aws"
        data_dir.mkdir(parents=True)
        (data_dir / "accounts.yml").write_text("""
accounts:
  sandbox:
    id: '456'
""")

        with pytest.raises(ValueError, match="Account 'unknown' not found"):
            get_account("unknown")

    def test_list_accounts(self, monkeypatch, tmp_path):
        """Test listing all accounts."""
        monkeypatch.setenv("CLAUDE_PATH", str(tmp_path))
        data_dir = tmp_path / ".data" / "aws"
        data_dir.mkdir(parents=True)
        (data_dir / "accounts.yml").write_text("""
accounts:
  beta:
    id: '222'
  alpha:
    id: '111'
""")

        result = list_accounts()

        # Should be sorted by alias
        assert len(result) == 2
        assert result[0]["alias"] == "alpha"
        assert result[1]["alias"] == "beta"

    def test_get_management_account_id(self, monkeypatch, tmp_path):
        """Test getting management account ID."""
        monkeypatch.setenv("CLAUDE_PATH", str(tmp_path))
        data_dir = tmp_path / ".data" / "aws"
        data_dir.mkdir(parents=True)
        (data_dir / "accounts.yml").write_text("""
management_account_id: '123456789012'
accounts: {}
""")

        result = get_management_account_id()

        assert result == "123456789012"

    def test_get_manager_account(self, monkeypatch, tmp_path):
        """Test getting manager account by is_manager flag."""
        monkeypatch.setenv("CLAUDE_PATH", str(tmp_path))
        data_dir = tmp_path / ".data" / "aws"
        data_dir.mkdir(parents=True)
        (data_dir / "accounts.yml").write_text("""
accounts:
  root:
    id: '123'
    is_manager: true
  sandbox:
    id: '456'
""")

        result = get_manager_account()

        assert result["alias"] == "root"
        assert result["id"] == "123"

    def test_get_manager_account_fallback(self, monkeypatch, tmp_path):
        """Test fallback to management_account_id."""
        monkeypatch.setenv("CLAUDE_PATH", str(tmp_path))
        data_dir = tmp_path / ".data" / "aws"
        data_dir.mkdir(parents=True)
        (data_dir / "accounts.yml").write_text("""
management_account_id: '123'
accounts:
  root:
    id: '123'
  sandbox:
    id: '456'
""")

        result = get_manager_account()

        assert result["alias"] == "root"


class TestClearAwsData:
    """Tests for clear_aws_data function."""

    def test_clears_existing_directory(self, monkeypatch, tmp_path):
        """Test deletes .data/aws directory."""
        monkeypatch.setenv("CLAUDE_PATH", str(tmp_path))
        data_dir = tmp_path / ".data" / "aws"
        data_dir.mkdir(parents=True)
        (data_dir / "accounts.yml").write_text("test")

        result = clear_aws_data()

        assert result is True
        assert not data_dir.exists()

    def test_returns_false_when_nonexistent(self, monkeypatch, tmp_path):
        """Test returns False when directory doesn't exist."""
        monkeypatch.setenv("CLAUDE_PATH", str(tmp_path))

        result = clear_aws_data()

        assert result is False


class TestInventoryExists:
    """Tests for inventory_exists function."""

    def test_returns_false_when_no_data_dir(self, monkeypatch, tmp_path):
        """Test returns False when .data/aws doesn't exist."""
        monkeypatch.setenv("CLAUDE_PATH", str(tmp_path))

        result = inventory_exists()

        assert result is False

    def test_returns_false_when_only_accounts_yml(self, monkeypatch, tmp_path):
        """Test returns False when only accounts.yml exists (no inventory)."""
        monkeypatch.setenv("CLAUDE_PATH", str(tmp_path))
        data_dir = tmp_path / ".data" / "aws"
        data_dir.mkdir(parents=True)
        (data_dir / "accounts.yml").write_text("schema_version: '1.0'")

        result = inventory_exists()

        assert result is False

    def test_returns_true_when_inventory_files_exist(self, monkeypatch, tmp_path):
        """Test returns True when inventory .yml files exist in org subdirs."""
        monkeypatch.setenv("CLAUDE_PATH", str(tmp_path))
        data_dir = tmp_path / ".data" / "aws"
        data_dir.mkdir(parents=True)
        (data_dir / "accounts.yml").write_text("schema_version: '1.0'")

        # Create org structure with inventory file
        org_dir = data_dir / "o-abc123" / "root"
        org_dir.mkdir(parents=True)
        (org_dir / "sandbox.yml").write_text("vpcs: []")

        result = inventory_exists()

        assert result is True

    def test_detects_deeply_nested_inventory(self, monkeypatch, tmp_path):
        """Test detects inventory in nested OU paths."""
        monkeypatch.setenv("CLAUDE_PATH", str(tmp_path))
        data_dir = tmp_path / ".data" / "aws"
        data_dir.mkdir(parents=True)

        # Create deeply nested inventory
        nested_dir = data_dir / "o-abc123" / "production" / "workloads" / "team-a"
        nested_dir.mkdir(parents=True)
        (nested_dir / "app-account.yml").write_text("vpcs: []")

        result = inventory_exists()

        assert result is True
