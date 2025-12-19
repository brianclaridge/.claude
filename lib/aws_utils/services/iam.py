"""IAM resource discovery - Roles, Policies, Users, Groups."""

from botocore.exceptions import ClientError
from loguru import logger

from aws_utils.core.schemas import IAMRole, IAMPolicy, IAMUser, IAMGroup
from aws_utils.core.session import create_session


def discover_iam_roles(
    profile_name: str | None = None,
    region: str | None = None,
) -> list[IAMRole]:
    """Discover all IAM roles in an account.

    Note: IAM is a global service, region parameter is only used for session creation.

    Args:
        profile_name: AWS CLI profile name
        region: AWS region (for session creation only)

    Returns:
        List of IAMRole objects
    """
    session = create_session(profile_name, region)
    iam = session.client("iam")

    try:
        roles = []
        paginator = iam.get_paginator("list_roles")

        for page in paginator.paginate():
            for role in page.get("Roles", []):
                # Extract tags
                tags_dict = {}
                for tag in role.get("Tags", []):
                    tags_dict[tag["Key"]] = tag["Value"]

                iam_role = IAMRole(
                    role_name=role["RoleName"],
                    role_id=role["RoleId"],
                    arn=role["Arn"],
                    path=role.get("Path", "/"),
                    description=role.get("Description"),
                    create_date=role.get("CreateDate", "").isoformat()
                    if role.get("CreateDate")
                    else None,
                    max_session_duration=role.get("MaxSessionDuration", 3600),
                    assume_role_policy_document=str(role.get("AssumeRolePolicyDocument"))
                    if role.get("AssumeRolePolicyDocument")
                    else None,
                    tags=tags_dict,
                )
                roles.append(iam_role)

        logger.debug(f"Discovered {len(roles)} IAM roles")
        return roles
    except ClientError as e:
        logger.warning(f"Failed to discover IAM roles: {e}")
        return []


def discover_iam_policies(
    profile_name: str | None = None,
    region: str | None = None,
) -> list[IAMPolicy]:
    """Discover customer managed IAM policies in an account.

    Note: Only returns customer managed policies (Scope='Local'), not AWS managed policies.

    Args:
        profile_name: AWS CLI profile name
        region: AWS region (for session creation only)

    Returns:
        List of IAMPolicy objects (customer managed only)
    """
    session = create_session(profile_name, region)
    iam = session.client("iam")

    try:
        policies = []
        paginator = iam.get_paginator("list_policies")

        # Scope='Local' returns only customer managed policies
        for page in paginator.paginate(Scope="Local"):
            for policy in page.get("Policies", []):
                iam_policy = IAMPolicy(
                    policy_name=policy["PolicyName"],
                    policy_id=policy["PolicyId"],
                    arn=policy["Arn"],
                    path=policy.get("Path", "/"),
                    description=policy.get("Description"),
                    create_date=policy.get("CreateDate", "").isoformat()
                    if policy.get("CreateDate")
                    else None,
                    update_date=policy.get("UpdateDate", "").isoformat()
                    if policy.get("UpdateDate")
                    else None,
                    attachment_count=policy.get("AttachmentCount", 0),
                    is_attachable=policy.get("IsAttachable", True),
                    default_version_id=policy.get("DefaultVersionId"),
                )
                policies.append(iam_policy)

        logger.debug(f"Discovered {len(policies)} IAM customer managed policies")
        return policies
    except ClientError as e:
        logger.warning(f"Failed to discover IAM policies: {e}")
        return []


def discover_iam_users(
    profile_name: str | None = None,
    region: str | None = None,
) -> list[IAMUser]:
    """Discover all IAM users in an account.

    Args:
        profile_name: AWS CLI profile name
        region: AWS region (for session creation only)

    Returns:
        List of IAMUser objects
    """
    session = create_session(profile_name, region)
    iam = session.client("iam")

    try:
        users = []
        paginator = iam.get_paginator("list_users")

        for page in paginator.paginate():
            for user in page.get("Users", []):
                # Extract tags
                tags_dict = {}
                for tag in user.get("Tags", []):
                    tags_dict[tag["Key"]] = tag["Value"]

                iam_user = IAMUser(
                    user_name=user["UserName"],
                    user_id=user["UserId"],
                    arn=user["Arn"],
                    path=user.get("Path", "/"),
                    create_date=user.get("CreateDate", "").isoformat()
                    if user.get("CreateDate")
                    else None,
                    password_last_used=user.get("PasswordLastUsed", "").isoformat()
                    if user.get("PasswordLastUsed")
                    else None,
                    tags=tags_dict,
                )
                users.append(iam_user)

        logger.debug(f"Discovered {len(users)} IAM users")
        return users
    except ClientError as e:
        logger.warning(f"Failed to discover IAM users: {e}")
        return []


def discover_iam_groups(
    profile_name: str | None = None,
    region: str | None = None,
) -> list[IAMGroup]:
    """Discover all IAM groups in an account.

    Args:
        profile_name: AWS CLI profile name
        region: AWS region (for session creation only)

    Returns:
        List of IAMGroup objects
    """
    session = create_session(profile_name, region)
    iam = session.client("iam")

    try:
        groups = []
        paginator = iam.get_paginator("list_groups")

        for page in paginator.paginate():
            for group in page.get("Groups", []):
                iam_group = IAMGroup(
                    group_name=group["GroupName"],
                    group_id=group["GroupId"],
                    arn=group["Arn"],
                    path=group.get("Path", "/"),
                    create_date=group.get("CreateDate", "").isoformat()
                    if group.get("CreateDate")
                    else None,
                )
                groups.append(iam_group)

        logger.debug(f"Discovered {len(groups)} IAM groups")
        return groups
    except ClientError as e:
        logger.warning(f"Failed to discover IAM groups: {e}")
        return []
