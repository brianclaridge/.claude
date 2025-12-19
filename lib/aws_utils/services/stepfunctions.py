"""Step Functions state machine and activity discovery."""

from botocore.exceptions import ClientError
from loguru import logger

from aws_utils.core.schemas import SFNActivity, StateMachine
from aws_utils.core.session import create_session


def discover_state_machines(
    profile_name: str | None = None,
    region: str | None = None,
) -> list[StateMachine]:
    """Discover all Step Functions state machines in a region.

    Args:
        profile_name: AWS CLI profile name
        region: AWS region

    Returns:
        List of StateMachine objects
    """
    session = create_session(profile_name, region)
    sfn = session.client("stepfunctions")
    region_name = session.region_name or "us-east-1"

    try:
        state_machines = []
        paginator = sfn.get_paginator("list_state_machines")

        # First collect all state machine ARNs
        sm_list = []
        for page in paginator.paginate():
            sm_list.extend(page.get("stateMachines", []))

        # Then describe each to get role and logging config
        for sm_data in sm_list:
            sm_arn = sm_data["stateMachineArn"]

            # Get detailed info including role and logging
            try:
                describe_resp = sfn.describe_state_machine(stateMachineArn=sm_arn)
                role_arn = describe_resp.get("roleArn")
                logging_config = describe_resp.get("loggingConfiguration", {})

                # Extract log group ARN and level
                destinations = logging_config.get("destinations", [])
                log_group_arn = None
                if destinations:
                    # Get first CloudWatch destination
                    for dest in destinations:
                        cw_log = dest.get("cloudWatchLogsLogGroup", {})
                        if cw_log.get("logGroupArn"):
                            log_group_arn = cw_log["logGroupArn"]
                            break

                log_level = logging_config.get("level")  # ALL, ERROR, FATAL, OFF
            except ClientError:
                # Fall back to basic info if describe fails
                role_arn = None
                log_group_arn = None
                log_level = None

            state_machine = StateMachine(
                name=sm_data["name"],
                arn=sm_arn,
                status="ACTIVE",  # list_state_machines doesn't return status
                machine_type=sm_data.get("type", "STANDARD"),
                creation_date=sm_data["creationDate"].isoformat(),
                region=region_name,
                # IAM
                role_arn=role_arn,
                # Logging
                log_group_arn=log_group_arn,
                log_level=log_level,
            )
            state_machines.append(state_machine)

        logger.debug(f"Discovered {len(state_machines)} state machines in {region_name}")
        return state_machines
    except ClientError as e:
        logger.warning(f"Failed to discover state machines: {e}")
        return []


def discover_sfn_activities(
    profile_name: str | None = None,
    region: str | None = None,
) -> list[SFNActivity]:
    """Discover all Step Functions activities in a region.

    Args:
        profile_name: AWS CLI profile name
        region: AWS region

    Returns:
        List of SFNActivity objects
    """
    session = create_session(profile_name, region)
    sfn = session.client("stepfunctions")
    region_name = session.region_name or "us-east-1"

    try:
        activities = []
        paginator = sfn.get_paginator("list_activities")

        for page in paginator.paginate():
            for activity_data in page.get("activities", []):
                activity = SFNActivity(
                    name=activity_data["name"],
                    arn=activity_data["activityArn"],
                    creation_date=activity_data["creationDate"].isoformat(),
                    region=region_name,
                )
                activities.append(activity)

        logger.debug(f"Discovered {len(activities)} Step Functions activities in {region_name}")
        return activities
    except ClientError as e:
        logger.warning(f"Failed to discover Step Functions activities: {e}")
        return []
