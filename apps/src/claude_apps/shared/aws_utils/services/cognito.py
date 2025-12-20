"""Cognito User Pools and Identity Pools discovery."""

from botocore.exceptions import ClientError
from loguru import logger

from ..core.schemas import CognitoUserPool, CognitoIdentityPool
from ..core.session import create_session, get_default_region


def discover_user_pools(
    profile_name: str | None = None,
    region: str | None = None,
) -> list[CognitoUserPool]:
    """Discover Cognito User Pools.

    Args:
        profile_name: AWS CLI profile name
        region: AWS region

    Returns:
        List of CognitoUserPool objects
    """
    region = region or get_default_region()
    session = create_session(profile_name, region)
    client = session.client("cognito-idp")

    try:
        pools = []
        paginator = client.get_paginator("list_user_pools")

        for page in paginator.paginate(MaxResults=60):
            for pool_data in page.get("UserPools", []):
                pool_id = pool_data.get("Id", "")

                # Get detailed info for each pool
                try:
                    detail = client.describe_user_pool(UserPoolId=pool_id)
                    pool_detail = detail.get("UserPool", {})

                    creation_date = pool_detail.get("CreationDate")
                    last_modified = pool_detail.get("LastModifiedDate")

                    pool = CognitoUserPool(
                        id=pool_id,
                        name=pool_data.get("Name", ""),
                        arn=pool_detail.get("Arn", ""),
                        status=pool_detail.get("Status"),
                        creation_date=creation_date.isoformat() if creation_date else None,
                        last_modified_date=last_modified.isoformat() if last_modified else None,
                        mfa_configuration=pool_detail.get("MfaConfiguration"),
                        estimated_number_of_users=pool_detail.get("EstimatedNumberOfUsers", 0),
                        region=region,
                    )
                    pools.append(pool)
                except ClientError as e:
                    logger.warning(f"Failed to describe user pool {pool_id}: {e}")

        logger.debug(f"Discovered {len(pools)} Cognito User Pools in {region}")
        return pools
    except ClientError as e:
        logger.warning(f"Failed to discover Cognito User Pools: {e}")
        return []


def discover_identity_pools(
    profile_name: str | None = None,
    region: str | None = None,
) -> list[CognitoIdentityPool]:
    """Discover Cognito Identity Pools (Federated Identities).

    Args:
        profile_name: AWS CLI profile name
        region: AWS region

    Returns:
        List of CognitoIdentityPool objects
    """
    region = region or get_default_region()
    session = create_session(profile_name, region)
    client = session.client("cognito-identity")

    try:
        pools = []
        paginator = client.get_paginator("list_identity_pools")

        for page in paginator.paginate(MaxResults=60):
            for pool_data in page.get("IdentityPools", []):
                pool_id = pool_data.get("IdentityPoolId", "")

                # Get detailed info for each pool
                try:
                    detail = client.describe_identity_pool(IdentityPoolId=pool_id)

                    pool = CognitoIdentityPool(
                        identity_pool_id=pool_id,
                        identity_pool_name=detail.get("IdentityPoolName", ""),
                        allow_unauthenticated=detail.get("AllowUnauthenticatedIdentities", False),
                        developer_provider_name=detail.get("DeveloperProviderName"),
                        region=region,
                    )
                    pools.append(pool)
                except ClientError as e:
                    logger.warning(f"Failed to describe identity pool {pool_id}: {e}")

        logger.debug(f"Discovered {len(pools)} Cognito Identity Pools in {region}")
        return pools
    except ClientError as e:
        logger.warning(f"Failed to discover Cognito Identity Pools: {e}")
        return []
