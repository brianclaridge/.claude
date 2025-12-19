"""CloudWatch Logs and Alarms discovery."""

from botocore.exceptions import ClientError
from loguru import logger

from aws_utils.core.schemas import CloudWatchLogGroup, CloudWatchAlarm
from aws_utils.core.session import create_session, get_default_region


def discover_log_groups(
    profile_name: str | None = None,
    region: str | None = None,
) -> list[CloudWatchLogGroup]:
    """Discover all CloudWatch Log Groups in a region.

    Args:
        profile_name: AWS CLI profile name
        region: AWS region

    Returns:
        List of CloudWatchLogGroup objects
    """
    region = region or get_default_region()
    session = create_session(profile_name, region)
    logs = session.client("logs")

    try:
        log_groups = []
        paginator = logs.get_paginator("describe_log_groups")

        for page in paginator.paginate():
            for lg in page.get("logGroups", []):
                log_group = CloudWatchLogGroup(
                    log_group_name=lg["logGroupName"],
                    arn=lg.get("arn", ""),
                    creation_time=str(lg.get("creationTime"))
                    if lg.get("creationTime")
                    else None,
                    retention_days=lg.get("retentionInDays"),
                    stored_bytes=lg.get("storedBytes", 0),
                    metric_filter_count=lg.get("metricFilterCount", 0),
                    kms_key_id=lg.get("kmsKeyId"),
                    region=region,
                )
                log_groups.append(log_group)

        logger.debug(f"Discovered {len(log_groups)} CloudWatch log groups in {region}")
        return log_groups
    except ClientError as e:
        logger.warning(f"Failed to discover CloudWatch log groups: {e}")
        return []


def discover_alarms(
    profile_name: str | None = None,
    region: str | None = None,
) -> list[CloudWatchAlarm]:
    """Discover all CloudWatch Alarms in a region.

    Args:
        profile_name: AWS CLI profile name
        region: AWS region

    Returns:
        List of CloudWatchAlarm objects
    """
    region = region or get_default_region()
    session = create_session(profile_name, region)
    cloudwatch = session.client("cloudwatch")

    try:
        alarms = []
        paginator = cloudwatch.get_paginator("describe_alarms")

        for page in paginator.paginate():
            # Process metric alarms
            for alarm in page.get("MetricAlarms", []):
                cw_alarm = CloudWatchAlarm(
                    alarm_name=alarm["AlarmName"],
                    alarm_arn=alarm.get("AlarmArn", ""),
                    alarm_description=alarm.get("AlarmDescription"),
                    state_value=alarm.get("StateValue", "INSUFFICIENT_DATA"),
                    state_reason=alarm.get("StateReason"),
                    metric_name=alarm.get("MetricName"),
                    namespace=alarm.get("Namespace"),
                    statistic=alarm.get("Statistic"),
                    period=alarm.get("Period"),
                    evaluation_periods=alarm.get("EvaluationPeriods"),
                    threshold=alarm.get("Threshold"),
                    comparison_operator=alarm.get("ComparisonOperator"),
                    actions_enabled=alarm.get("ActionsEnabled", True),
                    alarm_actions=alarm.get("AlarmActions", []),
                    ok_actions=alarm.get("OKActions", []),
                    region=region,
                )
                alarms.append(cw_alarm)

            # Process composite alarms
            for alarm in page.get("CompositeAlarms", []):
                cw_alarm = CloudWatchAlarm(
                    alarm_name=alarm["AlarmName"],
                    alarm_arn=alarm.get("AlarmArn", ""),
                    alarm_description=alarm.get("AlarmDescription"),
                    state_value=alarm.get("StateValue", "INSUFFICIENT_DATA"),
                    state_reason=alarm.get("StateReason"),
                    metric_name=None,  # Composite alarms don't have metrics
                    namespace=None,
                    statistic=None,
                    period=None,
                    evaluation_periods=None,
                    threshold=None,
                    comparison_operator=None,
                    actions_enabled=alarm.get("ActionsEnabled", True),
                    alarm_actions=alarm.get("AlarmActions", []),
                    ok_actions=alarm.get("OKActions", []),
                    region=region,
                )
                alarms.append(cw_alarm)

        logger.debug(f"Discovered {len(alarms)} CloudWatch alarms in {region}")
        return alarms
    except ClientError as e:
        logger.warning(f"Failed to discover CloudWatch alarms: {e}")
        return []
