"""RDS database discovery."""

from botocore.exceptions import ClientError
from loguru import logger

from aws_utils.core.schemas import RDSCluster, RDSInstance
from aws_utils.core.session import create_session


def discover_rds_instances(
    profile_name: str | None = None,
    region: str | None = None,
) -> list[RDSInstance]:
    """Discover all RDS instances in a region.

    Args:
        profile_name: AWS CLI profile name
        region: AWS region

    Returns:
        List of RDSInstance objects
    """
    session = create_session(profile_name, region)
    rds = session.client("rds")
    region_name = session.region_name or "us-east-1"

    try:
        instances = []
        paginator = rds.get_paginator("describe_db_instances")

        for page in paginator.paginate():
            for instance_data in page.get("DBInstances", []):
                endpoint = instance_data.get("Endpoint", {})
                instance = RDSInstance(
                    db_instance_identifier=instance_data["DBInstanceIdentifier"],
                    engine=instance_data["Engine"],
                    engine_version=instance_data["EngineVersion"],
                    instance_class=instance_data["DBInstanceClass"],
                    status=instance_data["DBInstanceStatus"],
                    endpoint=endpoint.get("Address"),
                    port=endpoint.get("Port"),
                    arn=instance_data["DBInstanceArn"],
                    region=region_name,
                )
                instances.append(instance)

        logger.debug(f"Discovered {len(instances)} RDS instances in {region_name}")
        return instances
    except ClientError as e:
        logger.warning(f"Failed to discover RDS instances: {e}")
        return []


def discover_rds_clusters(
    profile_name: str | None = None,
    region: str | None = None,
) -> list[RDSCluster]:
    """Discover all RDS Aurora clusters in a region.

    Args:
        profile_name: AWS CLI profile name
        region: AWS region

    Returns:
        List of RDSCluster objects
    """
    session = create_session(profile_name, region)
    rds = session.client("rds")
    region_name = session.region_name or "us-east-1"

    try:
        clusters = []
        paginator = rds.get_paginator("describe_db_clusters")

        for page in paginator.paginate():
            for cluster_data in page.get("DBClusters", []):
                cluster = RDSCluster(
                    cluster_identifier=cluster_data["DBClusterIdentifier"],
                    engine=cluster_data["Engine"],
                    engine_version=cluster_data["EngineVersion"],
                    status=cluster_data["Status"],
                    endpoint=cluster_data.get("Endpoint"),
                    reader_endpoint=cluster_data.get("ReaderEndpoint"),
                    port=cluster_data.get("Port"),
                    arn=cluster_data["DBClusterArn"],
                    region=region_name,
                )
                clusters.append(cluster)

        logger.debug(f"Discovered {len(clusters)} RDS clusters in {region_name}")
        return clusters
    except ClientError as e:
        logger.warning(f"Failed to discover RDS clusters: {e}")
        return []
