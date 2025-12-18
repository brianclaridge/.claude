"""Secrets Manager discovery (metadata only, never secret values)."""

from botocore.exceptions import ClientError
from loguru import logger

from aws_utils.core.schemas import SecretsManagerSecret
from aws_utils.core.session import create_session, get_default_region


def discover_secrets(
    profile_name: str | None = None,
    region: str | None = None,
) -> list[SecretsManagerSecret]:
    """Discover Secrets Manager secrets (metadata only, never values).

    SECURITY: This function only retrieves metadata (names, ARNs, rotation status).
    It NEVER retrieves or returns actual secret values.

    Args:
        profile_name: AWS CLI profile name
        region: AWS region

    Returns:
        List of SecretsManagerSecret objects (metadata only)
    """
    region = region or get_default_region()
    session = create_session(profile_name, region)
    client = session.client("secretsmanager")

    try:
        secrets = []
        paginator = client.get_paginator("list_secrets")

        for page in paginator.paginate():
            for secret_data in page.get("SecretList", []):
                # Convert tags list to dict
                tags = {}
                for tag in secret_data.get("Tags", []):
                    tags[tag.get("Key", "")] = tag.get("Value", "")

                # Format dates as ISO strings
                last_rotated = secret_data.get("LastRotatedDate")
                last_accessed = secret_data.get("LastAccessedDate")

                secret = SecretsManagerSecret(
                    name=secret_data.get("Name", ""),
                    arn=secret_data.get("ARN", ""),
                    description=secret_data.get("Description"),
                    kms_key_id=secret_data.get("KmsKeyId"),
                    rotation_enabled=secret_data.get("RotationEnabled", False),
                    last_rotated_date=last_rotated.isoformat() if last_rotated else None,
                    last_accessed_date=last_accessed.isoformat() if last_accessed else None,
                    tags=tags,
                    region=region,
                )
                secrets.append(secret)

        logger.debug(f"Discovered {len(secrets)} secrets in {region}")
        return secrets
    except ClientError as e:
        logger.warning(f"Failed to discover secrets: {e}")
        return []
