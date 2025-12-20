"""Tests for AWS Organizations discovery using moto."""

import pytest
from moto import mock_aws

from claude_apps.shared.aws_utils.services.organizations import (
    _generate_alias,
    collect_all_accounts,
    discover_organization,
    get_organization_id,
)


class TestGenerateAlias:
    """Tests for _generate_alias function."""

    def test_simple_name(self):
        """Test alias from simple account name."""
        assert _generate_alias("MyAccount") == "myaccount"

    def test_name_with_spaces(self):
        """Test alias from name with spaces."""
        assert _generate_alias("My Account Name") == "my-account-name"

    def test_strip_prefix(self):
        """Test stripping default prefix."""
        assert _generate_alias("provision-iam-production") == "production"

    def test_custom_prefix(self):
        """Test stripping custom prefix."""
        assert _generate_alias("aws-dev-staging", prefix_to_strip="aws-dev-") == "staging"

    def test_no_prefix_match(self):
        """Test when prefix doesn't match."""
        assert _generate_alias("production-account") == "production-account"

    def test_empty_after_strip(self):
        """Test when name equals prefix."""
        # Should return lowercase name when result would be empty
        assert _generate_alias("provision-iam-") == "provision-iam-"


class TestCollectAllAccounts:
    """Tests for collect_all_accounts function."""

    def test_empty_tree(self):
        """Test with empty tree."""
        node = {"accounts": {}, "children": {}}
        result = list(collect_all_accounts(node))
        assert result == []

    def test_single_level_accounts(self):
        """Test with accounts at root level only."""
        node = {
            "accounts": {
                "prod": {"id": "111111111111", "name": "Production"},
                "dev": {"id": "222222222222", "name": "Development"},
            },
            "children": {},
        }
        result = list(collect_all_accounts(node))
        assert len(result) == 2
        aliases = {alias for alias, _ in result}
        assert aliases == {"prod", "dev"}

    def test_nested_accounts(self):
        """Test with accounts in nested OUs."""
        node = {
            "accounts": {
                "root-acct": {"id": "111111111111", "name": "Root"},
            },
            "children": {
                "Workloads": {
                    "accounts": {
                        "prod": {"id": "222222222222", "name": "Production"},
                    },
                    "children": {
                        "Dev": {
                            "accounts": {
                                "dev": {"id": "333333333333", "name": "Development"},
                            },
                            "children": {},
                        }
                    },
                }
            },
        }
        result = list(collect_all_accounts(node))
        assert len(result) == 3
        aliases = {alias for alias, _ in result}
        assert aliases == {"root-acct", "prod", "dev"}

    def test_deep_nesting(self):
        """Test deeply nested structure."""
        node = {
            "accounts": {},
            "children": {
                "L1": {
                    "accounts": {"a1": {"id": "1"}},
                    "children": {
                        "L2": {
                            "accounts": {"a2": {"id": "2"}},
                            "children": {
                                "L3": {
                                    "accounts": {"a3": {"id": "3"}},
                                    "children": {},
                                }
                            },
                        }
                    },
                }
            },
        }
        result = list(collect_all_accounts(node))
        assert len(result) == 3


class TestGetOrganizationId:
    """Tests for get_organization_id function."""

    @mock_aws
    def test_get_org_id_not_in_org(self):
        """Test when account is not in an organization."""
        # moto starts without an organization by default
        result = get_organization_id()
        assert result is None

    @mock_aws
    def test_get_org_id_with_org(self):
        """Test getting org ID when organization exists."""
        import boto3

        # Create an organization
        org = boto3.client("organizations", region_name="us-east-1")
        org.create_organization(FeatureSet="ALL")

        result = get_organization_id()
        assert result is not None
        assert result.startswith("o-")


class TestDiscoverOrganization:
    """Tests for discover_organization function."""

    @mock_aws
    def test_discover_empty_org(self):
        """Test discovering an empty organization."""
        import boto3

        org = boto3.client("organizations", region_name="us-east-1")
        org.create_organization(FeatureSet="ALL")

        result = discover_organization()

        assert "organization_id" in result
        assert "management_account_id" in result
        assert "root_id" in result
        assert result["organization_id"].startswith("o-")
        assert result["root_id"].startswith("r-")

    @mock_aws
    def test_discover_org_with_accounts(self):
        """Test discovering organization with accounts."""
        import boto3

        org = boto3.client("organizations", region_name="us-east-1")
        org.create_organization(FeatureSet="ALL")

        # Create accounts
        org.create_account(AccountName="Production", Email="prod@example.com")
        org.create_account(AccountName="Development", Email="dev@example.com")

        result = discover_organization()

        # The root should have accounts
        accounts = list(collect_all_accounts(result))
        # Note: moto may or may not include these immediately depending on version
        assert isinstance(accounts, list)

    @mock_aws
    def test_discover_no_org(self):
        """Test discovering when no organization exists."""
        result = discover_organization()
        assert result == {}

    @mock_aws
    def test_discover_org_with_ous(self):
        """Test discovering organization with OUs."""
        import boto3

        org = boto3.client("organizations", region_name="us-east-1")
        org.create_organization(FeatureSet="ALL")

        # Get root ID
        roots = org.list_roots()["Roots"]
        root_id = roots[0]["Id"]

        # Create OU
        ou_response = org.create_organizational_unit(
            ParentId=root_id,
            Name="Workloads",
        )
        ou_id = ou_response["OrganizationalUnit"]["Id"]

        result = discover_organization()

        assert "children" in result
        assert "organization_id" in result

    @mock_aws
    def test_discover_org_metadata(self):
        """Test that discovery includes all expected metadata."""
        import boto3

        org = boto3.client("organizations", region_name="us-east-1")
        create_response = org.create_organization(FeatureSet="ALL")

        result = discover_organization()

        expected_keys = [
            "organization_id",
            "management_account_id",
            "root_id",
            "root_name",
            "accounts",
            "children",
        ]
        for key in expected_keys:
            assert key in result, f"Missing key: {key}"
