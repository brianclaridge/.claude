"""Classic Elastic Load Balancer (ELB) discovery."""

from botocore.exceptions import ClientError
from loguru import logger

from aws_utils.core.schemas import ClassicLoadBalancer
from aws_utils.core.session import create_session, get_default_region


def discover_classic_load_balancers(
    profile_name: str | None = None,
    region: str | None = None,
) -> list[ClassicLoadBalancer]:
    """Discover all Classic Load Balancers in a region.

    Args:
        profile_name: AWS CLI profile name
        region: AWS region

    Returns:
        List of ClassicLoadBalancer objects
    """
    region = region or get_default_region()
    session = create_session(profile_name, region)
    elb = session.client("elb")

    try:
        classic_lbs = []
        paginator = elb.get_paginator("describe_load_balancers")

        for page in paginator.paginate():
            for lb in page.get("LoadBalancerDescriptions", []):
                # Extract instance IDs
                instances = [
                    inst.get("InstanceId", "") for inst in lb.get("Instances", [])
                ]

                # Get health check target
                health_check = lb.get("HealthCheck", {})
                health_target = health_check.get("Target")

                classic_lb = ClassicLoadBalancer(
                    name=lb["LoadBalancerName"],
                    dns_name=lb.get("DNSName", ""),
                    scheme=lb.get("Scheme", "internet-facing"),
                    vpc_id=lb.get("VPCId"),  # None for EC2-Classic
                    created_time=lb.get("CreatedTime", "").isoformat()
                    if lb.get("CreatedTime")
                    else None,
                    availability_zones=lb.get("AvailabilityZones", []),
                    subnets=lb.get("Subnets", []),
                    security_groups=lb.get("SecurityGroups", []),
                    instances=instances,
                    health_check_target=health_target,
                    region=region,
                )
                classic_lbs.append(classic_lb)

        logger.debug(f"Discovered {len(classic_lbs)} Classic Load Balancers in {region}")
        return classic_lbs
    except ClientError as e:
        logger.warning(f"Failed to discover Classic LBs: {e}")
        return []
