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

        for page in paginator.paginate():
            for sm_data in page.get("stateMachines", []):
                state_machine = StateMachine(
                    name=sm_data["name"],
                    arn=sm_data["stateMachineArn"],
                    status="ACTIVE",  # list_state_machines doesn't return status
                    machine_type=sm_data.get("type", "STANDARD"),
                    creation_date=sm_data["creationDate"].isoformat(),
                    region=region_name,
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
