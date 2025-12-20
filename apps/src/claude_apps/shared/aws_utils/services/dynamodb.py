"""DynamoDB table discovery."""

from botocore.exceptions import ClientError
from loguru import logger

from ..core.schemas import DynamoDBTable
from ..core.session import create_session


def discover_dynamodb_tables(
    profile_name: str | None = None,
    region: str | None = None,
) -> list[DynamoDBTable]:
    """Discover all DynamoDB tables in a region.

    Args:
        profile_name: AWS CLI profile name
        region: AWS region

    Returns:
        List of DynamoDBTable objects
    """
    session = create_session(profile_name, region)
    dynamodb = session.client("dynamodb")
    region_name = session.region_name or "us-east-1"

    try:
        tables = []
        paginator = dynamodb.get_paginator("list_tables")

        table_names = []
        for page in paginator.paginate():
            table_names.extend(page.get("TableNames", []))

        # Get details for each table
        for table_name in table_names:
            try:
                response = dynamodb.describe_table(TableName=table_name)
                table_data = response["Table"]

                table = DynamoDBTable(
                    table_name=table_data["TableName"],
                    status=table_data["TableStatus"],
                    item_count=table_data.get("ItemCount", 0),
                    size_bytes=table_data.get("TableSizeBytes", 0),
                    arn=table_data["TableArn"],
                    region=region_name,
                )
                tables.append(table)
            except ClientError as e:
                logger.warning(f"Failed to describe table {table_name}: {e}")

        logger.debug(f"Discovered {len(tables)} DynamoDB tables in {region_name}")
        return tables
    except ClientError as e:
        logger.warning(f"Failed to discover DynamoDB tables: {e}")
        return []
