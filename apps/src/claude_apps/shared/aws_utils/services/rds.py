"""RDS database discovery."""

from botocore.exceptions import ClientError
from loguru import logger

from ..core.schemas import RDSCluster, RDSInstance
from ..core.session import create_session


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

                # Extract VPC/subnet group info
                db_subnet_group = instance_data.get("DBSubnetGroup", {})
                vpc_id = db_subnet_group.get("VpcId")
                db_subnet_group_name = db_subnet_group.get("DBSubnetGroupName")

                # Extract security group IDs
                vpc_security_groups = instance_data.get("VpcSecurityGroups", [])
                security_group_ids = [
                    sg.get("VpcSecurityGroupId")
                    for sg in vpc_security_groups
                    if sg.get("VpcSecurityGroupId")
                ]

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
                    # VPC configuration
                    vpc_id=vpc_id,
                    db_subnet_group_name=db_subnet_group_name,
                    security_group_ids=security_group_ids,
                    # Encryption
                    kms_key_id=instance_data.get("KmsKeyId"),
                    storage_encrypted=instance_data.get("StorageEncrypted", False),
                    # Monitoring
                    monitoring_role_arn=instance_data.get("MonitoringRoleArn"),
                    # Cluster membership
                    db_cluster_identifier=instance_data.get("DBClusterIdentifier"),
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
                # Note: DBSubnetGroup for clusters is a string, not a dict
                db_subnet_group_name = cluster_data.get("DBSubnetGroup")

                # Extract security group IDs
                vpc_security_groups = cluster_data.get("VpcSecurityGroups", [])
                security_group_ids = [
                    sg.get("VpcSecurityGroupId")
                    for sg in vpc_security_groups
                    if sg.get("VpcSecurityGroupId")
                ]

                # Extract cluster member identifiers
                db_cluster_members = cluster_data.get("DBClusterMembers", [])
                member_identifiers = [
                    member.get("DBInstanceIdentifier")
                    for member in db_cluster_members
                    if member.get("DBInstanceIdentifier")
                ]

                # Extract associated IAM roles
                associated_roles = cluster_data.get("AssociatedRoles", [])
                role_arns = [
                    role.get("RoleArn")
                    for role in associated_roles
                    if role.get("RoleArn")
                ]

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
                    # VPC configuration (VpcId not directly available on cluster)
                    db_subnet_group_name=db_subnet_group_name,
                    security_group_ids=security_group_ids,
                    # Encryption
                    kms_key_id=cluster_data.get("KmsKeyId"),
                    # Cluster members
                    db_cluster_members=member_identifiers,
                    # Associated roles
                    associated_role_arns=role_arns,
                )
                clusters.append(cluster)

        logger.debug(f"Discovered {len(clusters)} RDS clusters in {region_name}")
        return clusters
    except ClientError as e:
        logger.warning(f"Failed to discover RDS clusters: {e}")
        return []
