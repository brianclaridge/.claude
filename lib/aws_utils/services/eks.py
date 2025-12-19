"""EKS service discovery."""

from botocore.exceptions import ClientError
from loguru import logger

from aws_utils.core.schemas import EKSCluster, EKSFargateProfile, EKSNodeGroup
from aws_utils.core.session import create_session


def discover_eks_clusters(
    profile_name: str | None = None,
    region: str | None = None,
) -> list[EKSCluster]:
    """Discover all EKS clusters in a region.

    Args:
        profile_name: AWS CLI profile name
        region: AWS region

    Returns:
        List of EKSCluster objects
    """
    session = create_session(profile_name, region)
    eks_client = session.client("eks")
    region_name = session.region_name or "us-east-1"

    try:
        clusters = []
        paginator = eks_client.get_paginator("list_clusters")

        cluster_names = []
        for page in paginator.paginate():
            cluster_names.extend(page.get("clusters", []))

        # Describe each cluster
        for name in cluster_names:
            response = eks_client.describe_cluster(name=name)
            cluster_data = response.get("cluster", {})

            # Extract VPC configuration
            vpc_config = cluster_data.get("resourcesVpcConfig", {})
            vpc_id = vpc_config.get("vpcId")
            subnet_ids = vpc_config.get("subnetIds", [])
            security_group_ids = vpc_config.get("securityGroupIds", [])
            cluster_security_group_id = vpc_config.get("clusterSecurityGroupId")

            # Extract enabled log types
            logging_config = cluster_data.get("logging", {})
            cluster_logging = logging_config.get("clusterLogging", [])
            enabled_log_types = []
            for log_entry in cluster_logging:
                if log_entry.get("enabled"):
                    enabled_log_types.extend(log_entry.get("types", []))

            cluster = EKSCluster(
                cluster_name=cluster_data.get("name", name),
                cluster_arn=cluster_data.get("arn", ""),
                status=cluster_data.get("status", "UNKNOWN"),
                version=cluster_data.get("version", ""),
                endpoint=cluster_data.get("endpoint"),
                platform_version=cluster_data.get("platformVersion"),
                created_at=cluster_data.get("createdAt"),
                region=region_name,
                # VPC configuration
                vpc_id=vpc_id,
                subnet_ids=subnet_ids,
                security_group_ids=security_group_ids,
                cluster_security_group_id=cluster_security_group_id,
                # IAM
                role_arn=cluster_data.get("roleArn"),
                # Logging
                enabled_log_types=enabled_log_types,
            )
            clusters.append(cluster)

        logger.debug(f"Discovered {len(clusters)} EKS clusters in {region_name}")
        return clusters
    except ClientError as e:
        logger.warning(f"Failed to discover EKS clusters: {e}")
        return []


def discover_eks_node_groups(
    profile_name: str | None = None,
    region: str | None = None,
    cluster_name: str | None = None,
) -> list[EKSNodeGroup]:
    """Discover EKS node groups for a cluster.

    Args:
        profile_name: AWS CLI profile name
        region: AWS region
        cluster_name: EKS cluster name (required)

    Returns:
        List of EKSNodeGroup objects
    """
    if not cluster_name:
        logger.warning("cluster_name is required for discover_eks_node_groups")
        return []

    session = create_session(profile_name, region)
    eks_client = session.client("eks")
    region_name = session.region_name or "us-east-1"

    try:
        node_groups = []
        paginator = eks_client.get_paginator("list_nodegroups")

        ng_names = []
        for page in paginator.paginate(clusterName=cluster_name):
            ng_names.extend(page.get("nodegroups", []))

        # Describe each node group
        for ng_name in ng_names:
            response = eks_client.describe_nodegroup(
                clusterName=cluster_name, nodegroupName=ng_name
            )
            ng_data = response.get("nodegroup", {})
            scaling = ng_data.get("scalingConfig", {})

            # Extract remote access configuration
            remote_access = ng_data.get("remoteAccess", {})
            source_security_groups = remote_access.get("sourceSecurityGroups", [])
            # Get first source security group if available
            remote_access_sg = source_security_groups[0] if source_security_groups else None

            # Extract launch template
            launch_template = ng_data.get("launchTemplate", {})
            launch_template_id = launch_template.get("id")

            node_group = EKSNodeGroup(
                nodegroup_name=ng_data.get("nodegroupName", ng_name),
                nodegroup_arn=ng_data.get("nodegroupArn", ""),
                cluster_name=cluster_name,
                status=ng_data.get("status", "UNKNOWN"),
                instance_types=ng_data.get("instanceTypes", []),
                desired_size=scaling.get("desiredSize", 0),
                min_size=scaling.get("minSize", 0),
                max_size=scaling.get("maxSize", 0),
                region=region_name,
                # Network configuration
                subnet_ids=ng_data.get("subnets", []),
                # IAM
                node_role_arn=ng_data.get("nodeRole"),
                # Remote access
                remote_access_security_group=remote_access_sg,
                # Launch template
                launch_template_id=launch_template_id,
            )
            node_groups.append(node_group)

        logger.debug(f"Discovered {len(node_groups)} EKS node groups for {cluster_name}")
        return node_groups
    except ClientError as e:
        logger.warning(f"Failed to discover EKS node groups: {e}")
        return []


def discover_all_eks_node_groups(
    profile_name: str | None = None,
    region: str | None = None,
) -> list[EKSNodeGroup]:
    """Discover all EKS node groups across all clusters in a region.

    Args:
        profile_name: AWS CLI profile name
        region: AWS region

    Returns:
        List of EKSNodeGroup objects from all clusters
    """
    clusters = discover_eks_clusters(profile_name, region)
    all_node_groups = []

    for cluster in clusters:
        node_groups = discover_eks_node_groups(profile_name, region, cluster.cluster_name)
        all_node_groups.extend(node_groups)

    return all_node_groups


def discover_eks_fargate_profiles(
    profile_name: str | None = None,
    region: str | None = None,
    cluster_name: str | None = None,
) -> list[EKSFargateProfile]:
    """Discover EKS Fargate profiles for a cluster.

    Args:
        profile_name: AWS CLI profile name
        region: AWS region
        cluster_name: EKS cluster name (required)

    Returns:
        List of EKSFargateProfile objects
    """
    if not cluster_name:
        logger.warning("cluster_name is required for discover_eks_fargate_profiles")
        return []

    session = create_session(profile_name, region)
    eks_client = session.client("eks")
    region_name = session.region_name or "us-east-1"

    try:
        profiles = []
        paginator = eks_client.get_paginator("list_fargate_profiles")

        profile_names = []
        for page in paginator.paginate(clusterName=cluster_name):
            profile_names.extend(page.get("fargateProfileNames", []))

        # Describe each Fargate profile
        for fp_name in profile_names:
            response = eks_client.describe_fargate_profile(
                clusterName=cluster_name, fargateProfileName=fp_name
            )
            fp_data = response.get("fargateProfile", {})

            profile = EKSFargateProfile(
                fargate_profile_name=fp_data.get("fargateProfileName", fp_name),
                fargate_profile_arn=fp_data.get("fargateProfileArn", ""),
                cluster_name=cluster_name,
                status=fp_data.get("status", "UNKNOWN"),
                pod_execution_role_arn=fp_data.get("podExecutionRoleArn", ""),
                selectors=fp_data.get("selectors", []),
                region=region_name,
            )
            profiles.append(profile)

        logger.debug(f"Discovered {len(profiles)} EKS Fargate profiles for {cluster_name}")
        return profiles
    except ClientError as e:
        logger.warning(f"Failed to discover EKS Fargate profiles: {e}")
        return []


def discover_all_eks_fargate_profiles(
    profile_name: str | None = None,
    region: str | None = None,
) -> list[EKSFargateProfile]:
    """Discover all EKS Fargate profiles across all clusters in a region.

    Args:
        profile_name: AWS CLI profile name
        region: AWS region

    Returns:
        List of EKSFargateProfile objects from all clusters
    """
    clusters = discover_eks_clusters(profile_name, region)
    all_profiles = []

    for cluster in clusters:
        profiles = discover_eks_fargate_profiles(profile_name, region, cluster.cluster_name)
        all_profiles.extend(profiles)

    return all_profiles
