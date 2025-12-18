"""CloudFront distribution discovery."""

from botocore.exceptions import ClientError
from loguru import logger

from aws_utils.core.schemas import CloudFrontDistribution
from aws_utils.core.session import create_session


def discover_distributions(
    profile_name: str | None = None,
) -> list[CloudFrontDistribution]:
    """Discover CloudFront distributions.

    Note: CloudFront is a global service, no region parameter needed.

    Args:
        profile_name: AWS CLI profile name

    Returns:
        List of CloudFrontDistribution objects
    """
    # CloudFront is global, use us-east-1 for API calls
    session = create_session(profile_name, "us-east-1")
    client = session.client("cloudfront")

    try:
        distributions = []
        paginator = client.get_paginator("list_distributions")

        for page in paginator.paginate():
            distribution_list = page.get("DistributionList", {})
            for dist_data in distribution_list.get("Items", []):
                # Extract aliases (CNAMEs)
                aliases_data = dist_data.get("Aliases", {})
                aliases = aliases_data.get("Items", []) if aliases_data else []

                # Extract origin domain names
                origins_data = dist_data.get("Origins", {})
                origins = []
                for origin in origins_data.get("Items", []):
                    domain = origin.get("DomainName", "")
                    if domain:
                        origins.append(domain)

                # Extract default cache behavior
                default_behavior = dist_data.get("DefaultCacheBehavior", {})
                default_ttl = default_behavior.get("DefaultTTL")
                viewer_protocol = default_behavior.get("ViewerProtocolPolicy")

                # Format last modified date
                last_modified = dist_data.get("LastModifiedTime")

                distribution = CloudFrontDistribution(
                    id=dist_data.get("Id", ""),
                    arn=dist_data.get("ARN", ""),
                    domain_name=dist_data.get("DomainName", ""),
                    status=dist_data.get("Status", ""),
                    enabled=dist_data.get("Enabled", True),
                    price_class=dist_data.get("PriceClass"),
                    aliases=aliases,
                    origins=origins,
                    default_ttl=default_ttl,
                    viewer_protocol_policy=viewer_protocol,
                    http_version=dist_data.get("HttpVersion"),
                    is_ipv6_enabled=dist_data.get("IsIPV6Enabled", False),
                    last_modified_time=last_modified.isoformat() if last_modified else None,
                )
                distributions.append(distribution)

        logger.debug(f"Discovered {len(distributions)} CloudFront distributions")
        return distributions
    except ClientError as e:
        logger.warning(f"Failed to discover CloudFront distributions: {e}")
        return []
