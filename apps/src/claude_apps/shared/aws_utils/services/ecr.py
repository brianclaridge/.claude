"""ECR repository discovery."""

from botocore.exceptions import ClientError
from loguru import logger

from ..core.schemas import ECRRepository
from ..core.session import create_session


def discover_ecr_repositories(
    profile_name: str | None = None,
    region: str | None = None,
) -> list[ECRRepository]:
    """Discover all ECR repositories in a region.

    Args:
        profile_name: AWS CLI profile name
        region: AWS region

    Returns:
        List of ECRRepository objects
    """
    session = create_session(profile_name, region)
    ecr_client = session.client("ecr")
    region_name = session.region_name or "us-east-1"

    try:
        repositories = []
        paginator = ecr_client.get_paginator("describe_repositories")

        for page in paginator.paginate():
            for repo in page.get("repositories", []):
                repo_name = repo.get("repositoryName", "")

                # Get image count
                image_count = 0
                try:
                    img_paginator = ecr_client.get_paginator("list_images")
                    for img_page in img_paginator.paginate(
                        repositoryName=repo_name, filter={"tagStatus": "ANY"}
                    ):
                        image_count += len(img_page.get("imageIds", []))
                except ClientError:
                    pass

                scan_config = repo.get("imageScanningConfiguration", {})

                repository = ECRRepository(
                    repository_name=repo_name,
                    arn=repo.get("repositoryArn", ""),
                    uri=repo.get("repositoryUri", ""),
                    registry_id=repo.get("registryId", ""),
                    created_at=repo.get("createdAt"),
                    image_count=image_count,
                    image_tag_mutability=repo.get("imageTagMutability", "MUTABLE"),
                    scan_on_push=scan_config.get("scanOnPush", False),
                    region=region_name,
                )
                repositories.append(repository)

        logger.debug(f"Discovered {len(repositories)} ECR repositories in {region_name}")
        return repositories
    except ClientError as e:
        logger.warning(f"Failed to discover ECR repositories: {e}")
        return []
