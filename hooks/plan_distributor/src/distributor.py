"""Distribute plan files to the canonical plans directory."""

import shutil
from pathlib import Path
from typing import NamedTuple

from .parser import extract_file_paths, detect_project_roots, generate_plan_filename


class DistributionResult(NamedTuple):
    """Result of plan distribution."""

    source_path: str
    destinations: list[str]
    success: bool
    message: str


def distribute_plan(
    plan_path: str,
    workspace_root: str = "/workspace"
) -> DistributionResult:
    """Distribute a plan file to appropriate project directories.

    Args:
        plan_path: Path to the source plan file
        workspace_root: Root workspace directory

    Returns:
        DistributionResult with details of the distribution
    """
    source = Path(plan_path)

    if not source.exists():
        return DistributionResult(
            source_path=plan_path,
            destinations=[],
            success=False,
            message=f"Source plan file not found: {plan_path}"
        )

    # Read plan content
    content = source.read_text()

    # Extract file paths from plan
    file_paths = extract_file_paths(content)

    if not file_paths:
        return DistributionResult(
            source_path=plan_path,
            destinations=[],
            success=True,
            message="No file paths found in plan; no distribution needed"
        )

    # Detect project roots from paths
    project_plans = detect_project_roots(file_paths, workspace_root)

    if not project_plans:
        return DistributionResult(
            source_path=plan_path,
            destinations=[],
            success=True,
            message="No project directories identified; no distribution needed"
        )

    destinations: list[str] = []
    errors: list[str] = []

    # Generate proper filename from plan content
    new_filename = generate_plan_filename(content)

    for plan_dir, _paths in project_plans.items():
        try:
            # Create plans directory if it doesn't exist
            dest_dir = Path(plan_dir)
            dest_dir.mkdir(parents=True, exist_ok=True)

            # Copy plan file to destination with proper naming
            dest_path = dest_dir / new_filename
            shutil.copy2(source, dest_path)
            destinations.append(str(dest_path))

        except OSError as e:
            errors.append(f"Failed to copy to {plan_dir}: {e}")

    if errors:
        return DistributionResult(
            source_path=plan_path,
            destinations=destinations,
            success=False,
            message=f"Partial distribution. Errors: {'; '.join(errors)}"
        )

    return DistributionResult(
        source_path=plan_path,
        destinations=destinations,
        success=True,
        message=f"Plan distributed to {len(destinations)} project(s)"
    )


def get_distribution_summary(result: DistributionResult) -> str:
    """Generate a human-readable summary of distribution result.

    Args:
        result: DistributionResult from distribute_plan

    Returns:
        Formatted summary string
    """
    lines = [
        f"Source: {result.source_path}",
        f"Status: {'Success' if result.success else 'Failed'}",
        f"Message: {result.message}",
    ]

    if result.destinations:
        lines.append("Destinations:")
        for dest in result.destinations:
            lines.append(f"  - {dest}")

    return "\n".join(lines)
