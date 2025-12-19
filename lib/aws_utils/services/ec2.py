"""EC2 resource discovery - VPCs, subnets, gateways, elastic IPs."""

from typing import Any

from botocore.exceptions import ClientError
from loguru import logger

from aws_utils.core.schemas import (
    VPC,
    ElasticIP,
    InternetGateway,
    NATGateway,
    Subnet,
    EC2Instance,
)
from aws_utils.core.session import create_session, get_default_region, get_account_id


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


def discover_ec2_instances(
    profile_name: str | None = None,
    region: str | None = None,
) -> list[EC2Instance]:
    """Discover all EC2 instances in an account.

    Args:
        profile_name: AWS CLI profile name
        region: AWS region

    Returns:
        List of EC2Instance objects
    """
    region = region or get_default_region()
    session = create_session(profile_name, region)
    ec2 = session.client("ec2")

    try:
        # Get account ID for ARN construction
        account_id = get_account_id(profile_name)

        instances = []
        paginator = ec2.get_paginator("describe_instances")

        for page in paginator.paginate():
            for reservation in page.get("Reservations", []):
                for inst in reservation.get("Instances", []):
                    instance_id = inst["InstanceId"]

                    # Extract Name tag
                    name = None
                    tags_dict = {}
                    for tag in inst.get("Tags", []):
                        tags_dict[tag["Key"]] = tag["Value"]
                        if tag["Key"] == "Name":
                            name = tag["Value"]

                    # Extract security group IDs
                    security_groups = [
                        sg["GroupId"] for sg in inst.get("SecurityGroups", [])
                    ]

                    # Extract IAM instance profile ARN
                    iam_profile = inst.get("IamInstanceProfile", {})
                    iam_profile_arn = iam_profile.get("Arn")

                    # Build ARN
                    arn = f"arn:aws:ec2:{region}:{account_id}:instance/{instance_id}"

                    instance = EC2Instance(
                        instance_id=instance_id,
                        instance_type=inst.get("InstanceType", "unknown"),
                        state=inst.get("State", {}).get("Name", "unknown"),
                        private_ip=inst.get("PrivateIpAddress"),
                        public_ip=inst.get("PublicIpAddress"),
                        vpc_id=inst.get("VpcId"),
                        subnet_id=inst.get("SubnetId"),
                        launch_time=inst.get("LaunchTime", "").isoformat()
                        if inst.get("LaunchTime")
                        else None,
                        name=name,
                        platform=inst.get("Platform"),  # 'windows' or None
                        image_id=inst.get("ImageId"),
                        key_name=inst.get("KeyName"),
                        security_groups=security_groups,
                        iam_instance_profile=iam_profile_arn,
                        tags=tags_dict,
                        arn=arn,
                        region=region,
                    )
                    instances.append(instance)

        logger.debug(f"Discovered {len(instances)} EC2 instances in {region}")
        return instances
    except ClientError as e:
        logger.warning(f"Failed to discover EC2 instances: {e}")
        return []


# =============================================================================
# Standalone Network Resource Discovery
# These functions discover ALL resources in the account (not per-VPC).
# They follow the standard pattern: discover_*(profile_name, region) -> list[Schema]
# =============================================================================


def discover_internet_gateways_all(
    profile_name: str | None = None,
    region: str | None = None,
) -> list[InternetGateway]:
    """Discover all Internet Gateways in an account.

    Args:
        profile_name: AWS CLI profile name
        region: AWS region

    Returns:
        List of InternetGateway objects
    """
    region = region or get_default_region()
    session = create_session(profile_name, region)
    ec2 = session.client("ec2")

    try:
        response = ec2.describe_internet_gateways()
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

        logger.debug(f"Discovered {len(gateways)} Internet Gateways in {region}")
        return gateways
    except ClientError as e:
        logger.warning(f"Failed to discover Internet Gateways: {e}")
        return []


def discover_nat_gateways_all(
    profile_name: str | None = None,
    region: str | None = None,
) -> list[NATGateway]:
    """Discover all NAT Gateways in an account.

    Args:
        profile_name: AWS CLI profile name
        region: AWS region

    Returns:
        List of NATGateway objects
    """
    region = region or get_default_region()
    session = create_session(profile_name, region)
    ec2 = session.client("ec2")

    try:
        response = ec2.describe_nat_gateways(
            Filters=[{"Name": "state", "Values": ["available", "pending"]}]
        )
        gateways = []

        for nat in response.get("NatGateways", []):
            # Get elastic IP info
            addresses = nat.get("NatGatewayAddresses", [])
            eip_alloc = None
            public_ip = None
            if addresses:
                eip_alloc = addresses[0].get("AllocationId")
                public_ip = addresses[0].get("PublicIp")

            gateways.append(
                NATGateway(
                    id=nat["NatGatewayId"],
                    state=nat.get("State", "unknown"),
                    elastic_ip=eip_alloc,
                    public_ip=public_ip,
                )
            )

        logger.debug(f"Discovered {len(gateways)} NAT Gateways in {region}")
        return gateways
    except ClientError as e:
        logger.warning(f"Failed to discover NAT Gateways: {e}")
        return []


def discover_subnets_all(
    profile_name: str | None = None,
    region: str | None = None,
) -> list[Subnet]:
    """Discover all Subnets in an account.

    Args:
        profile_name: AWS CLI profile name
        region: AWS region

    Returns:
        List of Subnet objects
    """
    region = region or get_default_region()
    session = create_session(profile_name, region)
    ec2 = session.client("ec2")

    try:
        response = ec2.describe_subnets()
        subnets = []

        # Build a set of public subnet IDs by checking route tables
        public_subnet_ids: set[str] = set()
        try:
            rt_response = ec2.describe_route_tables()
            for rt in rt_response.get("RouteTables", []):
                has_igw_route = any(
                    route.get("GatewayId", "").startswith("igw-")
                    for route in rt.get("Routes", [])
                )
                if has_igw_route:
                    for assoc in rt.get("Associations", []):
                        subnet_id = assoc.get("SubnetId")
                        if subnet_id:
                            public_subnet_ids.add(subnet_id)
        except ClientError:
            pass  # Continue without public/private classification

        for s in response.get("Subnets", []):
            subnet_id = s["SubnetId"]
            subnet_type = "public" if subnet_id in public_subnet_ids else "private"

            subnet = Subnet(
                id=subnet_id,
                cidr=s["CidrBlock"],
                az=s["AvailabilityZone"],
                type=subnet_type,
                nat_gateway=None,  # NAT gateways handled separately at top level
            )
            subnets.append(subnet)

        logger.debug(f"Discovered {len(subnets)} Subnets in {region}")
        return subnets
    except ClientError as e:
        logger.warning(f"Failed to discover Subnets: {e}")
        return []
