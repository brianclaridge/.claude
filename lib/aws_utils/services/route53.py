"""Route53 hosted zone and record discovery."""

from botocore.exceptions import ClientError
from loguru import logger

from aws_utils.core.schemas import Route53Domain, Route53Record, Route53Zone
from aws_utils.core.session import create_session


def discover_route53_zones(
    profile_name: str | None = None,
    region: str | None = None,
) -> list[Route53Zone]:
    """Discover all Route53 hosted zones.

    Note: Route53 is a global service, region parameter is ignored.

    Args:
        profile_name: AWS CLI profile name
        region: Ignored (Route53 is global)

    Returns:
        List of Route53Zone objects
    """
    session = create_session(profile_name, region)
    route53 = session.client("route53")

    try:
        zones = []
        paginator = route53.get_paginator("list_hosted_zones")

        for page in paginator.paginate():
            for zone_data in page.get("HostedZones", []):
                # Zone ID comes as /hostedzone/Z123..., extract just the ID
                zone_id = zone_data["Id"].replace("/hostedzone/", "")

                zone = Route53Zone(
                    zone_id=zone_id,
                    name=zone_data["Name"],
                    is_private=zone_data.get("Config", {}).get("PrivateZone", False),
                    record_count=zone_data.get("ResourceRecordSetCount", 0),
                )
                zones.append(zone)

        logger.debug(f"Discovered {len(zones)} Route53 hosted zones")
        return zones
    except ClientError as e:
        logger.warning(f"Failed to discover Route53 zones: {e}")
        return []


def discover_route53_records(
    zone_id: str,
    profile_name: str | None = None,
    region: str | None = None,
) -> list[Route53Record]:
    """Discover all records in a Route53 hosted zone.

    Args:
        zone_id: Hosted zone ID
        profile_name: AWS CLI profile name
        region: Ignored (Route53 is global)

    Returns:
        List of Route53Record objects
    """
    session = create_session(profile_name, region)
    route53 = session.client("route53")

    try:
        records = []
        paginator = route53.get_paginator("list_resource_record_sets")

        for page in paginator.paginate(HostedZoneId=zone_id):
            for record_data in page.get("ResourceRecordSets", []):
                # Extract values from ResourceRecords or AliasTarget
                values = []
                is_alias = False
                alias_target_dns_name = None
                alias_target_hosted_zone_id = None
                target_resource_type = None

                if "ResourceRecords" in record_data:
                    values = [rr["Value"] for rr in record_data["ResourceRecords"]]
                elif "AliasTarget" in record_data:
                    alias = record_data["AliasTarget"]
                    is_alias = True
                    alias_target_dns_name = alias.get("DNSName")
                    alias_target_hosted_zone_id = alias.get("HostedZoneId")
                    values = [f"ALIAS {alias_target_dns_name}"]

                    # Infer target resource type from DNS name pattern
                    if alias_target_dns_name:
                        dns_lower = alias_target_dns_name.lower()
                        if ".elb.amazonaws.com" in dns_lower:
                            target_resource_type = "alb" if "app-" in dns_lower else "nlb"
                        elif ".cloudfront.net" in dns_lower:
                            target_resource_type = "cloudfront"
                        elif ".s3.amazonaws.com" in dns_lower or ".s3-website" in dns_lower:
                            target_resource_type = "s3"
                        elif ".execute-api." in dns_lower:
                            target_resource_type = "api_gateway"
                        elif ".elasticbeanstalk.com" in dns_lower:
                            target_resource_type = "elastic_beanstalk"

                record = Route53Record(
                    zone_id=zone_id,
                    name=record_data["Name"],
                    record_type=record_data["Type"],
                    ttl=record_data.get("TTL"),
                    values=values,
                    # Alias configuration
                    is_alias=is_alias,
                    alias_target_dns_name=alias_target_dns_name,
                    alias_target_hosted_zone_id=alias_target_hosted_zone_id,
                    target_resource_type=target_resource_type,
                    # Health check
                    health_check_id=record_data.get("HealthCheckId"),
                )
                records.append(record)

        logger.debug(f"Discovered {len(records)} records in zone {zone_id}")
        return records
    except ClientError as e:
        logger.warning(f"Failed to discover Route53 records for zone {zone_id}: {e}")
        return []


def discover_all_route53_records(
    profile_name: str | None = None,
    region: str | None = None,
) -> list[Route53Record]:
    """Discover all Route53 records across all hosted zones.

    Args:
        profile_name: AWS CLI profile name
        region: Ignored (Route53 is global)

    Returns:
        List of Route53Record objects from all zones
    """
    zones = discover_route53_zones(profile_name, region)
    all_records = []

    for zone in zones:
        records = discover_route53_records(zone.zone_id, profile_name, region)
        all_records.extend(records)

    logger.debug(f"Discovered {len(all_records)} total Route53 records")
    return all_records


def discover_route53_domains(
    profile_name: str | None = None,
) -> list[Route53Domain]:
    """Discover all Route53 registered domains.

    Note: Route53 Domains is a global service (us-east-1 endpoint only).

    Args:
        profile_name: AWS CLI profile name

    Returns:
        List of Route53Domain objects
    """
    # Route53 Domains API only available in us-east-1
    session = create_session(profile_name, "us-east-1")
    client = session.client("route53domains")

    try:
        domains = []
        paginator = client.get_paginator("list_domains")

        for page in paginator.paginate():
            for domain_data in page.get("Domains", []):
                domain_name = domain_data.get("DomainName", "")

                # Get detailed info for each domain
                try:
                    detail = client.get_domain_detail(DomainName=domain_name)

                    expiration = detail.get("ExpirationDate")
                    creation = detail.get("CreationDate")

                    domain = Route53Domain(
                        domain_name=domain_name,
                        auto_renew=domain_data.get("AutoRenew", True),
                        transfer_lock=domain_data.get("TransferLock", True),
                        expiration_date=expiration.isoformat() if expiration else None,
                        creation_date=creation.isoformat() if creation else None,
                        registrar_name=detail.get("RegistrarName"),
                        registrar_url=detail.get("RegistrarUrl"),
                        abuse_contact_email=detail.get("AbuseContactEmail"),
                        abuse_contact_phone=detail.get("AbuseContactPhone"),
                    )
                    domains.append(domain)
                except ClientError as e:
                    logger.warning(f"Failed to get domain detail for {domain_name}: {e}")

        logger.debug(f"Discovered {len(domains)} Route53 registered domains")
        return domains
    except ClientError as e:
        logger.warning(f"Failed to discover Route53 domains: {e}")
        return []
