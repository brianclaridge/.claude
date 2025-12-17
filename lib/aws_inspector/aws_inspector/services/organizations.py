"""AWS Organizations discovery."""

from typing import Any, Callable

from botocore.exceptions import ClientError
from loguru import logger

from aws_inspector.core.session import create_session


def get_organization_id(profile_name: str | None = None) -> str | None:
    """Get the AWS Organization ID.

    Args:
        profile_name: AWS CLI profile name

    Returns:
        Organization ID (o-xxx) or None if not in an organization
    """
    session = create_session(profile_name)
    org = session.client("organizations")

    try:
        response = org.describe_organization()
        return response.get("Organization", {}).get("Id")
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "")
        if error_code == "AWSOrganizationsNotInUseException":
            logger.warning("Account is not part of an AWS Organization")
            return None
        logger.warning(f"Failed to get organization ID: {e}")
        return None


def _traverse_ou(
    org_client: Any,
    parent_id: str,
    path: str = "",
) -> dict[str, Any]:
    """Recursively traverse OUs and collect accounts.

    Args:
        org_client: Boto3 Organizations client
        parent_id: Parent OU or root ID
        path: Current OU path

    Returns:
        Tree structure with accounts and children OUs
    """
    node = {"accounts": {}, "children": {}}

    # List accounts in this OU
    try:
        paginator = org_client.get_paginator("list_accounts_for_parent")
        for page in paginator.paginate(ParentId=parent_id):
            for account in page.get("Accounts", []):
                if account.get("Status") != "ACTIVE":
                    continue

                account_id = account["Id"]
                account_name = account.get("Name", "")

                # Generate alias from name
                alias = _generate_alias(account_name)

                node["accounts"][alias] = {
                    "id": account_id,
                    "name": account_name,
                    "ou_path": path,
                }
    except ClientError as e:
        logger.warning(f"Failed to list accounts for {parent_id}: {e}")

    # List child OUs
    try:
        paginator = org_client.get_paginator("list_organizational_units_for_parent")
        for page in paginator.paginate(ParentId=parent_id):
            for ou in page.get("OrganizationalUnits", []):
                ou_id = ou["Id"]
                ou_name = ou.get("Name", ou_id)

                # Build child path
                child_path = f"{path}/{ou_name}" if path else ou_name

                # Recurse into child OU
                node["children"][ou_name] = _traverse_ou(org_client, ou_id, child_path)
    except ClientError as e:
        logger.warning(f"Failed to list OUs for {parent_id}: {e}")

    return node


def _generate_alias(account_name: str, prefix_to_strip: str = "provision-iam-") -> str:
    """Generate account alias from name.

    Args:
        account_name: Full account name
        prefix_to_strip: Prefix to remove

    Returns:
        Shortened alias
    """
    alias = account_name.lower().replace(" ", "-")
    if alias.startswith(prefix_to_strip):
        alias = alias[len(prefix_to_strip):]
    return alias or account_name.lower()


def discover_organization(
    profile_name: str | None = None,
    force_refresh: bool = False,
) -> dict[str, Any]:
    """Discover AWS Organizations hierarchy with all accounts.

    Args:
        profile_name: AWS CLI profile name
        force_refresh: Ignored (for API compatibility)

    Returns:
        Organization tree with accounts and OUs
    """
    session = create_session(profile_name)
    org = session.client("organizations")

    try:
        # Get organization info
        org_response = org.describe_organization()
        org_data = org_response.get("Organization", {})
        org_id = org_data.get("Id", "")

        # Get root ID
        roots_response = org.list_roots()
        roots = roots_response.get("Roots", [])
        if not roots:
            logger.error("No organization roots found")
            return {}

        root_id = roots[0]["Id"]
        root_name = roots[0].get("Name", "Root")

        # Traverse the organization
        logger.info("Discovering organization hierarchy...")
        tree = _traverse_ou(org, root_id, "")

        # Add metadata
        tree["organization_id"] = org_id
        tree["root_id"] = root_id
        tree["root_name"] = root_name

        total_accounts = sum(1 for _ in collect_all_accounts(tree))
        logger.info(f"Discovered {total_accounts} accounts in organization {org_id}")

        return tree
    except ClientError as e:
        logger.error(f"Failed to discover organization: {e}")
        return {}


def collect_all_accounts(node: dict[str, Any]) -> list[tuple[str, dict]]:
    """Collect all accounts from organization tree.

    Args:
        node: Organization tree node

    Yields:
        Tuples of (alias, account_dict)
    """
    # Collect accounts at this level
    for alias, account in node.get("accounts", {}).items():
        yield (alias, account)

    # Recurse into children
    for child in node.get("children", {}).values():
        yield from collect_all_accounts(child)
