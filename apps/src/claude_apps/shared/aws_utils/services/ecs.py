"""ECS service discovery."""

from botocore.exceptions import ClientError
from loguru import logger

from ..core.schemas import ECSCluster, ECSService, ECSTaskDefinition
from ..core.session import create_session


def discover_ecs_clusters(
    profile_name: str | None = None,
    region: str | None = None,
) -> list[ECSCluster]:
    """Discover all ECS clusters in a region.

    Args:
        profile_name: AWS CLI profile name
        region: AWS region

    Returns:
        List of ECSCluster objects
    """
    session = create_session(profile_name, region)
    ecs_client = session.client("ecs")
    region_name = session.region_name or "us-east-1"

    try:
        clusters = []
        paginator = ecs_client.get_paginator("list_clusters")

        cluster_arns = []
        for page in paginator.paginate():
            cluster_arns.extend(page.get("clusterArns", []))

        if not cluster_arns:
            return []

        # Describe clusters in batches of 100
        for i in range(0, len(cluster_arns), 100):
            batch = cluster_arns[i : i + 100]
            response = ecs_client.describe_clusters(clusters=batch)

            for cluster_data in response.get("clusters", []):
                cluster = ECSCluster(
                    cluster_name=cluster_data["clusterName"],
                    cluster_arn=cluster_data["clusterArn"],
                    status=cluster_data.get("status", "UNKNOWN"),
                    registered_container_instances=cluster_data.get(
                        "registeredContainerInstancesCount", 0
                    ),
                    running_tasks=cluster_data.get("runningTasksCount", 0),
                    pending_tasks=cluster_data.get("pendingTasksCount", 0),
                    active_services=cluster_data.get("activeServicesCount", 0),
                    region=region_name,
                )
                clusters.append(cluster)

        logger.debug(f"Discovered {len(clusters)} ECS clusters in {region_name}")
        return clusters
    except ClientError as e:
        logger.warning(f"Failed to discover ECS clusters: {e}")
        return []


def discover_ecs_services(
    profile_name: str | None = None,
    region: str | None = None,
    cluster_arn: str | None = None,
) -> list[ECSService]:
    """Discover ECS services in a cluster.

    Args:
        profile_name: AWS CLI profile name
        region: AWS region
        cluster_arn: Cluster ARN to query (required)

    Returns:
        List of ECSService objects
    """
    if not cluster_arn:
        logger.warning("cluster_arn is required for discover_ecs_services")
        return []

    session = create_session(profile_name, region)
    ecs_client = session.client("ecs")
    region_name = session.region_name or "us-east-1"

    try:
        services = []
        paginator = ecs_client.get_paginator("list_services")

        service_arns = []
        for page in paginator.paginate(cluster=cluster_arn):
            service_arns.extend(page.get("serviceArns", []))

        if not service_arns:
            return []

        # Describe services in batches of 10
        for i in range(0, len(service_arns), 10):
            batch = service_arns[i : i + 10]
            response = ecs_client.describe_services(cluster=cluster_arn, services=batch)

            for svc_data in response.get("services", []):
                # Extract network configuration (awsvpc mode)
                network_config = svc_data.get("networkConfiguration", {})
                awsvpc_config = network_config.get("awsvpcConfiguration", {})
                subnet_ids = awsvpc_config.get("subnets", [])
                security_group_ids = awsvpc_config.get("securityGroups", [])

                # Extract load balancer target groups
                load_balancers = svc_data.get("loadBalancers", [])
                target_groups = [
                    lb.get("targetGroupArn")
                    for lb in load_balancers
                    if lb.get("targetGroupArn")
                ]

                # Extract service registries (Cloud Map)
                registries = svc_data.get("serviceRegistries", [])
                registry_arns = [
                    reg.get("registryArn")
                    for reg in registries
                    if reg.get("registryArn")
                ]

                service = ECSService(
                    service_name=svc_data["serviceName"],
                    service_arn=svc_data["serviceArn"],
                    cluster_arn=svc_data["clusterArn"],
                    status=svc_data.get("status", "UNKNOWN"),
                    desired_count=svc_data.get("desiredCount", 0),
                    running_count=svc_data.get("runningCount", 0),
                    launch_type=svc_data.get("launchType", "EC2"),
                    task_definition=svc_data.get("taskDefinition", ""),
                    region=region_name,
                    # VPC configuration
                    subnet_ids=subnet_ids,
                    security_group_ids=security_group_ids,
                    # Load balancers
                    load_balancer_target_groups=target_groups,
                    # Service discovery
                    service_registries=registry_arns,
                )
                services.append(service)

        logger.debug(f"Discovered {len(services)} ECS services in cluster")
        return services
    except ClientError as e:
        logger.warning(f"Failed to discover ECS services: {e}")
        return []


def discover_all_ecs_services(
    profile_name: str | None = None,
    region: str | None = None,
) -> list[ECSService]:
    """Discover all ECS services across all clusters in a region.

    Args:
        profile_name: AWS CLI profile name
        region: AWS region

    Returns:
        List of ECSService objects from all clusters
    """
    clusters = discover_ecs_clusters(profile_name, region)
    all_services = []

    for cluster in clusters:
        services = discover_ecs_services(profile_name, region, cluster.cluster_arn)
        all_services.extend(services)

    return all_services


def discover_ecs_task_definitions(
    profile_name: str | None = None,
    region: str | None = None,
    status: str = "ACTIVE",
) -> list[ECSTaskDefinition]:
    """Discover ECS task definitions in a region.

    Args:
        profile_name: AWS CLI profile name
        region: AWS region
        status: Task definition status filter (ACTIVE or INACTIVE)

    Returns:
        List of ECSTaskDefinition objects
    """
    session = create_session(profile_name, region)
    ecs_client = session.client("ecs")
    region_name = session.region_name or "us-east-1"

    try:
        task_defs = []
        paginator = ecs_client.get_paginator("list_task_definitions")

        task_def_arns = []
        for page in paginator.paginate(status=status):
            task_def_arns.extend(page.get("taskDefinitionArns", []))

        # Describe each task definition
        for arn in task_def_arns:
            response = ecs_client.describe_task_definition(taskDefinition=arn)
            td_data = response.get("taskDefinition", {})

            task_def = ECSTaskDefinition(
                family=td_data.get("family", ""),
                task_definition_arn=td_data.get("taskDefinitionArn", arn),
                revision=td_data.get("revision", 0),
                status=td_data.get("status", "UNKNOWN"),
                cpu=td_data.get("cpu"),
                memory=td_data.get("memory"),
                requires_compatibilities=td_data.get("requiresCompatibilities", []),
                region=region_name,
            )
            task_defs.append(task_def)

        logger.debug(f"Discovered {len(task_defs)} ECS task definitions in {region_name}")
        return task_defs
    except ClientError as e:
        logger.warning(f"Failed to discover ECS task definitions: {e}")
        return []
