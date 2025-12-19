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
                # Extract VPC configuration
                vpc_config = func_data.get("VpcConfig", {})
                vpc_id = vpc_config.get("VpcId")
                subnet_ids = vpc_config.get("SubnetIds", [])
                security_group_ids = vpc_config.get("SecurityGroupIds", [])

                # Extract dead letter config
                dlq_config = func_data.get("DeadLetterConfig", {})
                dead_letter_target_arn = dlq_config.get("TargetArn")

                # Extract layer ARNs
                layers = func_data.get("Layers", [])
                layer_arns = [layer.get("Arn") for layer in layers if layer.get("Arn")]

                function = LambdaFunction(
                    function_name=func_data["FunctionName"],
                    runtime=func_data.get("Runtime"),
                    memory_size=func_data.get("MemorySize", 128),
                    timeout=func_data.get("Timeout", 3),
                    last_modified=func_data.get("LastModified", ""),
                    arn=func_data["FunctionArn"],
                    region=region_name,
                    # VPC configuration
                    vpc_id=vpc_id if vpc_id else None,
                    subnet_ids=subnet_ids,
                    security_group_ids=security_group_ids,
                    # IAM configuration
                    execution_role_arn=func_data.get("Role"),
                    # Dead letter config
                    dead_letter_target_arn=dead_letter_target_arn,
                    # Layers
                    layer_arns=layer_arns,
                )
                functions.append(function)

        logger.debug(f"Discovered {len(functions)} Lambda functions in {region_name}")
        return functions
    except ClientError as e:
        logger.warning(f"Failed to discover Lambda functions: {e}")
        return []
