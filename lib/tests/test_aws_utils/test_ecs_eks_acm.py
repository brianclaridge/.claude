"""Tests for ECS, EKS, and ACM service discovery modules."""

from datetime import datetime
from unittest.mock import MagicMock, patch

from aws_utils.core.schemas import (
    ACMCertificate,
    ECSCluster,
    ECSService,
    ECSTaskDefinition,
    EKSCluster,
    EKSFargateProfile,
    EKSNodeGroup,
)


class TestECSSchemas:
    """Test ECS Pydantic schema models."""

    def test_ecs_cluster_schema(self):
        """Test ECSCluster schema instantiation."""
        cluster = ECSCluster(
            cluster_name="test-cluster",
            cluster_arn="arn:aws:ecs:us-east-1:123456789:cluster/test-cluster",
            status="ACTIVE",
            registered_container_instances=2,
            running_tasks=5,
            pending_tasks=1,
            active_services=3,
            region="us-east-1",
        )
        assert cluster.cluster_name == "test-cluster"
        assert cluster.status == "ACTIVE"
        assert cluster.running_tasks == 5

    def test_ecs_cluster_defaults(self):
        """Test ECSCluster default values."""
        cluster = ECSCluster(
            cluster_name="minimal-cluster",
            cluster_arn="arn:aws:ecs:us-east-1:123456789:cluster/minimal-cluster",
            status="ACTIVE",
            region="us-east-1",
        )
        assert cluster.registered_container_instances == 0
        assert cluster.running_tasks == 0
        assert cluster.pending_tasks == 0
        assert cluster.active_services == 0

    def test_ecs_service_schema(self):
        """Test ECSService schema instantiation."""
        service = ECSService(
            service_name="web-service",
            service_arn="arn:aws:ecs:us-east-1:123456789:service/test-cluster/web-service",
            cluster_arn="arn:aws:ecs:us-east-1:123456789:cluster/test-cluster",
            status="ACTIVE",
            desired_count=3,
            running_count=3,
            launch_type="FARGATE",
            task_definition="arn:aws:ecs:us-east-1:123456789:task-definition/web:1",
            region="us-east-1",
        )
        assert service.service_name == "web-service"
        assert service.launch_type == "FARGATE"
        assert service.desired_count == 3

    def test_ecs_task_definition_schema(self):
        """Test ECSTaskDefinition schema instantiation."""
        task_def = ECSTaskDefinition(
            family="web-task",
            task_definition_arn="arn:aws:ecs:us-east-1:123456789:task-definition/web:5",
            revision=5,
            status="ACTIVE",
            cpu="256",
            memory="512",
            requires_compatibilities=["FARGATE"],
            region="us-east-1",
        )
        assert task_def.family == "web-task"
        assert task_def.revision == 5
        assert task_def.cpu == "256"

    def test_ecs_task_definition_optional_fields(self):
        """Test ECSTaskDefinition with optional fields."""
        task_def = ECSTaskDefinition(
            family="ec2-task",
            task_definition_arn="arn:aws:ecs:us-east-1:123456789:task-definition/ec2:1",
            revision=1,
            status="ACTIVE",
            region="us-east-1",
        )
        assert task_def.cpu is None
        assert task_def.memory is None
        assert task_def.requires_compatibilities == []


class TestEKSSchemas:
    """Test EKS Pydantic schema models."""

    def test_eks_cluster_schema(self):
        """Test EKSCluster schema instantiation."""
        cluster = EKSCluster(
            cluster_name="prod-cluster",
            cluster_arn="arn:aws:eks:us-east-1:123456789:cluster/prod-cluster",
            status="ACTIVE",
            version="1.28",
            endpoint="https://ABCD1234.gr7.us-east-1.eks.amazonaws.com",
            platform_version="eks.5",
            created_at=datetime(2024, 1, 1, 12, 0, 0),
            region="us-east-1",
        )
        assert cluster.cluster_name == "prod-cluster"
        assert cluster.version == "1.28"
        assert cluster.status == "ACTIVE"

    def test_eks_cluster_optional_fields(self):
        """Test EKSCluster with optional fields."""
        cluster = EKSCluster(
            cluster_name="new-cluster",
            cluster_arn="arn:aws:eks:us-east-1:123456789:cluster/new-cluster",
            status="CREATING",
            version="1.29",
            region="us-east-1",
        )
        assert cluster.endpoint is None
        assert cluster.platform_version is None
        assert cluster.created_at is None

    def test_eks_node_group_schema(self):
        """Test EKSNodeGroup schema instantiation."""
        node_group = EKSNodeGroup(
            nodegroup_name="workers",
            nodegroup_arn="arn:aws:eks:us-east-1:123456789:nodegroup/prod/workers/abc",
            cluster_name="prod-cluster",
            status="ACTIVE",
            instance_types=["t3.medium", "t3.large"],
            desired_size=3,
            min_size=1,
            max_size=5,
            region="us-east-1",
        )
        assert node_group.nodegroup_name == "workers"
        assert node_group.instance_types == ["t3.medium", "t3.large"]
        assert node_group.desired_size == 3

    def test_eks_fargate_profile_schema(self):
        """Test EKSFargateProfile schema instantiation."""
        profile = EKSFargateProfile(
            fargate_profile_name="default-fargate",
            fargate_profile_arn="arn:aws:eks:us-east-1:123456789:fargateprofile/prod/default-fargate/abc",
            cluster_name="prod-cluster",
            status="ACTIVE",
            pod_execution_role_arn="arn:aws:iam::123456789:role/eks-fargate-role",
            selectors=[
                {"namespace": "default"},
                {"namespace": "kube-system", "labels": {"app": "monitoring"}},
            ],
            region="us-east-1",
        )
        assert profile.fargate_profile_name == "default-fargate"
        assert len(profile.selectors) == 2
        assert profile.pod_execution_role_arn.endswith("eks-fargate-role")


class TestACMSchemas:
    """Test ACM Pydantic schema models."""

    def test_acm_certificate_schema(self):
        """Test ACMCertificate schema instantiation."""
        cert = ACMCertificate(
            certificate_arn="arn:aws:acm:us-east-1:123456789:certificate/abc-123",
            domain_name="example.com",
            status="ISSUED",
            certificate_type="AMAZON_ISSUED",
            issuer="Amazon",
            not_before=datetime(2024, 1, 1),
            not_after=datetime(2025, 1, 1),
            in_use_by=["arn:aws:elasticloadbalancing:us-east-1:123456789:loadbalancer/app/my-alb/abc"],
            subject_alternative_names=["example.com", "*.example.com"],
            region="us-east-1",
        )
        assert cert.domain_name == "example.com"
        assert cert.status == "ISSUED"
        assert len(cert.subject_alternative_names) == 2

    def test_acm_certificate_optional_fields(self):
        """Test ACMCertificate with optional fields."""
        cert = ACMCertificate(
            certificate_arn="arn:aws:acm:us-east-1:123456789:certificate/pending-123",
            domain_name="new-domain.com",
            status="PENDING_VALIDATION",
            certificate_type="AMAZON_ISSUED",
            region="us-east-1",
        )
        assert cert.issuer is None
        assert cert.not_before is None
        assert cert.not_after is None
        assert cert.in_use_by == []

    def test_acm_imported_certificate(self):
        """Test ACMCertificate for imported certificate."""
        cert = ACMCertificate(
            certificate_arn="arn:aws:acm:us-east-1:123456789:certificate/imported-123",
            domain_name="internal.corp.com",
            status="ISSUED",
            certificate_type="IMPORTED",
            issuer="Internal CA",
            not_before=datetime(2024, 6, 1),
            not_after=datetime(2025, 6, 1),
            in_use_by=[],
            subject_alternative_names=["internal.corp.com"],
            region="us-east-1",
        )
        assert cert.certificate_type == "IMPORTED"
        assert cert.issuer == "Internal CA"


class TestECSDiscovery:
    """Test ECS service discovery functions."""

    @patch("aws_utils.services.ecs.create_session")
    def test_discover_ecs_clusters(self, mock_create_session):
        """Test discovering ECS clusters."""
        from aws_utils.services.ecs import discover_ecs_clusters

        # Mock boto3 client
        mock_client = MagicMock()
        mock_session = MagicMock()
        mock_session.client.return_value = mock_client
        mock_session.region_name = "us-east-1"
        mock_create_session.return_value = mock_session

        # Mock paginator
        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [
            {"clusterArns": ["arn:aws:ecs:us-east-1:123:cluster/test-cluster"]}
        ]
        mock_client.get_paginator.return_value = mock_paginator

        # Mock describe_clusters
        mock_client.describe_clusters.return_value = {
            "clusters": [
                {
                    "clusterName": "test-cluster",
                    "clusterArn": "arn:aws:ecs:us-east-1:123:cluster/test-cluster",
                    "status": "ACTIVE",
                    "registeredContainerInstancesCount": 2,
                    "runningTasksCount": 5,
                    "pendingTasksCount": 0,
                    "activeServicesCount": 3,
                }
            ]
        }

        clusters = discover_ecs_clusters()
        assert len(clusters) == 1
        assert clusters[0].cluster_name == "test-cluster"
        assert clusters[0].running_tasks == 5

    @patch("aws_utils.services.ecs.create_session")
    def test_discover_ecs_clusters_empty(self, mock_create_session):
        """Test discovering ECS clusters when none exist."""
        from aws_utils.services.ecs import discover_ecs_clusters

        mock_client = MagicMock()
        mock_session = MagicMock()
        mock_session.client.return_value = mock_client
        mock_session.region_name = "us-east-1"
        mock_create_session.return_value = mock_session

        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [{"clusterArns": []}]
        mock_client.get_paginator.return_value = mock_paginator

        clusters = discover_ecs_clusters()
        assert len(clusters) == 0

    @patch("aws_utils.services.ecs.create_session")
    def test_discover_ecs_services(self, mock_create_session):
        """Test discovering ECS services for a cluster."""
        from aws_utils.services.ecs import discover_ecs_services

        mock_client = MagicMock()
        mock_session = MagicMock()
        mock_session.client.return_value = mock_client
        mock_session.region_name = "us-east-1"
        mock_create_session.return_value = mock_session

        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [
            {"serviceArns": ["arn:aws:ecs:us-east-1:123:service/cluster/web-svc"]}
        ]
        mock_client.get_paginator.return_value = mock_paginator

        mock_client.describe_services.return_value = {
            "services": [
                {
                    "serviceName": "web-svc",
                    "serviceArn": "arn:aws:ecs:us-east-1:123:service/cluster/web-svc",
                    "clusterArn": "arn:aws:ecs:us-east-1:123:cluster/test",
                    "status": "ACTIVE",
                    "desiredCount": 2,
                    "runningCount": 2,
                    "launchType": "FARGATE",
                    "taskDefinition": "arn:aws:ecs:us-east-1:123:task-definition/web:1",
                }
            ]
        }

        services = discover_ecs_services(cluster_arn="arn:aws:ecs:us-east-1:123:cluster/test")
        assert len(services) == 1
        assert services[0].service_name == "web-svc"
        assert services[0].launch_type == "FARGATE"

    def test_discover_ecs_services_no_cluster(self):
        """Test discover_ecs_services without cluster_arn."""
        from aws_utils.services.ecs import discover_ecs_services

        services = discover_ecs_services()
        assert services == []


class TestEKSDiscovery:
    """Test EKS service discovery functions."""

    @patch("aws_utils.services.eks.create_session")
    def test_discover_eks_clusters(self, mock_create_session):
        """Test discovering EKS clusters."""
        from aws_utils.services.eks import discover_eks_clusters

        mock_client = MagicMock()
        mock_session = MagicMock()
        mock_session.client.return_value = mock_client
        mock_session.region_name = "us-east-1"
        mock_create_session.return_value = mock_session

        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [{"clusters": ["prod-cluster"]}]
        mock_client.get_paginator.return_value = mock_paginator

        mock_client.describe_cluster.return_value = {
            "cluster": {
                "name": "prod-cluster",
                "arn": "arn:aws:eks:us-east-1:123:cluster/prod-cluster",
                "status": "ACTIVE",
                "version": "1.28",
                "endpoint": "https://ABC.eks.amazonaws.com",
                "platformVersion": "eks.5",
            }
        }

        clusters = discover_eks_clusters()
        assert len(clusters) == 1
        assert clusters[0].cluster_name == "prod-cluster"
        assert clusters[0].version == "1.28"

    @patch("aws_utils.services.eks.create_session")
    def test_discover_eks_node_groups(self, mock_create_session):
        """Test discovering EKS node groups."""
        from aws_utils.services.eks import discover_eks_node_groups

        mock_client = MagicMock()
        mock_session = MagicMock()
        mock_session.client.return_value = mock_client
        mock_session.region_name = "us-east-1"
        mock_create_session.return_value = mock_session

        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [{"nodegroups": ["workers"]}]
        mock_client.get_paginator.return_value = mock_paginator

        mock_client.describe_nodegroup.return_value = {
            "nodegroup": {
                "nodegroupName": "workers",
                "nodegroupArn": "arn:aws:eks:us-east-1:123:nodegroup/prod/workers/abc",
                "status": "ACTIVE",
                "instanceTypes": ["t3.medium"],
                "scalingConfig": {"desiredSize": 3, "minSize": 1, "maxSize": 5},
            }
        }

        node_groups = discover_eks_node_groups(cluster_name="prod-cluster")
        assert len(node_groups) == 1
        assert node_groups[0].nodegroup_name == "workers"
        assert node_groups[0].desired_size == 3

    def test_discover_eks_node_groups_no_cluster(self):
        """Test discover_eks_node_groups without cluster_name."""
        from aws_utils.services.eks import discover_eks_node_groups

        node_groups = discover_eks_node_groups()
        assert node_groups == []


class TestACMDiscovery:
    """Test ACM service discovery functions."""

    @patch("aws_utils.services.acm.create_session")
    def test_discover_acm_certificates(self, mock_create_session):
        """Test discovering ACM certificates."""
        from aws_utils.services.acm import discover_acm_certificates

        mock_client = MagicMock()
        mock_session = MagicMock()
        mock_session.client.return_value = mock_client
        mock_session.region_name = "us-east-1"
        mock_create_session.return_value = mock_session

        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [
            {
                "CertificateSummaryList": [
                    {"CertificateArn": "arn:aws:acm:us-east-1:123:certificate/abc-123"}
                ]
            }
        ]
        mock_client.get_paginator.return_value = mock_paginator

        mock_client.describe_certificate.return_value = {
            "Certificate": {
                "CertificateArn": "arn:aws:acm:us-east-1:123:certificate/abc-123",
                "DomainName": "example.com",
                "Status": "ISSUED",
                "Type": "AMAZON_ISSUED",
                "Issuer": "Amazon",
                "InUseBy": [],
                "SubjectAlternativeNames": ["example.com", "*.example.com"],
            }
        }

        certs = discover_acm_certificates()
        assert len(certs) == 1
        assert certs[0].domain_name == "example.com"
        assert certs[0].status == "ISSUED"

    @patch("aws_utils.services.acm.create_session")
    def test_discover_acm_certificates_empty(self, mock_create_session):
        """Test discovering ACM certificates when none exist."""
        from aws_utils.services.acm import discover_acm_certificates

        mock_client = MagicMock()
        mock_session = MagicMock()
        mock_session.client.return_value = mock_client
        mock_session.region_name = "us-east-1"
        mock_create_session.return_value = mock_session

        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [{"CertificateSummaryList": []}]
        mock_client.get_paginator.return_value = mock_paginator

        certs = discover_acm_certificates()
        assert len(certs) == 0
