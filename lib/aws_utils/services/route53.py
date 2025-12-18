"""Route53 hosted zone and record discovery."""

from botocore.exceptions import ClientError
from loguru import logger

from aws_utils.core.schemas import Route53Record, Route53Zone
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
                if "ResourceRecords" in record_data:
                    values = [rr["Value"] for rr in record_data["ResourceRecords"]]
                elif "AliasTarget" in record_data:
                    alias = record_data["AliasTarget"]
                    values = [f"ALIAS {alias['DNSName']}"]

                record = Route53Record(
                    zone_id=zone_id,
                    name=record_data["Name"],
                    record_type=record_data["Type"],
                    ttl=record_data.get("TTL"),
                    values=values,
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
