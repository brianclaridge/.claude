"""SQS queue discovery."""

from botocore.exceptions import ClientError
from loguru import logger

from aws_inspector.core.schemas import SQSQueue
from aws_inspector.core.session import create_session, get_default_region


def discover_sqs_queues(
    profile_name: str | None = None,
    region: str | None = None,
) -> list[SQSQueue]:
    """Discover all SQS queues in an account/region.

    Args:
        profile_name: AWS CLI profile name
        region: AWS region

    Returns:
        List of SQSQueue objects
    """
    region = region or get_default_region()
    session = create_session(profile_name, region)
    sqs = session.client("sqs")

    try:
        response = sqs.list_queues()
        queues = []

        for queue_url in response.get("QueueUrls", []):
            # Extract queue name from URL
            # URL format: https://sqs.{region}.amazonaws.com/{account_id}/{queue_name}
            queue_name = queue_url.split("/")[-1]

            # Get queue ARN
            try:
                attrs = sqs.get_queue_attributes(
                    QueueUrl=queue_url,
                    AttributeNames=["QueueArn"],
                )
                queue_arn = attrs.get("Attributes", {}).get("QueueArn", "")
            except ClientError:
                # Construct ARN from URL
                parts = queue_url.split("/")
                account_id = parts[-2] if len(parts) >= 2 else ""
                queue_arn = f"arn:aws:sqs:{region}:{account_id}:{queue_name}"

            queue = SQSQueue(
                name=queue_name,
                url=queue_url,
                arn=queue_arn,
                region=region,
            )
            queues.append(queue)

        logger.debug(f"Discovered {len(queues)} SQS queues in {region}")
        return queues
    except ClientError as e:
        logger.warning(f"Failed to discover SQS queues: {e}")
        return []
