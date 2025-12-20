"""CloudFront distribution discovery."""

from botocore.exceptions import ClientError
from loguru import logger

from ..core.schemas import CloudFrontDistribution, CloudFrontOrigin
from ..core.session import create_session


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

                # Extract origin domain names (simple list) and detailed configs
                origins_data = dist_data.get("Origins", {})
                origins = []
                origin_details = []
                for origin in origins_data.get("Items", []):
                    domain = origin.get("DomainName", "")
                    if domain:
                        origins.append(domain)

                    # Determine origin type
                    origin_type = None
                    if origin.get("S3OriginConfig"):
                        origin_type = "s3"
                    elif origin.get("CustomOriginConfig"):
                        origin_type = "custom"

                    origin_detail = CloudFrontOrigin(
                        id=origin.get("Id", ""),
                        domain_name=domain,
                        origin_type=origin_type,
                        s3_origin_config=origin.get("S3OriginConfig"),
                        custom_origin_config=origin.get("CustomOriginConfig"),
                    )
                    origin_details.append(origin_detail)

                # Extract ACM certificate ARN
                viewer_cert = dist_data.get("ViewerCertificate", {})
                acm_certificate_arn = viewer_cert.get("ACMCertificateArn")

                # Extract WAF Web ACL ID
                web_acl_id = dist_data.get("WebACLId")

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
                    default_root_object=dist_data.get("DefaultRootObject"),
                    comment=dist_data.get("Comment"),
                    last_modified_time=last_modified.isoformat() if last_modified else None,
                    # Relationship fields
                    acm_certificate_arn=acm_certificate_arn,
                    web_acl_id=web_acl_id if web_acl_id else None,
                    origin_details=origin_details,
                )
                distributions.append(distribution)

        logger.debug(f"Discovered {len(distributions)} CloudFront distributions")
        return distributions
    except ClientError as e:
        logger.warning(f"Failed to discover CloudFront distributions: {e}")
        return []
