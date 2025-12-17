"""S3 bucket discovery."""

from botocore.exceptions import ClientError
from loguru import logger

from aws_inspector.core.schemas import S3Bucket
from aws_inspector.core.session import create_session


def discover_s3_buckets(
    profile_name: str | None = None,
    region: str | None = None,
) -> list[S3Bucket]:
    """Discover all S3 buckets in an account.

    Note: S3 bucket listing is global, but we include region for consistency.
    Bucket region is determined by GetBucketLocation.

    Args:
        profile_name: AWS CLI profile name
        region: Default region for session (bucket regions discovered individually)

    Returns:
        List of S3Bucket objects
    """
    session = create_session(profile_name, region)
    s3 = session.client("s3")

    try:
        response = s3.list_buckets()
        buckets = []

        for bucket_data in response.get("Buckets", []):
            bucket_name = bucket_data["Name"]

            # Get bucket region
            try:
                location = s3.get_bucket_location(Bucket=bucket_name)
                bucket_region = location.get("LocationConstraint") or "us-east-1"
            except ClientError:
                bucket_region = "unknown"

            # Get creation date
            created = bucket_data.get("CreationDate")

            bucket = S3Bucket(
                name=bucket_name,
                region=bucket_region,
                arn=f"arn:aws:s3:::{bucket_name}",
                created=created,
            )
            buckets.append(bucket)

        logger.debug(f"Discovered {len(buckets)} S3 buckets")
        return buckets
    except ClientError as e:
        logger.warning(f"Failed to discover S3 buckets: {e}")
        return []
