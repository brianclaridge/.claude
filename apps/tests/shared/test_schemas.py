"""Tests for AWS inventory Pydantic schemas."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from claude_apps.shared.aws_utils.core.schemas import (
    ACMCertificate,
    AccountConfig,
    AccountInventory,
    AccountsConfig,
    ApplicationLoadBalancer,
    AutoScalingGroup,
    CloudFrontDistribution,
    CloudWatchAlarm,
    CloudWatchLogGroup,
    DynamoDBTable,
    EC2Instance,
    ECSCluster,
    ECSService,
    ECSTaskDefinition,
    EKSCluster,
    EKSFargateProfile,
    EKSNodeGroup,
    ECRRepository,
    ElasticIP,
    IAMGroup,
    IAMPolicy,
    IAMRole,
    IAMUser,
    InternetGateway,
    LambdaFunction,
    NATGateway,
    RDSCluster,
    RDSInstance,
    RelationshipGraph,
    Route53Domain,
    Route53Record,
    Route53Zone,
    S3Bucket,
    SecretsManagerSecret,
    SESIdentity,
    SNSTopic,
    SQSQueue,
    SSOAccount,
    SSOInstance,
    StateMachine,
    Subnet,
    VPC,
)


class TestNATGateway:
    """Tests for NATGateway model."""

    def test_minimal_nat_gateway(self):
        """Test NAT Gateway with required fields only."""
        nat = NATGateway(id="nat-12345", state="available")
        assert nat.id == "nat-12345"
        assert nat.state == "available"
        assert nat.elastic_ip is None
        assert nat.public_ip is None

    def test_full_nat_gateway(self):
        """Test NAT Gateway with all fields."""
        nat = NATGateway(
            id="nat-12345",
            state="available",
            elastic_ip="eipalloc-12345",
            public_ip="1.2.3.4",
        )
        assert nat.elastic_ip == "eipalloc-12345"
        assert nat.public_ip == "1.2.3.4"


class TestSubnet:
    """Tests for Subnet model."""

    def test_minimal_subnet(self):
        """Test Subnet with required fields only."""
        subnet = Subnet(
            id="subnet-12345",
            cidr="10.0.1.0/24",
            az="us-east-1a",
            type="private",
        )
        assert subnet.id == "subnet-12345"
        assert subnet.cidr == "10.0.1.0/24"
        assert subnet.az == "us-east-1a"
        assert subnet.type == "private"
        assert subnet.nat_gateway is None

    def test_subnet_with_nat_gateway(self):
        """Test Subnet with NAT Gateway attached."""
        nat = NATGateway(id="nat-12345", state="available")
        subnet = Subnet(
            id="subnet-12345",
            cidr="10.0.1.0/24",
            az="us-east-1a",
            type="public",
            nat_gateway=nat,
        )
        assert subnet.nat_gateway is not None
        assert subnet.nat_gateway.id == "nat-12345"


class TestVPC:
    """Tests for VPC model."""

    def test_minimal_vpc(self):
        """Test VPC with required fields only."""
        vpc = VPC(id="vpc-12345", cidr="10.0.0.0/16")
        assert vpc.id == "vpc-12345"
        assert vpc.cidr == "10.0.0.0/16"
        assert vpc.is_default is False
        assert vpc.internet_gateways == []
        assert vpc.subnets == []

    def test_vpc_with_resources(self):
        """Test VPC with subnets and internet gateways."""
        igw = InternetGateway(id="igw-12345", state="attached")
        subnet = Subnet(
            id="subnet-12345",
            cidr="10.0.1.0/24",
            az="us-east-1a",
            type="public",
        )
        vpc = VPC(
            id="vpc-12345",
            cidr="10.0.0.0/16",
            is_default=True,
            internet_gateways=[igw],
            subnets=[subnet],
        )
        assert vpc.is_default is True
        assert len(vpc.internet_gateways) == 1
        assert len(vpc.subnets) == 1


class TestS3Bucket:
    """Tests for S3Bucket model."""

    def test_minimal_s3_bucket(self):
        """Test S3 bucket with required fields."""
        bucket = S3Bucket(
            name="my-bucket",
            region="us-east-1",
            arn="arn:aws:s3:::my-bucket",
        )
        assert bucket.name == "my-bucket"
        assert bucket.region == "us-east-1"
        assert bucket.created is None

    def test_s3_bucket_with_date(self):
        """Test S3 bucket with creation date."""
        created = datetime(2024, 1, 15, 12, 0, 0)
        bucket = S3Bucket(
            name="my-bucket",
            region="us-east-1",
            arn="arn:aws:s3:::my-bucket",
            created=created,
        )
        assert bucket.created == created


class TestLambdaFunction:
    """Tests for LambdaFunction model."""

    def test_minimal_lambda(self):
        """Test Lambda with required fields."""
        func = LambdaFunction(
            function_name="my-function",
            memory_size=128,
            timeout=30,
            last_modified="2024-01-15T12:00:00.000+0000",
            arn="arn:aws:lambda:us-east-1:123456789012:function:my-function",
            region="us-east-1",
        )
        assert func.function_name == "my-function"
        assert func.runtime is None
        assert func.vpc_id is None
        assert func.subnet_ids == []
        assert func.security_group_ids == []

    def test_vpc_connected_lambda(self):
        """Test Lambda with VPC configuration."""
        func = LambdaFunction(
            function_name="my-function",
            runtime="python3.12",
            memory_size=256,
            timeout=60,
            last_modified="2024-01-15T12:00:00.000+0000",
            arn="arn:aws:lambda:us-east-1:123456789012:function:my-function",
            region="us-east-1",
            vpc_id="vpc-12345",
            subnet_ids=["subnet-1", "subnet-2"],
            security_group_ids=["sg-1"],
            execution_role_arn="arn:aws:iam::123456789012:role/my-role",
        )
        assert func.vpc_id == "vpc-12345"
        assert len(func.subnet_ids) == 2
        assert func.execution_role_arn is not None


class TestEC2Instance:
    """Tests for EC2Instance model."""

    def test_minimal_ec2(self):
        """Test EC2 instance with required fields."""
        instance = EC2Instance(
            instance_id="i-12345",
            instance_type="t3.micro",
            state="running",
            arn="arn:aws:ec2:us-east-1:123456789012:instance/i-12345",
            region="us-east-1",
        )
        assert instance.instance_id == "i-12345"
        assert instance.state == "running"
        assert instance.vpc_id is None
        assert instance.security_groups == []

    def test_full_ec2(self):
        """Test EC2 instance with all fields."""
        instance = EC2Instance(
            instance_id="i-12345",
            instance_type="t3.large",
            state="running",
            private_ip="10.0.1.5",
            public_ip="1.2.3.4",
            vpc_id="vpc-12345",
            subnet_id="subnet-12345",
            launch_time="2024-01-15T12:00:00.000Z",
            name="web-server",
            image_id="ami-12345",
            key_name="my-key",
            security_groups=["sg-1", "sg-2"],
            iam_instance_profile="arn:aws:iam::123456789012:instance-profile/my-profile",
            tags={"Environment": "production"},
            arn="arn:aws:ec2:us-east-1:123456789012:instance/i-12345",
            region="us-east-1",
        )
        assert instance.name == "web-server"
        assert len(instance.security_groups) == 2
        assert instance.tags["Environment"] == "production"


class TestRelationshipGraph:
    """Tests for RelationshipGraph model."""

    def test_add_relationship(self):
        """Test adding a relationship."""
        graph = RelationshipGraph()
        graph.add_relationship(
            source_type="lambda",
            source_id="my-func",
            relationship_type="deployed_in",
            target_type="vpc",
            target_id="vpc-12345",
        )

        edges = graph.get_relationships("lambda", "my-func")
        assert len(edges) == 1
        assert edges[0].relationship_type == "deployed_in"
        assert edges[0].target.resource_type == "vpc"
        assert edges[0].target.resource_id == "vpc-12345"

    def test_reverse_edges(self):
        """Test reverse edge lookup."""
        graph = RelationshipGraph()
        graph.add_relationship(
            source_type="lambda",
            source_id="func-1",
            relationship_type="deployed_in",
            target_type="vpc",
            target_id="vpc-12345",
        )
        graph.add_relationship(
            source_type="rds_instance",
            source_id="db-1",
            relationship_type="deployed_in",
            target_type="vpc",
            target_id="vpc-12345",
        )

        sources = graph.get_resources_targeting("vpc", "vpc-12345")
        assert len(sources) == 2
        assert "lambda:func-1" in sources
        assert "rds_instance:db-1" in sources

    def test_get_resources_in_vpc(self):
        """Test getting resources in a VPC."""
        graph = RelationshipGraph()
        graph.add_relationship(
            "ec2", "i-12345", "deployed_in", "vpc", "vpc-12345"
        )

        resources = graph.get_resources_in_vpc("vpc-12345")
        assert "ec2:i-12345" in resources


class TestAccountInventory:
    """Tests for AccountInventory model."""

    def test_minimal_inventory(self):
        """Test inventory with required fields."""
        inventory = AccountInventory(
            account_id="123456789012",
            account_alias="my-account",
            region="us-east-1",
        )
        assert inventory.account_id == "123456789012"
        assert inventory.schema_version == "1.0"
        assert inventory.vpcs == []
        assert inventory.lambda_functions == []

    def test_inventory_with_resources(self):
        """Test inventory with various resources."""
        vpc = VPC(id="vpc-12345", cidr="10.0.0.0/16")
        func = LambdaFunction(
            function_name="my-func",
            memory_size=128,
            timeout=30,
            last_modified="2024-01-15T12:00:00.000+0000",
            arn="arn:aws:lambda:us-east-1:123456789012:function:my-func",
            region="us-east-1",
            vpc_id="vpc-12345",
        )

        inventory = AccountInventory(
            account_id="123456789012",
            account_alias="my-account",
            region="us-east-1",
            vpcs=[vpc],
            lambda_functions=[func],
        )

        assert len(inventory.vpcs) == 1
        assert len(inventory.lambda_functions) == 1

    def test_build_relationships(self):
        """Test building relationship graph from inventory."""
        func = LambdaFunction(
            function_name="my-func",
            memory_size=128,
            timeout=30,
            last_modified="2024-01-15T12:00:00.000+0000",
            arn="arn:aws:lambda:us-east-1:123456789012:function:my-func",
            region="us-east-1",
            vpc_id="vpc-12345",
            subnet_ids=["subnet-1"],
            security_group_ids=["sg-1"],
            execution_role_arn="arn:aws:iam::123456789012:role/my-role",
        )

        inventory = AccountInventory(
            account_id="123456789012",
            account_alias="my-account",
            region="us-east-1",
            lambda_functions=[func],
        )

        inventory.build_relationships()

        edges = inventory.relationships.get_relationships("lambda", "my-func")
        assert len(edges) >= 3  # vpc, subnet, security group, role

        relationship_types = {e.relationship_type for e in edges}
        assert "deployed_in" in relationship_types
        assert "uses_subnet" in relationship_types
        assert "uses_security_group" in relationship_types

    def test_to_dict(self):
        """Test serialization to dictionary."""
        inventory = AccountInventory(
            account_id="123456789012",
            account_alias="my-account",
            region="us-east-1",
        )

        data = inventory.to_dict()
        assert data["account_id"] == "123456789012"
        assert isinstance(data["discovered_at"], str)


class TestAccountConfig:
    """Tests for AccountConfig model."""

    def test_minimal_config(self):
        """Test account config with required fields."""
        config = AccountConfig(
            id="123456789012",
            name="my-account",
            ou_path="dev-accounts",
        )
        assert config.id == "123456789012"
        assert config.sso_role == "AdministratorAccess"
        assert config.inventory_path is None

    def test_full_config(self):
        """Test account config with all fields."""
        config = AccountConfig(
            id="123456789012",
            name="my-account",
            ou_path="prod-accounts",
            sso_role="ReadOnlyAccess",
            inventory_path="inventory/prod.yml",
        )
        assert config.sso_role == "ReadOnlyAccess"
        assert config.inventory_path == "inventory/prod.yml"


class TestAccountsConfig:
    """Tests for AccountsConfig model."""

    def test_minimal_accounts_config(self):
        """Test accounts config with required fields."""
        config = AccountsConfig(
            organization_id="o-12345",
            sso_start_url="https://my-org.awsapps.com/start",
        )
        assert config.schema_version == "4.0"
        assert config.default_region == "us-east-1"
        assert config.accounts == {}

    def test_accounts_config_with_accounts(self):
        """Test accounts config with account entries."""
        account = AccountConfig(
            id="123456789012",
            name="sandbox",
            ou_path="dev-accounts",
        )
        config = AccountsConfig(
            organization_id="o-12345",
            sso_start_url="https://my-org.awsapps.com/start",
            default_region="us-west-2",
            accounts={"sandbox": account},
        )
        assert config.default_region == "us-west-2"
        assert "sandbox" in config.accounts
        assert config.accounts["sandbox"].id == "123456789012"


class TestECSResources:
    """Tests for ECS-related models."""

    def test_ecs_cluster(self):
        """Test ECS cluster model."""
        cluster = ECSCluster(
            cluster_name="my-cluster",
            cluster_arn="arn:aws:ecs:us-east-1:123456789012:cluster/my-cluster",
            status="ACTIVE",
            region="us-east-1",
        )
        assert cluster.running_tasks == 0
        assert cluster.active_services == 0

    def test_ecs_service(self):
        """Test ECS service model."""
        service = ECSService(
            service_name="my-service",
            service_arn="arn:aws:ecs:us-east-1:123456789012:service/my-cluster/my-service",
            cluster_arn="arn:aws:ecs:us-east-1:123456789012:cluster/my-cluster",
            status="ACTIVE",
            launch_type="FARGATE",
            task_definition="arn:aws:ecs:us-east-1:123456789012:task-definition/my-task:1",
            region="us-east-1",
            vpc_id="vpc-12345",
            subnet_ids=["subnet-1", "subnet-2"],
            security_group_ids=["sg-1"],
        )
        assert service.launch_type == "FARGATE"
        assert len(service.subnet_ids) == 2


class TestEKSResources:
    """Tests for EKS-related models."""

    def test_eks_cluster(self):
        """Test EKS cluster model."""
        cluster = EKSCluster(
            cluster_name="my-cluster",
            cluster_arn="arn:aws:eks:us-east-1:123456789012:cluster/my-cluster",
            status="ACTIVE",
            version="1.28",
            endpoint="https://xxx.eks.us-east-1.amazonaws.com",
            region="us-east-1",
            vpc_id="vpc-12345",
            subnet_ids=["subnet-1", "subnet-2"],
        )
        assert cluster.version == "1.28"
        assert cluster.vpc_id == "vpc-12345"

    def test_eks_node_group(self):
        """Test EKS node group model."""
        ng = EKSNodeGroup(
            nodegroup_name="my-ng",
            nodegroup_arn="arn:aws:eks:us-east-1:123456789012:nodegroup/my-cluster/my-ng/xxx",
            cluster_name="my-cluster",
            status="ACTIVE",
            instance_types=["t3.medium"],
            desired_size=2,
            min_size=1,
            max_size=4,
            region="us-east-1",
        )
        assert ng.desired_size == 2
        assert "t3.medium" in ng.instance_types


class TestACMCertificate:
    """Tests for ACM certificate model."""

    def test_acm_certificate(self):
        """Test ACM certificate model."""
        cert = ACMCertificate(
            certificate_arn="arn:aws:acm:us-east-1:123456789012:certificate/xxx",
            domain_name="example.com",
            status="ISSUED",
            certificate_type="AMAZON_ISSUED",
            region="us-east-1",
            subject_alternative_names=["*.example.com", "www.example.com"],
        )
        assert cert.status == "ISSUED"
        assert len(cert.subject_alternative_names) == 2


class TestIAMResources:
    """Tests for IAM-related models."""

    def test_iam_role(self):
        """Test IAM role model."""
        role = IAMRole(
            role_name="my-role",
            role_id="AROA12345",
            arn="arn:aws:iam::123456789012:role/my-role",
        )
        assert role.path == "/"
        assert role.max_session_duration == 3600

    def test_iam_user(self):
        """Test IAM user model."""
        user = IAMUser(
            user_name="admin",
            user_id="AIDA12345",
            arn="arn:aws:iam::123456789012:user/admin",
        )
        assert user.path == "/"


class TestCloudWatchResources:
    """Tests for CloudWatch-related models."""

    def test_log_group(self):
        """Test CloudWatch log group model."""
        lg = CloudWatchLogGroup(
            log_group_name="/aws/lambda/my-func",
            arn="arn:aws:logs:us-east-1:123456789012:log-group:/aws/lambda/my-func",
            region="us-east-1",
        )
        assert lg.retention_days is None
        assert lg.stored_bytes == 0

    def test_alarm(self):
        """Test CloudWatch alarm model."""
        alarm = CloudWatchAlarm(
            alarm_name="HighCPU",
            alarm_arn="arn:aws:cloudwatch:us-east-1:123456789012:alarm:HighCPU",
            state_value="OK",
            metric_name="CPUUtilization",
            namespace="AWS/EC2",
            region="us-east-1",
        )
        assert alarm.state_value == "OK"
        assert alarm.actions_enabled is True
