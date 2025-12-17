"""SNS topic discovery."""

from botocore.exceptions import ClientError
from loguru import logger

from aws_inspector.core.schemas import SNSTopic
from aws_inspector.core.session import create_session, get_default_region


def discover_sns_topics(
    profile_name: str | None = None,
    region: str | None = None,
) -> list[SNSTopic]:
    """Discover all SNS topics in an account/region.

    Args:
        profile_name: AWS CLI profile name
        region: AWS region

    Returns:
        List of SNSTopic objects
    """
    region = region or get_default_region()
    session = create_session(profile_name, region)
    sns = session.client("sns")

    try:
        topics = []
        paginator = sns.get_paginator("list_topics")

        for page in paginator.paginate():
            for topic_data in page.get("Topics", []):
                topic_arn = topic_data["TopicArn"]
                # Extract topic name from ARN
                # ARN format: arn:aws:sns:{region}:{account_id}:{topic_name}
                topic_name = topic_arn.split(":")[-1]

                topic = SNSTopic(
                    name=topic_name,
                    arn=topic_arn,
                    region=region,
                )
                topics.append(topic)

        logger.debug(f"Discovered {len(topics)} SNS topics in {region}")
        return topics
    except ClientError as e:
        logger.warning(f"Failed to discover SNS topics: {e}")
        return []
