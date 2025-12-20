"""CodeBuild project discovery."""

from botocore.exceptions import ClientError
from loguru import logger

from ..core.schemas import CodeBuildProject
from ..core.session import create_session, get_default_region


def discover_codebuild_projects(
    profile_name: str | None = None,
    region: str | None = None,
) -> list[CodeBuildProject]:
    """Discover CodeBuild projects.

    Args:
        profile_name: AWS CLI profile name
        region: AWS region

    Returns:
        List of CodeBuildProject objects
    """
    region = region or get_default_region()
    session = create_session(profile_name, region)
    client = session.client("codebuild")

    try:
        projects = []

        # First, list all project names
        project_names = []
        paginator = client.get_paginator("list_projects")

        for page in paginator.paginate():
            project_names.extend(page.get("projects", []))

        if not project_names:
            logger.debug(f"No CodeBuild projects found in {region}")
            return []

        # Batch describe projects (max 100 per call)
        for i in range(0, len(project_names), 100):
            batch = project_names[i : i + 100]
            response = client.batch_get_projects(names=batch)

            for proj_data in response.get("projects", []):
                # Extract source info
                source = proj_data.get("source", {})
                source_type = source.get("type", "")
                source_location = source.get("location")

                # Extract environment info
                environment = proj_data.get("environment", {})
                env_type = environment.get("type")
                env_image = environment.get("image")
                compute_type = environment.get("computeType")

                # Format dates
                created = proj_data.get("created")
                last_modified = proj_data.get("lastModified")

                # Convert tags list to dict
                tags = {}
                for tag in proj_data.get("tags", []):
                    tags[tag.get("key", "")] = tag.get("value", "")

                project = CodeBuildProject(
                    name=proj_data.get("name", ""),
                    arn=proj_data.get("arn", ""),
                    source_type=source_type,
                    source_location=source_location,
                    environment_type=env_type,
                    environment_image=env_image,
                    compute_type=compute_type,
                    service_role=proj_data.get("serviceRole"),
                    timeout_in_minutes=proj_data.get("timeoutInMinutes"),
                    build_batch_config_enabled=proj_data.get("buildBatchConfig") is not None,
                    created=created.isoformat() if created else None,
                    last_modified=last_modified.isoformat() if last_modified else None,
                    tags=tags,
                    region=region,
                )
                projects.append(project)

        logger.debug(f"Discovered {len(projects)} CodeBuild projects in {region}")
        return projects
    except ClientError as e:
        logger.warning(f"Failed to discover CodeBuild projects: {e}")
        return []
