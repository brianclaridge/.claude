"""CodePipeline discovery."""

from botocore.exceptions import ClientError
from loguru import logger

from aws_utils.core.schemas import CodePipeline
from aws_utils.core.session import create_session, get_default_region


def discover_pipelines(
    profile_name: str | None = None,
    region: str | None = None,
) -> list[CodePipeline]:
    """Discover CodePipeline pipelines.

    Args:
        profile_name: AWS CLI profile name
        region: AWS region

    Returns:
        List of CodePipeline objects
    """
    region = region or get_default_region()
    session = create_session(profile_name, region)
    client = session.client("codepipeline")

    try:
        pipelines = []
        paginator = client.get_paginator("list_pipelines")

        for page in paginator.paginate():
            for pipeline_summary in page.get("pipelines", []):
                pipeline_name = pipeline_summary.get("name", "")

                # Get detailed info for each pipeline
                try:
                    detail = client.get_pipeline(name=pipeline_name)
                    pipeline_data = detail.get("pipeline", {})
                    metadata = detail.get("metadata", {})

                    # Count stages and extract stage names
                    stages = pipeline_data.get("stages", [])
                    stage_names = [s.get("name", "") for s in stages]

                    # Format dates
                    created = metadata.get("created")
                    updated = metadata.get("updated")

                    # Get pipeline type and execution mode
                    pipeline_type = pipeline_data.get("pipelineType", "V1")
                    execution_mode = pipeline_data.get("executionMode")

                    # Get tags
                    tags = {}
                    try:
                        tags_response = client.list_tags_for_resource(
                            resourceArn=metadata.get("pipelineArn", "")
                        )
                        for tag in tags_response.get("tags", []):
                            tags[tag.get("key", "")] = tag.get("value", "")
                    except ClientError:
                        pass  # Tags may not be accessible

                    pipeline = CodePipeline(
                        name=pipeline_name,
                        arn=metadata.get("pipelineArn"),
                        role_arn=pipeline_data.get("roleArn"),
                        stage_count=len(stages),
                        stages=stage_names,
                        pipeline_type=pipeline_type,
                        execution_mode=execution_mode,
                        created=created.isoformat() if created else None,
                        updated=updated.isoformat() if updated else None,
                        tags=tags,
                        region=region,
                    )
                    pipelines.append(pipeline)
                except ClientError as e:
                    logger.warning(f"Failed to describe pipeline {pipeline_name}: {e}")

        logger.debug(f"Discovered {len(pipelines)} CodePipeline pipelines in {region}")
        return pipelines
    except ClientError as e:
        logger.warning(f"Failed to discover CodePipeline pipelines: {e}")
        return []
