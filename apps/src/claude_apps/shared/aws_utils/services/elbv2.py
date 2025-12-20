"""Elastic Load Balancing v2 (ALB/NLB) discovery."""

from botocore.exceptions import ClientError
from loguru import logger

from ..core.schemas import ApplicationLoadBalancer, NetworkLoadBalancer
from ..core.session import create_session, get_default_region


def discover_application_load_balancers(
    profile_name: str | None = None,
    region: str | None = None,
) -> list[ApplicationLoadBalancer]:
    """Discover all Application Load Balancers in a region.

    Args:
        profile_name: AWS CLI profile name
        region: AWS region

    Returns:
        List of ApplicationLoadBalancer objects
    """
    region = region or get_default_region()
    session = create_session(profile_name, region)
    elbv2 = session.client("elbv2")

    try:
        albs = []
        paginator = elbv2.get_paginator("describe_load_balancers")

        for page in paginator.paginate():
            for lb in page.get("LoadBalancers", []):
                # Only process Application Load Balancers
                if lb.get("Type") != "application":
                    continue

                # Extract availability zone names
                az_names = [
                    az.get("ZoneName", "") for az in lb.get("AvailabilityZones", [])
                ]

                alb = ApplicationLoadBalancer(
                    name=lb["LoadBalancerName"],
                    arn=lb["LoadBalancerArn"],
                    dns_name=lb.get("DNSName", ""),
                    scheme=lb.get("Scheme", "internet-facing"),
                    vpc_id=lb.get("VpcId", ""),
                    state=lb.get("State", {}).get("Code", "unknown"),
                    type="application",
                    created_time=lb.get("CreatedTime", "").isoformat()
                    if lb.get("CreatedTime")
                    else None,
                    availability_zones=az_names,
                    security_groups=lb.get("SecurityGroups", []),
                    ip_address_type=lb.get("IpAddressType"),
                    region=region,
                )
                albs.append(alb)

        logger.debug(f"Discovered {len(albs)} Application Load Balancers in {region}")
        return albs
    except ClientError as e:
        logger.warning(f"Failed to discover ALBs: {e}")
        return []


def discover_network_load_balancers(
    profile_name: str | None = None,
    region: str | None = None,
) -> list[NetworkLoadBalancer]:
    """Discover all Network Load Balancers in a region.

    Args:
        profile_name: AWS CLI profile name
        region: AWS region

    Returns:
        List of NetworkLoadBalancer objects
    """
    region = region or get_default_region()
    session = create_session(profile_name, region)
    elbv2 = session.client("elbv2")

    try:
        nlbs = []
        paginator = elbv2.get_paginator("describe_load_balancers")

        for page in paginator.paginate():
            for lb in page.get("LoadBalancers", []):
                # Only process Network Load Balancers
                if lb.get("Type") != "network":
                    continue

                # Extract availability zone names
                az_names = [
                    az.get("ZoneName", "") for az in lb.get("AvailabilityZones", [])
                ]

                nlb = NetworkLoadBalancer(
                    name=lb["LoadBalancerName"],
                    arn=lb["LoadBalancerArn"],
                    dns_name=lb.get("DNSName", ""),
                    scheme=lb.get("Scheme", "internet-facing"),
                    vpc_id=lb.get("VpcId", ""),
                    state=lb.get("State", {}).get("Code", "unknown"),
                    type="network",
                    created_time=lb.get("CreatedTime", "").isoformat()
                    if lb.get("CreatedTime")
                    else None,
                    availability_zones=az_names,
                    ip_address_type=lb.get("IpAddressType"),
                    region=region,
                )
                nlbs.append(nlb)

        logger.debug(f"Discovered {len(nlbs)} Network Load Balancers in {region}")
        return nlbs
    except ClientError as e:
        logger.warning(f"Failed to discover NLBs: {e}")
        return []
