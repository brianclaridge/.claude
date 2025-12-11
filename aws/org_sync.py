#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "boto3",
#     "pyyaml",
#     "loguru",
# ]
# ///
"""
AWS Organizations hierarchy sync to aws.yml.

Fetches complete OU tree and account metadata from AWS Organizations API.
Merges with existing aws.yml, preserving aliases and SSO config.
"""

import argparse
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml
from loguru import logger

# Add scripts directory to path
scripts_dir = Path(__file__).parent
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

from auth_helper import get_aws_session
from config_reader import get_config_path
from logging_config import setup_logging


@dataclass
class AccountMetadata:
    """Full account metadata from AWS Organizations."""

    account_id: str
    account_name: str
    email: str
    status: str
    ou_path: str
    depth: int
    joined_method: str
    joined_timestamp: datetime | None
    tags: dict[str, str] = field(default_factory=dict)
    alias: str | None = None


@dataclass
class OUNode:
    """Organizational Unit node in the hierarchy tree."""

    id: str
    name: str
    accounts: dict[str, AccountMetadata] = field(default_factory=dict)
    ous: dict[str, "OUNode"] = field(default_factory=dict)


@dataclass
class OrganizationTree:
    """Complete AWS Organization tree."""

    org_id: str
    master_account_id: str
    synced_at: datetime
    root: OUNode


class OrganizationSync:
    """Syncs AWS Organizations hierarchy to aws.yml."""

    # Tags to exclude from output (AWS system tags)
    SYSTEM_TAGS = {"Email", "Name", "ManagedBy", "aws:"}

    def __init__(self, profile_name: str = "root"):
        """
        Initialize with AWS profile.

        Args:
            profile_name: AWS profile with Organizations access (typically root)
        """
        self.profile_name = profile_name
        self.session = None
        self.org_client = None
        self._alias_map: dict[str, str] = {}  # account_id -> alias

    def _connect(self) -> None:
        """Establish AWS Organizations API connection."""
        logger.debug(f"Connecting with profile: {self.profile_name}")
        self.session = get_aws_session(profile_name=self.profile_name)
        self.org_client = self.session.client("organizations")

    def _get_organization_info(self) -> tuple[str, str]:
        """
        Get organization ID and master account ID.

        Returns:
            tuple: (org_id, master_account_id)
        """
        response = self.org_client.describe_organization()
        org = response["Organization"]
        return org["Id"], org["MasterAccountId"]

    def _get_root_id(self) -> str:
        """
        Get organization root ID.

        Returns:
            str: Root ID (r-xxxx format)
        """
        response = self.org_client.list_roots()
        return response["Roots"][0]["Id"]

    def _fetch_account_tags(self, account_id: str) -> dict[str, str]:
        """
        Fetch user-defined tags (excluding system tags).

        Args:
            account_id: AWS account ID

        Returns:
            dict: Tag key-value pairs
        """
        try:
            response = self.org_client.list_tags_for_resource(ResourceId=account_id)
            return {
                tag["Key"]: tag["Value"]
                for tag in response.get("Tags", [])
                if not any(tag["Key"].startswith(sys_tag) for sys_tag in self.SYSTEM_TAGS)
            }
        except Exception as e:
            logger.warning(f"Failed to fetch tags for {account_id}: {e}")
            return {}

    def _fetch_account_metadata(self, account_id: str, ou_path: str, depth: int) -> AccountMetadata:
        """
        Fetch complete metadata for a single account.

        Args:
            account_id: AWS account ID
            ou_path: OU path for this account
            depth: Depth in the OU hierarchy

        Returns:
            AccountMetadata: Full account metadata
        """
        response = self.org_client.describe_account(AccountId=account_id)
        account = response["Account"]

        tags = self._fetch_account_tags(account_id)

        joined_timestamp = account.get("JoinedTimestamp")
        if joined_timestamp and not isinstance(joined_timestamp, datetime):
            joined_timestamp = None

        return AccountMetadata(
            account_id=account["Id"],
            account_name=account["Name"],
            email=account.get("Email", ""),
            status=account["Status"],
            ou_path=ou_path,
            depth=depth,
            joined_method=account.get("JoinedMethod", "UNKNOWN"),
            joined_timestamp=joined_timestamp,
            tags=tags,
            alias=self._alias_map.get(account_id),
        )

    def _generate_alias(self, account_name: str) -> str:
        """
        Generate alias from account name.

        Args:
            account_name: AWS account name

        Returns:
            str: Generated alias (lowercase, hyphenated)
        """
        return account_name.lower().replace(" ", "-").replace("_", "-")

    def _fetch_accounts_for_parent(
        self, parent_id: str, ou_path: str, depth: int
    ) -> dict[str, AccountMetadata]:
        """
        Fetch all accounts directly under a parent (root or OU).

        Args:
            parent_id: Parent ID (root or OU)
            ou_path: OU path for accounts
            depth: Depth in hierarchy

        Returns:
            dict: Accounts keyed by alias
        """
        accounts = {}

        paginator = self.org_client.get_paginator("list_accounts_for_parent")
        for page in paginator.paginate(ParentId=parent_id):
            for account in page["Accounts"]:
                if account["Status"] != "ACTIVE":
                    logger.debug(f"Skipping non-active account: {account['Name']} ({account['Status']})")
                    continue

                metadata = self._fetch_account_metadata(account["Id"], ou_path, depth)

                # Use preserved alias or generate from name
                key = metadata.alias or self._generate_alias(account["Name"])
                metadata.alias = key
                accounts[key] = metadata

                logger.debug(f"  Account: {key} ({metadata.account_id})")

        return accounts

    def _fetch_ous_recursive(
        self, parent_id: str, parent_path: str, depth: int
    ) -> dict[str, OUNode]:
        """
        Recursively fetch all OUs under a parent.

        Args:
            parent_id: Parent ID (root or OU)
            parent_path: Path to parent
            depth: Current depth in hierarchy

        Returns:
            dict: OUs keyed by name
        """
        ous = {}

        paginator = self.org_client.get_paginator("list_organizational_units_for_parent")
        for page in paginator.paginate(ParentId=parent_id):
            for ou in page["OrganizationalUnits"]:
                ou_id = ou["Id"]
                ou_name = ou["Name"]
                ou_path = f"{parent_path}/{ou_name}"

                logger.info(f"Scanning OU: {ou_path}")

                # Fetch accounts in this OU
                accounts = self._fetch_accounts_for_parent(ou_id, ou_path, depth + 1)

                # Recursively fetch child OUs
                child_ous = self._fetch_ous_recursive(ou_id, ou_path, depth + 1)

                ous[ou_name] = OUNode(
                    id=ou_id,
                    name=ou_name,
                    accounts=accounts,
                    ous=child_ous,
                )

        return ous

    def load_existing_aliases(self, config_path: Path) -> None:
        """
        Load existing account aliases from aws.yml.

        Preserves user-defined aliases across syncs.

        Args:
            config_path: Path to aws.yml
        """
        if not config_path.exists():
            logger.debug("No existing config to load aliases from")
            return

        try:
            with open(config_path) as f:
                config = yaml.safe_load(f) or {}
        except Exception as e:
            logger.warning(f"Failed to load existing config: {e}")
            return

        # Schema v2.0 - extract from flat accounts index
        if config.get("schema_version", "1.0").startswith("2"):
            for alias, data in config.get("accounts", {}).items():
                account_id = str(data.get("account_id", ""))
                if account_id:
                    self._alias_map[account_id] = alias
                    logger.debug(f"Loaded alias: {alias} -> {account_id}")
        else:
            # Schema v1.x - flat accounts dict with account_number
            for alias, data in config.get("accounts", {}).items():
                account_id = str(data.get("account_number") or data.get("account_id", ""))
                if account_id:
                    self._alias_map[account_id] = alias
                    logger.debug(f"Loaded alias: {alias} -> {account_id}")

        logger.info(f"Loaded {len(self._alias_map)} existing aliases")

    def sync(self) -> OrganizationTree:
        """
        Perform full organization sync.

        Returns:
            OrganizationTree: Complete organization hierarchy
        """
        self._connect()

        org_id, master_account_id = self._get_organization_info()
        root_id = self._get_root_id()

        logger.info(f"Organization: {org_id}")
        logger.info(f"Master account: {master_account_id}")
        logger.info(f"Root ID: {root_id}")
        logger.info("")

        # Fetch accounts directly under root
        logger.info("Scanning Root...")
        root_accounts = self._fetch_accounts_for_parent(root_id, "/", 0)

        # Recursively fetch all OUs
        root_ous = self._fetch_ous_recursive(root_id, "", 0)

        root_node = OUNode(
            id=root_id,
            name="Root",
            accounts=root_accounts,
            ous=root_ous,
        )

        return OrganizationTree(
            org_id=org_id,
            master_account_id=master_account_id,
            synced_at=datetime.now(),
            root=root_node,
        )


def _ou_node_to_dict(node: OUNode) -> dict[str, Any]:
    """Convert OUNode to dict for YAML serialization."""
    return {
        "id": node.id,
        "name": node.name,
        "accounts": {alias: _account_to_dict(acc) for alias, acc in node.accounts.items()},
        "ous": {name: _ou_node_to_dict(ou) for name, ou in node.ous.items()},
    }


def _account_to_dict(acc: AccountMetadata) -> dict[str, Any]:
    """Convert AccountMetadata to dict for YAML serialization."""
    result = {
        "account_id": acc.account_id,
        "account_name": acc.account_name,
        "email": acc.email,
        "status": acc.status,
        "ou_path": acc.ou_path,
        "depth": acc.depth,
        "joined_method": acc.joined_method,
    }
    if acc.joined_timestamp:
        result["joined_timestamp"] = acc.joined_timestamp.isoformat()
    if acc.tags:
        result["tags"] = acc.tags
    return result


def _build_flat_index(root: OUNode) -> dict[str, dict[str, Any]]:
    """Build flat accounts dict for backward compatibility."""
    index = {}
    _collect_accounts(root, index)
    return index


def _collect_accounts(node: OUNode, index: dict[str, dict[str, Any]]) -> None:
    """Recursively collect accounts into flat index."""
    for alias, acc in node.accounts.items():
        index[alias] = {
            "account_id": acc.account_id,
            "account_name": acc.account_name,
            "account_number": acc.account_id,  # Backward compat alias
            "ou_path": acc.ou_path,
        }
    for ou in node.ous.values():
        _collect_accounts(ou, index)


def _count_accounts(node: OUNode) -> int:
    """Count total accounts in tree."""
    count = len(node.accounts)
    for ou in node.ous.values():
        count += _count_accounts(ou)
    return count


def _count_ous(node: OUNode) -> int:
    """Count total OUs in tree."""
    count = len(node.ous)
    for ou in node.ous.values():
        count += _count_ous(ou)
    return count


def tree_to_yaml(tree: OrganizationTree, existing_config: dict[str, Any]) -> dict[str, Any]:
    """
    Convert OrganizationTree to aws.yml dict structure.

    Args:
        tree: Organization tree from sync
        existing_config: Existing aws.yml config to preserve settings from

    Returns:
        dict: Complete aws.yml config structure
    """
    return {
        "schema_version": "2.0",
        "default_region": existing_config.get("default_region", "us-east-1"),
        "log_path": existing_config.get("log_path", ".data/logs"),
        "sso_config": existing_config.get("sso_config", {}),
        "organization": {
            "id": tree.org_id,
            "master_account_id": tree.master_account_id,
            "synced_at": tree.synced_at.isoformat(),
            "root": _ou_node_to_dict(tree.root),
        },
        "accounts": _build_flat_index(tree.root),
    }


def main() -> int:
    """
    Main execution function.

    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    parser = argparse.ArgumentParser(
        description="Sync AWS Organizations hierarchy to aws.yml",
        epilog="Example: org_sync.py --profile root --dry-run",
    )
    parser.add_argument(
        "--profile",
        default="root",
        help="AWS profile for Organizations API (default: root)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output path (default: aws.yml from config)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show changes without writing",
    )
    args = parser.parse_args()

    setup_logging("org_sync")

    try:
        # Determine config path
        if args.output:
            config_path = Path(args.output)
        else:
            config_path = get_config_path()

        logger.info("AWS Organizations Sync")
        logger.info(f"  Profile: {args.profile}")
        logger.info(f"  Output: {config_path}")
        logger.info(f"  Dry run: {args.dry_run}")
        logger.info("")

        # Load existing config for alias preservation
        syncer = OrganizationSync(profile_name=args.profile)
        syncer.load_existing_aliases(config_path)

        # Perform sync
        logger.info("Fetching AWS Organizations hierarchy...")
        logger.info("")
        tree = syncer.sync()

        # Load existing config for merging
        existing = {}
        if config_path.exists():
            with open(config_path) as f:
                existing = yaml.safe_load(f) or {}

        # Convert to YAML structure
        new_config = tree_to_yaml(tree, existing)

        # Summary
        total_accounts = _count_accounts(tree.root)
        total_ous = _count_ous(tree.root)

        logger.info("")
        logger.info("Sync complete:")
        logger.info(f"  Total accounts: {total_accounts}")
        logger.info(f"  Total OUs: {total_ous}")

        if args.dry_run:
            logger.info("")
            logger.info("Dry run - would write:")
            logger.info("")
            print(yaml.dump(new_config, default_flow_style=False, sort_keys=False))
        else:
            # Atomic write: write to temp file, then rename
            temp_path = config_path.with_suffix(".yml.tmp")
            with open(temp_path, "w") as f:
                yaml.dump(new_config, f, default_flow_style=False, sort_keys=False)
            temp_path.rename(config_path)

            logger.success(f"Updated {config_path}")

        return 0

    except FileNotFoundError as e:
        logger.error(f"Configuration file not found: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Sync failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
