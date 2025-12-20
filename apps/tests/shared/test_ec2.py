"""Tests for EC2 resource discovery using moto."""

import pytest
from moto import mock_aws

from claude_apps.shared.aws_utils.services.ec2 import (
    discover_ec2_instances,
    discover_elastic_ips,
    discover_internet_gateways,
    discover_internet_gateways_all,
    discover_nat_gateways,
    discover_nat_gateways_all,
    discover_subnets,
    discover_subnets_all,
    discover_vpcs,
)


@pytest.fixture
def mock_vpc_setup():
    """Create a mock VPC with subnets and gateways."""
    import boto3

    with mock_aws():
        ec2 = boto3.client("ec2", region_name="us-east-1")

        # Create VPC
        vpc_response = ec2.create_vpc(CidrBlock="10.0.0.0/16")
        vpc_id = vpc_response["Vpc"]["VpcId"]

        # Create Internet Gateway
        igw_response = ec2.create_internet_gateway()
        igw_id = igw_response["InternetGateway"]["InternetGatewayId"]
        ec2.attach_internet_gateway(InternetGatewayId=igw_id, VpcId=vpc_id)

        # Create public subnet
        public_subnet = ec2.create_subnet(
            VpcId=vpc_id,
            CidrBlock="10.0.1.0/24",
            AvailabilityZone="us-east-1a",
        )
        public_subnet_id = public_subnet["Subnet"]["SubnetId"]

        # Create private subnet
        private_subnet = ec2.create_subnet(
            VpcId=vpc_id,
            CidrBlock="10.0.2.0/24",
            AvailabilityZone="us-east-1b",
        )
        private_subnet_id = private_subnet["Subnet"]["SubnetId"]

        # Create route table with IGW route for public subnet
        rt_response = ec2.create_route_table(VpcId=vpc_id)
        rt_id = rt_response["RouteTable"]["RouteTableId"]
        ec2.create_route(
            RouteTableId=rt_id,
            DestinationCidrBlock="0.0.0.0/0",
            GatewayId=igw_id,
        )
        ec2.associate_route_table(RouteTableId=rt_id, SubnetId=public_subnet_id)

        yield {
            "ec2": ec2,
            "vpc_id": vpc_id,
            "igw_id": igw_id,
            "public_subnet_id": public_subnet_id,
            "private_subnet_id": private_subnet_id,
        }


class TestDiscoverInternetGateways:
    """Tests for discover_internet_gateways function."""

    @mock_aws
    def test_discover_igw_for_vpc(self):
        """Test discovering IGWs attached to a VPC."""
        import boto3

        ec2 = boto3.client("ec2", region_name="us-east-1")

        # Create VPC and IGW
        vpc = ec2.create_vpc(CidrBlock="10.0.0.0/16")
        vpc_id = vpc["Vpc"]["VpcId"]

        igw = ec2.create_internet_gateway()
        igw_id = igw["InternetGateway"]["InternetGatewayId"]
        ec2.attach_internet_gateway(InternetGatewayId=igw_id, VpcId=vpc_id)

        # Discover
        gateways = discover_internet_gateways(ec2, vpc_id)

        assert len(gateways) == 1
        assert gateways[0].id == igw_id
        assert gateways[0].state == "attached"

    @mock_aws
    def test_discover_igw_empty_vpc(self):
        """Test discovering IGWs in VPC with none."""
        import boto3

        ec2 = boto3.client("ec2", region_name="us-east-1")

        # Create VPC without IGW
        vpc = ec2.create_vpc(CidrBlock="10.0.0.0/16")
        vpc_id = vpc["Vpc"]["VpcId"]

        gateways = discover_internet_gateways(ec2, vpc_id)
        assert len(gateways) == 0


class TestDiscoverNatGateways:
    """Tests for discover_nat_gateways function."""

    @mock_aws
    def test_discover_nat_gateways_empty(self):
        """Test discovering NAT gateways when none exist."""
        import boto3

        ec2 = boto3.client("ec2", region_name="us-east-1")

        vpc = ec2.create_vpc(CidrBlock="10.0.0.0/16")
        vpc_id = vpc["Vpc"]["VpcId"]

        nat_map = discover_nat_gateways(ec2, vpc_id)
        assert nat_map == {}


class TestDiscoverSubnets:
    """Tests for discover_subnets function."""

    @mock_aws
    def test_discover_subnets(self):
        """Test discovering subnets in a VPC."""
        import boto3

        ec2 = boto3.client("ec2", region_name="us-east-1")

        # Create VPC
        vpc = ec2.create_vpc(CidrBlock="10.0.0.0/16")
        vpc_id = vpc["Vpc"]["VpcId"]

        # Create subnets
        ec2.create_subnet(
            VpcId=vpc_id, CidrBlock="10.0.1.0/24", AvailabilityZone="us-east-1a"
        )
        ec2.create_subnet(
            VpcId=vpc_id, CidrBlock="10.0.2.0/24", AvailabilityZone="us-east-1b"
        )

        subnets = discover_subnets(ec2, vpc_id)

        assert len(subnets) == 2
        cidrs = {s.cidr for s in subnets}
        assert "10.0.1.0/24" in cidrs
        assert "10.0.2.0/24" in cidrs

    @mock_aws
    def test_discover_subnets_empty_vpc(self):
        """Test discovering subnets in VPC with none."""
        import boto3

        ec2 = boto3.client("ec2", region_name="us-east-1")

        vpc = ec2.create_vpc(CidrBlock="10.0.0.0/16")
        vpc_id = vpc["Vpc"]["VpcId"]

        subnets = discover_subnets(ec2, vpc_id)
        assert len(subnets) == 0


class TestDiscoverVPCs:
    """Tests for discover_vpcs function."""

    @mock_aws
    def test_discover_vpcs_with_subnets(self):
        """Test discovering VPCs that have subnets."""
        import boto3

        ec2 = boto3.client("ec2", region_name="us-east-1")

        # Create VPC with subnet
        vpc = ec2.create_vpc(CidrBlock="10.0.0.0/16")
        vpc_id = vpc["Vpc"]["VpcId"]
        ec2.create_subnet(
            VpcId=vpc_id, CidrBlock="10.0.1.0/24", AvailabilityZone="us-east-1a"
        )

        vpcs = discover_vpcs(region="us-east-1")

        # Should include our VPC and possibly the default VPC
        vpc_ids = {v.id for v in vpcs}
        assert vpc_id in vpc_ids

    @mock_aws
    def test_discover_vpcs_skips_empty(self):
        """Test that VPCs without subnets are skipped."""
        import boto3

        ec2 = boto3.client("ec2", region_name="us-east-1")

        # Create VPC without any subnets
        vpc = ec2.create_vpc(CidrBlock="10.0.0.0/16")
        vpc_id = vpc["Vpc"]["VpcId"]

        # Note: Default VPC might be included
        vpcs = discover_vpcs(region="us-east-1")

        # Our empty VPC should be skipped
        vpc_ids = {v.id for v in vpcs}
        assert vpc_id not in vpc_ids


class TestDiscoverElasticIPs:
    """Tests for discover_elastic_ips function."""

    @mock_aws
    def test_discover_elastic_ips(self):
        """Test discovering Elastic IPs."""
        import boto3

        ec2 = boto3.client("ec2", region_name="us-east-1")

        # Allocate an EIP
        eip = ec2.allocate_address(Domain="vpc")
        allocation_id = eip["AllocationId"]
        public_ip = eip["PublicIp"]

        eips = discover_elastic_ips(region="us-east-1")

        assert len(eips) == 1
        assert eips[0].allocation_id == allocation_id
        assert eips[0].public_ip == public_ip
        assert eips[0].domain == "vpc"
        assert eips[0].region == "us-east-1"

    @mock_aws
    def test_discover_elastic_ips_empty(self):
        """Test discovering when no Elastic IPs exist."""
        eips = discover_elastic_ips(region="us-east-1")
        assert eips == []


class TestDiscoverEC2Instances:
    """Tests for discover_ec2_instances function."""

    @mock_aws
    def test_discover_ec2_instances(self):
        """Test discovering EC2 instances."""
        import boto3

        ec2 = boto3.client("ec2", region_name="us-east-1")

        # Create VPC and subnet for instance
        vpc = ec2.create_vpc(CidrBlock="10.0.0.0/16")
        vpc_id = vpc["Vpc"]["VpcId"]
        subnet = ec2.create_subnet(
            VpcId=vpc_id, CidrBlock="10.0.1.0/24", AvailabilityZone="us-east-1a"
        )
        subnet_id = subnet["Subnet"]["SubnetId"]

        # Create security group
        sg = ec2.create_security_group(
            GroupName="test-sg",
            Description="Test security group",
            VpcId=vpc_id,
        )
        sg_id = sg["GroupId"]

        # Launch instance
        instances = ec2.run_instances(
            ImageId="ami-12345678",
            MinCount=1,
            MaxCount=1,
            InstanceType="t3.micro",
            SubnetId=subnet_id,
            SecurityGroupIds=[sg_id],
            TagSpecifications=[
                {
                    "ResourceType": "instance",
                    "Tags": [
                        {"Key": "Name", "Value": "test-instance"},
                        {"Key": "Environment", "Value": "test"},
                    ],
                }
            ],
        )
        instance_id = instances["Instances"][0]["InstanceId"]

        discovered = discover_ec2_instances(region="us-east-1")

        assert len(discovered) == 1
        inst = discovered[0]
        assert inst.instance_id == instance_id
        assert inst.instance_type == "t3.micro"
        assert inst.vpc_id == vpc_id
        assert inst.subnet_id == subnet_id
        assert inst.name == "test-instance"
        assert sg_id in inst.security_groups
        assert inst.tags["Environment"] == "test"
        assert inst.region == "us-east-1"
        assert "arn:aws:ec2" in inst.arn

    @mock_aws
    def test_discover_ec2_instances_empty(self):
        """Test discovering when no instances exist."""
        instances = discover_ec2_instances(region="us-east-1")
        assert instances == []


class TestDiscoverAllResources:
    """Tests for account-wide discovery functions."""

    @mock_aws
    def test_discover_internet_gateways_all(self):
        """Test discovering all IGWs in account."""
        import boto3

        ec2 = boto3.client("ec2", region_name="us-east-1")

        # Create IGWs
        igw1 = ec2.create_internet_gateway()
        igw2 = ec2.create_internet_gateway()

        gateways = discover_internet_gateways_all(region="us-east-1")

        assert len(gateways) == 2
        igw_ids = {g.id for g in gateways}
        assert igw1["InternetGateway"]["InternetGatewayId"] in igw_ids
        assert igw2["InternetGateway"]["InternetGatewayId"] in igw_ids

    @mock_aws
    def test_discover_nat_gateways_all_empty(self):
        """Test discovering all NAT gateways when none exist."""
        gateways = discover_nat_gateways_all(region="us-east-1")
        assert gateways == []

    @mock_aws
    def test_discover_subnets_all(self):
        """Test discovering all subnets in account."""
        import boto3

        ec2 = boto3.client("ec2", region_name="us-east-1")

        # Create VPC and subnets
        vpc = ec2.create_vpc(CidrBlock="10.0.0.0/16")
        vpc_id = vpc["Vpc"]["VpcId"]

        ec2.create_subnet(
            VpcId=vpc_id, CidrBlock="10.0.1.0/24", AvailabilityZone="us-east-1a"
        )
        ec2.create_subnet(
            VpcId=vpc_id, CidrBlock="10.0.2.0/24", AvailabilityZone="us-east-1b"
        )

        subnets = discover_subnets_all(region="us-east-1")

        # Should have at least our 2 subnets
        assert len(subnets) >= 2
        cidrs = {s.cidr for s in subnets}
        assert "10.0.1.0/24" in cidrs
        assert "10.0.2.0/24" in cidrs
