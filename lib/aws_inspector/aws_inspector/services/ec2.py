"""EC2 resource discovery - VPCs, subnets, gateways, elastic IPs."""

from typing import Any

import boto3
from botocore.exceptions import ClientError
from loguru import logger

from aws_inspector.core.schemas import (
    ElasticIP,
    InternetGateway,
    NATGateway,
    Subnet,
    VPC,
)
from aws_inspector.core.session import create_session, get_default_region


def discover_internet_gateways(ec2_client: Any, vpc_id: str) -> list[InternetGateway]:
    """Discover Internet Gateways attached to a VPC.

    Args:
        ec2_client: Boto3 EC2 client
        vpc_id: VPC ID to query

    Returns:
        List of InternetGateway objects
    """
    try:
        response = ec2_client.describe_internet_gateways(
            Filters=[{"Name": "attachment.vpc-id", "Values": [vpc_id]}]
        )
        gateways = []
        for igw in response.get("InternetGateways", []):
            attachments = igw.get("Attachments", [])
            state = "attached" if attachments else "detached"
            gateways.append(
                InternetGateway(
                    id=igw["InternetGatewayId"],
                    state=state,
                )
            )
        return gateways
    except ClientError as e:
        logger.warning(f"Failed to discover IGWs for {vpc_id}: {e}")
        return []


def discover_nat_gateways(ec2_client: Any, vpc_id: str) -> dict[str, NATGateway]:
    """Discover NAT Gateways in a VPC, mapped by subnet ID.

    Args:
        ec2_client: Boto3 EC2 client
        vpc_id: VPC ID to query

    Returns:
        Dict mapping subnet_id -> NATGateway
    """
    try:
        response = ec2_client.describe_nat_gateways(
            Filters=[
                {"Name": "vpc-id", "Values": [vpc_id]},
                {"Name": "state", "Values": ["available", "pending"]},
            ]
        )
        nat_map = {}
        for nat in response.get("NatGateways", []):
            subnet_id = nat.get("SubnetId")
            if not subnet_id:
                continue

            # Get elastic IP info
            addresses = nat.get("NatGatewayAddresses", [])
            eip_alloc = None
            public_ip = None
            if addresses:
                eip_alloc = addresses[0].get("AllocationId")
                public_ip = addresses[0].get("PublicIp")

            nat_map[subnet_id] = NATGateway(
                id=nat["NatGatewayId"],
                state=nat.get("State", "unknown"),
                elastic_ip=eip_alloc,
                public_ip=public_ip,
            )
        return nat_map
    except ClientError as e:
        logger.warning(f"Failed to discover NAT Gateways for {vpc_id}: {e}")
        return {}


def _get_public_subnet_ids(ec2_client: Any, vpc_id: str) -> set[str]:
    """Identify public subnets by checking route tables for IGW routes.

    A subnet is public if it has a route to an Internet Gateway.

    Args:
        ec2_client: Boto3 EC2 client
        vpc_id: VPC ID to query

    Returns:
        Set of public subnet IDs
    """
    public_subnet_ids = set()
    try:
        response = ec2_client.describe_route_tables(
            Filters=[{"Name": "vpc-id", "Values": [vpc_id]}]
        )
        for rt in response.get("RouteTables", []):
            has_igw_route = any(
                route.get("GatewayId", "").startswith("igw-")
                for route in rt.get("Routes", [])
            )
            if has_igw_route:
                for assoc in rt.get("Associations", []):
                    subnet_id = assoc.get("SubnetId")
                    if subnet_id:
                        public_subnet_ids.add(subnet_id)
    except ClientError as e:
        logger.warning(f"Failed to get route tables for {vpc_id}: {e}")
    return public_subnet_ids


def discover_subnets(
    ec2_client: Any,
    vpc_id: str,
    nat_gateways: dict[str, NATGateway] | None = None,
) -> list[Subnet]:
    """Discover subnets in a VPC.

    Args:
        ec2_client: Boto3 EC2 client
        vpc_id: VPC ID to query
        nat_gateways: Optional dict mapping subnet_id -> NATGateway

    Returns:
        List of Subnet objects
    """
    nat_gateways = nat_gateways or {}
    try:
        response = ec2_client.describe_subnets(
            Filters=[{"Name": "vpc-id", "Values": [vpc_id]}]
        )
        public_subnet_ids = _get_public_subnet_ids(ec2_client, vpc_id)

        subnets = []
        for s in response.get("Subnets", []):
            subnet_id = s["SubnetId"]
            subnet_type = "public" if subnet_id in public_subnet_ids else "private"

            subnet = Subnet(
                id=subnet_id,
                cidr=s["CidrBlock"],
                az=s["AvailabilityZone"],
                type=subnet_type,
                nat_gateway=nat_gateways.get(subnet_id),
            )
            subnets.append(subnet)
        return subnets
    except ClientError as e:
        logger.warning(f"Failed to discover subnets for {vpc_id}: {e}")
        return []


def discover_vpcs(
    profile_name: str | None = None,
    region: str | None = None,
) -> list[VPC]:
    """Discover all VPCs in an account with their subnets and gateways.

    Args:
        profile_name: AWS CLI profile name
        region: AWS region

    Returns:
        List of VPC objects with nested resources
    """
    region = region or get_default_region()
    session = create_session(profile_name, region)
    ec2 = session.client("ec2")

    try:
        response = ec2.describe_vpcs()
        vpcs = []

        for vpc_data in response.get("Vpcs", []):
            vpc_id = vpc_data["VpcId"]

            # Discover nested resources
            igws = discover_internet_gateways(ec2, vpc_id)
            nat_map = discover_nat_gateways(ec2, vpc_id)
            subnets = discover_subnets(ec2, vpc_id, nat_map)

            # Only include VPCs that have subnets
            if not subnets:
                logger.debug(f"Skipping VPC {vpc_id} - no subnets")
                continue

            vpc = VPC(
                id=vpc_id,
                cidr=vpc_data.get("CidrBlock", ""),
                is_default=vpc_data.get("IsDefault", False),
                internet_gateways=igws,
                subnets=subnets,
            )
            vpcs.append(vpc)

        logger.debug(f"Discovered {len(vpcs)} VPCs in {region}")
        return vpcs
    except ClientError as e:
        logger.warning(f"Failed to discover VPCs: {e}")
        return []


def discover_elastic_ips(
    profile_name: str | None = None,
    region: str | None = None,
) -> list[ElasticIP]:
    """Discover all Elastic IPs in an account.

    Args:
        profile_name: AWS CLI profile name
        region: AWS region

    Returns:
        List of ElasticIP objects
    """
    region = region or get_default_region()
    session = create_session(profile_name, region)
    ec2 = session.client("ec2")

    try:
        response = ec2.describe_addresses()
        eips = []

        for addr in response.get("Addresses", []):
            eip = ElasticIP(
                allocation_id=addr.get("AllocationId", ""),
                public_ip=addr.get("PublicIp", ""),
                association_id=addr.get("AssociationId"),
                domain=addr.get("Domain", "vpc"),
                region=region,
            )
            eips.append(eip)

        logger.debug(f"Discovered {len(eips)} Elastic IPs in {region}")
        return eips
    except ClientError as e:
        logger.warning(f"Failed to discover Elastic IPs: {e}")
        return []
