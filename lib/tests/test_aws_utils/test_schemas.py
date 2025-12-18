"""Tests for aws_utils.core.schemas module."""

import pytest

from aws_utils.core.schemas import (
    VPC,
    Subnet,
    InternetGateway,
    NATGateway,
    ElasticIP,
    S3Bucket,
    SQSQueue,
    SNSTopic,
    SESIdentity,
    AccountInventory,
)


class TestVPC:
    """Tests for VPC schema."""

    def test_create_vpc(self):
        """Should create VPC with required fields."""
        vpc = VPC(
            id="vpc-12345",
            cidr="10.0.0.0/16",
            is_default=False,
        )
        assert vpc.id == "vpc-12345"
        assert vpc.cidr == "10.0.0.0/16"
        assert vpc.is_default is False

    def test_vpc_with_subnets(self):
        """Should create VPC with nested subnets."""
        subnet = Subnet(
            id="subnet-12345",
            cidr="10.0.1.0/24",
            az="us-east-1a",
            type="public",
        )
        vpc = VPC(
            id="vpc-12345",
            cidr="10.0.0.0/16",
            is_default=False,
            subnets=[subnet],
        )
        assert len(vpc.subnets) == 1
        assert vpc.subnets[0].id == "subnet-12345"


class TestS3Bucket:
    """Tests for S3Bucket schema."""

    def test_create_bucket(self):
        """Should create S3Bucket with required fields."""
        bucket = S3Bucket(
            name="my-bucket",
            region="us-east-1",
            arn="arn:aws:s3:::my-bucket",
        )
        assert bucket.name == "my-bucket"
        assert bucket.region == "us-east-1"


class TestAccountInventory:
    """Tests for AccountInventory schema."""

    def test_create_inventory(self):
        """Should create AccountInventory with optional fields."""
        inventory = AccountInventory(
            account_id="123456789012",
            account_alias="sandbox",
            region="us-east-1",
        )
        assert inventory.account_id == "123456789012"
        assert inventory.vpcs == []
        assert inventory.s3_buckets == []
