#!/usr/bin/env python3
"""Add IAM policy binding for storage bucket access.

Optional script for granting storage.objectUser role on a GCS bucket.
"""

import os
import subprocess
import sys

from loguru import logger


def add_bucket_iam_binding(bucket_name: str, member_email: str, role: str = "roles/storage.objectUser") -> bool:
    """Add IAM policy binding to a GCS bucket.

    Args:
        bucket_name: GCS bucket name (without gs:// prefix)
        member_email: User email address
        role: IAM role to grant

    Returns:
        True if successful
    """
    bucket_uri = f"gs://{bucket_name}" if not bucket_name.startswith("gs://") else bucket_name
    member = f"user:{member_email}"

    cmd = [
        "gcloud", "storage", "buckets", "add-iam-policy-binding",
        bucket_uri,
        f"--member={member}",
        f"--role={role}"
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            logger.success(f"Added {role} to {member} on {bucket_uri}")
            return True
        else:
            logger.error(f"Failed: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"Error: {e}")
        return False


def main():
    """Main entry point."""
    bucket = os.environ.get("GENMEDIA_BUCKET")
    email = os.environ.get("GCLOUD_EMAIL_ADDRESS")

    if not bucket:
        logger.error("GENMEDIA_BUCKET environment variable not set")
        sys.exit(1)

    if not email:
        logger.error("GCLOUD_EMAIL_ADDRESS environment variable not set")
        sys.exit(1)

    logger.info(f"Adding storage.objectUser role for {email} on {bucket}")

    if add_bucket_iam_binding(bucket, email):
        logger.success("Bucket policy added successfully")
    else:
        logger.error("Failed to add bucket policy")
        sys.exit(1)


if __name__ == "__main__":
    main()
