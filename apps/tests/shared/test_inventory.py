"""Tests for inventory reader and writer."""

import pytest
from pathlib import Path

import yaml

from claude_apps.shared.aws_utils.core.schemas import (
    AccountConfig,
    AccountInventory,
    AccountsConfig,
    S3Bucket,
    VPC,
)
from claude_apps.shared.aws_utils.inventory.reader import (
    get_account,
    get_data_path,
    list_accounts,
    load_accounts_config,
    load_inventory,
    load_inventory_by_alias,
)
from claude_apps.shared.aws_utils.inventory.writer import (
    ensure_directory,
    get_aws_data_path,
    get_inventory_path,
    get_relative_inventory_path,
    save_accounts_config,
    save_inventory,
)


class TestGetDataPath:
    """Tests for data path functions."""

    def test_get_data_path_returns_path(self, tmp_path, monkeypatch):
        """Test that get_data_path returns a Path object."""
        monkeypatch.setenv("CLAUDE_PATH", str(tmp_path))
        result = get_data_path()
        assert isinstance(result, Path)

    def test_get_aws_data_path_default(self, tmp_path, monkeypatch):
        """Test default AWS data path when no config exists."""
        monkeypatch.setenv("CLAUDE_PATH", str(tmp_path))
        result = get_aws_data_path()
        assert result == tmp_path / ".data" / "aws"

    def test_get_aws_data_path_from_config(self, tmp_path, monkeypatch):
        """Test AWS data path from config.yml."""
        monkeypatch.setenv("CLAUDE_PATH", str(tmp_path))

        # Create config.yml with custom path
        config_path = tmp_path / "config.yml"
        config_path.write_text(
            yaml.dump({
                "cloud_providers": {
                    "aws": {
                        "data_path": "custom/aws/path"
                    }
                }
            })
        )

        result = get_aws_data_path()
        assert result == tmp_path / "custom" / "aws" / "path"


class TestInventoryPath:
    """Tests for inventory path functions."""

    def test_get_inventory_path(self, tmp_path, monkeypatch):
        """Test getting full inventory path."""
        monkeypatch.setenv("CLAUDE_PATH", str(tmp_path))
        result = get_inventory_path("o-12345", "workloads/prod", "production")
        expected = tmp_path / ".data" / "aws" / "o-12345" / "workloads/prod" / "production.yml"
        assert result == expected

    def test_get_relative_inventory_path(self):
        """Test getting relative inventory path."""
        result = get_relative_inventory_path("workloads/prod", "production")
        assert result == "workloads/prod/production.yml"


class TestEnsureDirectory:
    """Tests for ensure_directory function."""

    def test_creates_parent_directories(self, tmp_path):
        """Test that parent directories are created."""
        file_path = tmp_path / "a" / "b" / "c" / "file.yml"
        ensure_directory(file_path)
        assert file_path.parent.exists()

    def test_existing_directory_no_error(self, tmp_path):
        """Test that existing directory doesn't cause error."""
        existing_dir = tmp_path / "existing"
        existing_dir.mkdir()
        file_path = existing_dir / "file.yml"
        ensure_directory(file_path)  # Should not raise
        assert existing_dir.exists()


class TestAccountsConfig:
    """Tests for accounts config read/write."""

    def test_save_and_load_accounts_config(self, tmp_path, monkeypatch):
        """Test saving and loading accounts config."""
        monkeypatch.setenv("CLAUDE_PATH", str(tmp_path))

        config = AccountsConfig(
            schema_version="4.0",
            organization_id="o-test123",
            default_region="us-west-2",
            sso_start_url="https://example.awsapps.com/start",
            accounts={
                "prod": AccountConfig(
                    id="111111111111",
                    name="Production",
                    ou_path="workloads/prod",
                    sso_role="AdministratorAccess",
                    inventory_path="workloads/prod/prod.yml",
                ),
                "dev": AccountConfig(
                    id="222222222222",
                    name="Development",
                    ou_path="workloads/dev",
                    sso_role="PowerUserAccess",
                ),
            },
        )

        # Save
        result = save_accounts_config(config)
        assert result is True

        # Verify file exists
        config_path = tmp_path / ".data" / "aws" / "accounts.yml"
        assert config_path.exists()

        # Load
        loaded = load_accounts_config()
        assert loaded is not None
        assert loaded.organization_id == "o-test123"
        assert loaded.default_region == "us-west-2"
        assert len(loaded.accounts) == 2
        assert "prod" in loaded.accounts
        assert loaded.accounts["prod"].id == "111111111111"

    def test_load_accounts_config_not_found(self, tmp_path, monkeypatch):
        """Test loading when accounts.yml doesn't exist."""
        monkeypatch.setenv("CLAUDE_PATH", str(tmp_path))
        result = load_accounts_config()
        assert result is None

    def test_load_accounts_config_invalid_yaml(self, tmp_path, monkeypatch):
        """Test loading when accounts.yml is invalid."""
        monkeypatch.setenv("CLAUDE_PATH", str(tmp_path))

        config_path = tmp_path / ".data" / "aws" / "accounts.yml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text("invalid: yaml: :")

        result = load_accounts_config()
        assert result is None


class TestInventoryReadWrite:
    """Tests for inventory file read/write."""

    def test_save_and_load_inventory(self, tmp_path, monkeypatch):
        """Test saving and loading inventory."""
        monkeypatch.setenv("CLAUDE_PATH", str(tmp_path))

        inventory = AccountInventory(
            account_id="111111111111",
            account_alias="production",
            region="us-west-2",
            vpcs=[
                VPC(
                    id="vpc-12345",
                    name="main-vpc",
                    cidr="10.0.0.0/16",
                    region="us-west-2",
                    subnets=[],
                )
            ],
            s3_buckets=[
                S3Bucket(
                    name="my-bucket",
                    arn="arn:aws:s3:::my-bucket",
                    region="us-west-2",
                )
            ],
        )

        # Save
        result = save_inventory("o-test123", "workloads/prod", "production", inventory)
        assert result is True

        # Verify file exists
        inventory_path = tmp_path / ".data" / "aws" / "o-test123" / "workloads/prod" / "production.yml"
        assert inventory_path.exists()

        # Load
        loaded = load_inventory("o-test123", "workloads/prod", "production")
        assert loaded is not None
        assert loaded.account_id == "111111111111"
        assert loaded.region == "us-west-2"
        assert len(loaded.vpcs) == 1
        assert len(loaded.s3_buckets) == 1

    def test_load_inventory_not_found(self, tmp_path, monkeypatch):
        """Test loading when inventory doesn't exist."""
        monkeypatch.setenv("CLAUDE_PATH", str(tmp_path))
        result = load_inventory("o-test123", "workloads", "nonexistent")
        assert result is None


class TestLoadInventoryByAlias:
    """Tests for load_inventory_by_alias function."""

    def test_load_by_alias_success(self, tmp_path, monkeypatch):
        """Test loading inventory by alias with accounts.yml."""
        monkeypatch.setenv("CLAUDE_PATH", str(tmp_path))

        # Create accounts.yml
        config = AccountsConfig(
            schema_version="4.0",
            organization_id="o-test123",
            default_region="us-west-2",
            sso_start_url="https://example.awsapps.com/start",
            accounts={
                "prod": AccountConfig(
                    id="111111111111",
                    name="Production",
                    ou_path="workloads/prod",
                    inventory_path="workloads/prod/prod.yml",
                ),
            },
        )
        save_accounts_config(config)

        # Create inventory file
        inventory = AccountInventory(
            account_id="111111111111",
            account_alias="prod",
            region="us-west-2",
        )

        # Save directly to expected path
        inventory_path = tmp_path / ".data" / "aws" / "o-test123" / "workloads/prod" / "prod.yml"
        inventory_path.parent.mkdir(parents=True, exist_ok=True)
        with open(inventory_path, "w") as f:
            yaml.dump(inventory.to_dict(), f)

        # Load by alias
        loaded = load_inventory_by_alias("prod")
        assert loaded is not None
        assert loaded.account_id == "111111111111"

    def test_load_by_alias_no_config(self, tmp_path, monkeypatch):
        """Test loading by alias when no accounts.yml exists."""
        monkeypatch.setenv("CLAUDE_PATH", str(tmp_path))
        result = load_inventory_by_alias("prod")
        assert result is None

    def test_load_by_alias_account_not_found(self, tmp_path, monkeypatch):
        """Test loading by alias when account not in config."""
        monkeypatch.setenv("CLAUDE_PATH", str(tmp_path))

        config = AccountsConfig(
            organization_id="o-test123",
            sso_start_url="https://example.awsapps.com/start",
            accounts={},
        )
        save_accounts_config(config)

        result = load_inventory_by_alias("nonexistent")
        assert result is None

    def test_load_by_alias_no_inventory_path(self, tmp_path, monkeypatch):
        """Test loading by alias when account has no inventory_path."""
        monkeypatch.setenv("CLAUDE_PATH", str(tmp_path))

        config = AccountsConfig(
            organization_id="o-test123",
            sso_start_url="https://example.awsapps.com/start",
            accounts={
                "prod": AccountConfig(
                    id="111111111111",
                    name="Production",
                    ou_path="workloads/prod",
                    # No inventory_path
                ),
            },
        )
        save_accounts_config(config)

        result = load_inventory_by_alias("prod")
        assert result is None


class TestListAccounts:
    """Tests for list_accounts function."""

    def test_list_accounts_success(self, tmp_path, monkeypatch):
        """Test listing all accounts."""
        monkeypatch.setenv("CLAUDE_PATH", str(tmp_path))

        config = AccountsConfig(
            organization_id="o-test123",
            sso_start_url="https://example.awsapps.com/start",
            accounts={
                "prod": AccountConfig(
                    id="111111111111",
                    name="Production",
                    ou_path="workloads/prod",
                    sso_role="AdministratorAccess",
                ),
                "dev": AccountConfig(
                    id="222222222222",
                    name="Development",
                    ou_path="workloads/dev",
                ),
            },
        )
        save_accounts_config(config)

        accounts = list_accounts()
        assert len(accounts) == 2

        aliases = {a["alias"] for a in accounts}
        assert aliases == {"prod", "dev"}

        prod = next(a for a in accounts if a["alias"] == "prod")
        assert prod["id"] == "111111111111"
        assert prod["name"] == "Production"

    def test_list_accounts_empty(self, tmp_path, monkeypatch):
        """Test listing when no accounts exist."""
        monkeypatch.setenv("CLAUDE_PATH", str(tmp_path))
        accounts = list_accounts()
        assert accounts == []


class TestGetAccount:
    """Tests for get_account function."""

    def test_get_account_success(self, tmp_path, monkeypatch):
        """Test getting account by alias."""
        monkeypatch.setenv("CLAUDE_PATH", str(tmp_path))

        config = AccountsConfig(
            organization_id="o-test123",
            sso_start_url="https://example.awsapps.com/start",
            accounts={
                "prod": AccountConfig(
                    id="111111111111",
                    name="Production",
                    ou_path="workloads/prod",
                ),
            },
        )
        save_accounts_config(config)

        account = get_account("prod")
        assert account is not None
        assert account["alias"] == "prod"
        assert account["id"] == "111111111111"

    def test_get_account_not_found(self, tmp_path, monkeypatch):
        """Test getting nonexistent account."""
        monkeypatch.setenv("CLAUDE_PATH", str(tmp_path))

        config = AccountsConfig(
            organization_id="o-test123",
            sso_start_url="https://example.awsapps.com/start",
            accounts={},
        )
        save_accounts_config(config)

        account = get_account("nonexistent")
        assert account is None

    def test_get_account_no_config(self, tmp_path, monkeypatch):
        """Test getting account when no config exists."""
        monkeypatch.setenv("CLAUDE_PATH", str(tmp_path))
        account = get_account("any")
        assert account is None
