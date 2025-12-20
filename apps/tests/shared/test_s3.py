"""Tests for S3 bucket discovery using moto."""

import pytest
from moto import mock_aws

from claude_apps.shared.aws_utils.services.s3 import discover_s3_buckets


class TestDiscoverS3Buckets:
    """Tests for discover_s3_buckets function."""

    @mock_aws
    def test_discover_s3_buckets(self):
        """Test discovering S3 buckets."""
        import boto3

        s3 = boto3.client("s3", region_name="us-east-1")

        # Create buckets
        s3.create_bucket(Bucket="test-bucket-1")
        s3.create_bucket(
            Bucket="test-bucket-2",
            CreateBucketConfiguration={"LocationConstraint": "us-west-2"},
        )

        buckets = discover_s3_buckets(region="us-east-1")

        assert len(buckets) == 2
        bucket_names = {b.name for b in buckets}
        assert "test-bucket-1" in bucket_names
        assert "test-bucket-2" in bucket_names

    @mock_aws
    def test_discover_s3_buckets_with_region(self):
        """Test that bucket regions are correctly identified."""
        import boto3

        s3 = boto3.client("s3", region_name="us-east-1")

        # Create bucket in us-east-1 (default, no LocationConstraint)
        s3.create_bucket(Bucket="bucket-east")

        # Create bucket in eu-west-1
        s3.create_bucket(
            Bucket="bucket-west",
            CreateBucketConfiguration={"LocationConstraint": "eu-west-1"},
        )

        buckets = discover_s3_buckets(region="us-east-1")

        bucket_regions = {b.name: b.region for b in buckets}
        assert bucket_regions["bucket-east"] == "us-east-1"
        assert bucket_regions["bucket-west"] == "eu-west-1"

    @mock_aws
    def test_discover_s3_buckets_arn_format(self):
        """Test that bucket ARNs are correctly formatted."""
        import boto3

        s3 = boto3.client("s3", region_name="us-east-1")
        s3.create_bucket(Bucket="my-test-bucket")

        buckets = discover_s3_buckets(region="us-east-1")

        assert len(buckets) == 1
        assert buckets[0].arn == "arn:aws:s3:::my-test-bucket"

    @mock_aws
    def test_discover_s3_buckets_empty(self):
        """Test discovering when no buckets exist."""
        buckets = discover_s3_buckets(region="us-east-1")
        assert buckets == []

    @mock_aws
    def test_discover_s3_buckets_creation_date(self):
        """Test that bucket creation dates are included."""
        import boto3

        s3 = boto3.client("s3", region_name="us-east-1")
        s3.create_bucket(Bucket="dated-bucket")

        buckets = discover_s3_buckets(region="us-east-1")

        assert len(buckets) == 1
        # moto populates CreationDate
        assert buckets[0].created is not None

    @mock_aws
    def test_discover_s3_buckets_multiple(self):
        """Test discovering many buckets."""
        import boto3

        s3 = boto3.client("s3", region_name="us-east-1")

        # Create 5 buckets
        for i in range(5):
            s3.create_bucket(Bucket=f"bucket-{i}")

        buckets = discover_s3_buckets(region="us-east-1")

        assert len(buckets) == 5
        bucket_names = sorted([b.name for b in buckets])
        assert bucket_names == ["bucket-0", "bucket-1", "bucket-2", "bucket-3", "bucket-4"]
