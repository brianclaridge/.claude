"""Lambda function discovery."""

from botocore.exceptions import ClientError
from loguru import logger

from aws_utils.core.schemas import LambdaFunction
from aws_utils.core.session import create_session


def discover_lambda_functions(
    profile_name: str | None = None,
    region: str | None = None,
) -> list[LambdaFunction]:
    """Discover all Lambda functions in a region.

    Args:
        profile_name: AWS CLI profile name
        region: AWS region

    Returns:
        List of LambdaFunction objects
    """
    session = create_session(profile_name, region)
    lambda_client = session.client("lambda")
    region_name = session.region_name or "us-east-1"

    try:
        functions = []
        paginator = lambda_client.get_paginator("list_functions")

        for page in paginator.paginate():
            for func_data in page.get("Functions", []):
                function = LambdaFunction(
                    function_name=func_data["FunctionName"],
                    runtime=func_data.get("Runtime"),
                    memory_size=func_data.get("MemorySize", 128),
                    timeout=func_data.get("Timeout", 3),
                    last_modified=func_data.get("LastModified", ""),
                    arn=func_data["FunctionArn"],
                    region=region_name,
                )
                functions.append(function)

        logger.debug(f"Discovered {len(functions)} Lambda functions in {region_name}")
        return functions
    except ClientError as e:
        logger.warning(f"Failed to discover Lambda functions: {e}")
        return []
