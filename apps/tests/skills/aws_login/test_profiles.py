"""Tests for AWS CLI profile management."""

from configparser import ConfigParser
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from claude_apps.skills.aws_login.profiles import (
    clear_aws_config,
    ensure_aws_directory,
    ensure_profile,
    get_aws_config_path,
    load_aws_config,
    save_aws_config,
    set_default_profile,
)


class TestGetAwsConfigPath:
    """Tests for get_aws_config_path function."""

    def test_returns_home_aws_config(self):
        """Test returns ~/.aws/config path."""
        result = get_aws_config_path()

        assert result == Path.home() / ".aws" / "config"


class TestEnsureAwsDirectory:
    """Tests for ensure_aws_directory function."""

    def test_creates_aws_directory(self, tmp_path, monkeypatch):
        """Test creates ~/.aws directory."""
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        monkeypatch.setattr(Path, "home", lambda: fake_home)

        ensure_aws_directory()

        assert (fake_home / ".aws").exists()

    def test_handles_existing_directory(self, tmp_path, monkeypatch):
        """Test handles existing directory."""
        fake_home = tmp_path / "home"
        aws_dir = fake_home / ".aws"
        aws_dir.mkdir(parents=True)
        monkeypatch.setattr(Path, "home", lambda: fake_home)

        ensure_aws_directory()  # Should not raise

        assert aws_dir.exists()


class TestLoadAwsConfig:
    """Tests for load_aws_config function."""

    def test_loads_existing_config(self, tmp_path, monkeypatch):
        """Test loads existing AWS config."""
        fake_home = tmp_path / "home"
        aws_dir = fake_home / ".aws"
        aws_dir.mkdir(parents=True)
        config_file = aws_dir / "config"
        config_file.write_text("[profile test]\nregion = us-west-2\n")
        monkeypatch.setattr(Path, "home", lambda: fake_home)

        result = load_aws_config()

        assert result.has_section("profile test")
        assert result.get("profile test", "region") == "us-west-2"

    def test_returns_empty_for_missing_file(self, tmp_path, monkeypatch):
        """Test returns empty ConfigParser for missing file."""
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        monkeypatch.setattr(Path, "home", lambda: fake_home)

        result = load_aws_config()

        assert isinstance(result, ConfigParser)
        assert len(result.sections()) == 0


class TestSaveAwsConfig:
    """Tests for save_aws_config function."""

    def test_saves_config_to_file(self, tmp_path, monkeypatch):
        """Test saves config to ~/.aws/config."""
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        monkeypatch.setattr(Path, "home", lambda: fake_home)

        config = ConfigParser()
        config.add_section("profile test")
        config.set("profile test", "region", "eu-west-1")

        save_aws_config(config)

        saved_content = (fake_home / ".aws" / "config").read_text()
        assert "profile test" in saved_content
        assert "region = eu-west-1" in saved_content


class TestClearAwsConfig:
    """Tests for clear_aws_config function."""

    def test_removes_existing_config(self, tmp_path, monkeypatch):
        """Test removes existing config file."""
        fake_home = tmp_path / "home"
        aws_dir = fake_home / ".aws"
        aws_dir.mkdir(parents=True)
        config_file = aws_dir / "config"
        config_file.write_text("[profile old]\nregion = us-east-1\n")
        monkeypatch.setattr(Path, "home", lambda: fake_home)

        clear_aws_config()

        assert not config_file.exists()

    def test_handles_missing_config(self, tmp_path, monkeypatch):
        """Test handles missing config file."""
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        monkeypatch.setattr(Path, "home", lambda: fake_home)

        clear_aws_config()  # Should not raise


class TestEnsureProfile:
    """Tests for ensure_profile function."""

    def test_creates_new_profile(self, tmp_path, monkeypatch):
        """Test creates new SSO profile."""
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        monkeypatch.setattr(Path, "home", lambda: fake_home)
        monkeypatch.setenv("AWS_SSO_START_URL", "https://test.awsapps.com/start")
        monkeypatch.setenv("AWS_DEFAULT_REGION", "us-west-2")
        monkeypatch.setenv("AWS_SSO_REGION", "us-east-1")
        monkeypatch.setenv("AWS_SSO_ROLE_NAME", "AdminAccess")

        result = ensure_profile("sandbox", "123456789012", "Sandbox Account")

        assert result is True
        config = load_aws_config()
        assert config.has_section("profile sandbox")
        assert config.get("profile sandbox", "sso_account_id") == "123456789012"
        assert config.get("profile sandbox", "sso_start_url") == "https://test.awsapps.com/start"

    def test_returns_false_for_existing_profile(self, tmp_path, monkeypatch):
        """Test returns False if profile exists."""
        fake_home = tmp_path / "home"
        aws_dir = fake_home / ".aws"
        aws_dir.mkdir(parents=True)
        (aws_dir / "config").write_text("[profile sandbox]\nregion = us-east-1\n")
        monkeypatch.setattr(Path, "home", lambda: fake_home)

        result = ensure_profile("sandbox", "123456789012")

        assert result is False

    def test_adds_https_prefix(self, tmp_path, monkeypatch):
        """Test adds https:// prefix to SSO URL."""
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        monkeypatch.setattr(Path, "home", lambda: fake_home)
        monkeypatch.setenv("AWS_SSO_START_URL", "test.awsapps.com/start")
        monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
        monkeypatch.setenv("AWS_SSO_REGION", "us-east-1")

        ensure_profile("test", "111111111111")

        config = load_aws_config()
        assert config.get("profile test", "sso_start_url").startswith("https://")

    def test_uses_provided_values(self, tmp_path, monkeypatch):
        """Test uses explicitly provided values."""
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        monkeypatch.setattr(Path, "home", lambda: fake_home)
        monkeypatch.setenv("AWS_SSO_START_URL", "https://default.awsapps.com/start")
        monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
        monkeypatch.setenv("AWS_SSO_REGION", "us-east-1")

        ensure_profile(
            "custom",
            "222222222222",
            region="eu-west-1",
            sso_url="https://custom.awsapps.com/start",
            sso_role="ReadOnlyAccess",
        )

        config = load_aws_config()
        assert config.get("profile custom", "region") == "eu-west-1"
        assert config.get("profile custom", "sso_start_url") == "https://custom.awsapps.com/start"
        assert config.get("profile custom", "sso_role_name") == "ReadOnlyAccess"


class TestSetDefaultProfile:
    """Tests for set_default_profile function."""

    def test_copies_profile_to_default(self, tmp_path, monkeypatch):
        """Test copies named profile to default section."""
        fake_home = tmp_path / "home"
        aws_dir = fake_home / ".aws"
        aws_dir.mkdir(parents=True)
        (aws_dir / "config").write_text("""[profile sandbox]
sso_start_url = https://test.awsapps.com/start
sso_region = us-east-1
sso_account_id = 123456789012
sso_role_name = AdminAccess
region = us-west-2
""")
        monkeypatch.setattr(Path, "home", lambda: fake_home)

        set_default_profile("sandbox")

        config = load_aws_config()
        assert config.has_section("default")
        assert config.get("default", "sso_account_id") == "123456789012"
        assert config.get("default", "region") == "us-west-2"

    def test_handles_missing_profile(self, tmp_path, monkeypatch):
        """Test handles missing source profile."""
        fake_home = tmp_path / "home"
        aws_dir = fake_home / ".aws"
        aws_dir.mkdir(parents=True)
        (aws_dir / "config").write_text("")
        monkeypatch.setattr(Path, "home", lambda: fake_home)

        set_default_profile("nonexistent")  # Should not raise

    def test_creates_default_section(self, tmp_path, monkeypatch):
        """Test creates default section if missing."""
        fake_home = tmp_path / "home"
        aws_dir = fake_home / ".aws"
        aws_dir.mkdir(parents=True)
        (aws_dir / "config").write_text("[profile test]\nregion = us-east-1\n")
        monkeypatch.setattr(Path, "home", lambda: fake_home)

        set_default_profile("test")

        config = load_aws_config()
        assert config.has_section("default")
        assert config.get("default", "region") == "us-east-1"
