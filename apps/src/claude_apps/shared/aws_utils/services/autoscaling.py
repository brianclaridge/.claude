"""Auto Scaling Group discovery."""

from botocore.exceptions import ClientError
from loguru import logger

from ..core.schemas import AutoScalingGroup
from ..core.session import create_session, get_default_region


def discover_auto_scaling_groups(
    profile_name: str | None = None,
    region: str | None = None,
) -> list[AutoScalingGroup]:
    """Discover all Auto Scaling Groups in a region.

    Args:
        profile_name: AWS CLI profile name
        region: AWS region

    Returns:
        List of AutoScalingGroup objects
    """
    region = region or get_default_region()
    session = create_session(profile_name, region)
    autoscaling = session.client("autoscaling")

    try:
        asgs = []
        paginator = autoscaling.get_paginator("describe_auto_scaling_groups")

        for page in paginator.paginate():
            for asg in page.get("AutoScalingGroups", []):
                # Extract launch template info
                launch_template = asg.get("LaunchTemplate", {})
                launch_template_id = launch_template.get("LaunchTemplateId")
                launch_template_name = launch_template.get("LaunchTemplateName")

                # Extract instance IDs
                instances = [
                    inst.get("InstanceId", "") for inst in asg.get("Instances", [])
                ]

                # Extract tags
                tags_dict = {}
                for tag in asg.get("Tags", []):
                    tags_dict[tag["Key"]] = tag["Value"]

                auto_scaling_group = AutoScalingGroup(
                    name=asg["AutoScalingGroupName"],
                    arn=asg["AutoScalingGroupARN"],
                    launch_template_id=launch_template_id,
                    launch_template_name=launch_template_name,
                    launch_configuration_name=asg.get("LaunchConfigurationName"),
                    min_size=asg["MinSize"],
                    max_size=asg["MaxSize"],
                    desired_capacity=asg["DesiredCapacity"],
                    default_cooldown=asg.get("DefaultCooldown"),
                    availability_zones=asg.get("AvailabilityZones", []),
                    vpc_zone_identifier=asg.get("VPCZoneIdentifier"),
                    health_check_type=asg.get("HealthCheckType", "EC2"),
                    health_check_grace_period=asg.get("HealthCheckGracePeriod"),
                    target_group_arns=asg.get("TargetGroupARNs", []),
                    load_balancer_names=asg.get("LoadBalancerNames", []),
                    instances=instances,
                    created_time=asg.get("CreatedTime", "").isoformat()
                    if asg.get("CreatedTime")
                    else None,
                    tags=tags_dict,
                    region=region,
                )
                asgs.append(auto_scaling_group)

        logger.debug(f"Discovered {len(asgs)} Auto Scaling Groups in {region}")
        return asgs
    except ClientError as e:
        logger.warning(f"Failed to discover Auto Scaling Groups: {e}")
        return []
