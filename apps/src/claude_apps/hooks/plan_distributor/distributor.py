"""Distribute plan files to the canonical plans directory.

All plans are copied to ${CLAUDE_PLANS_PATH} regardless of content.
"""

import os
import shutil
from pathlib import Path
from typing import NamedTuple

from .parser import generate_plan_filename


class DistributionResult(NamedTuple):
    """Result of plan distribution."""

    source_path: str
    destinations: list[str]
    success: bool
    message: str


def get_plans_directory() -> Path:
    """Get the canonical plans directory from CLAUDE_PLANS_PATH env var.

    Returns:
        Path to the plans directory

    Raises:
        ValueError: If CLAUDE_PLANS_PATH is not set
    """
    plans_path = os.environ.get("CLAUDE_PLANS_PATH")
    if not plans_path:
        raise ValueError("CLAUDE_PLANS_PATH environment variable is not set")
    return Path(plans_path)


def distribute_plan(
    plan_path: str,
    workspace_root: str = "/workspace"
) -> DistributionResult:
    """Distribute a plan file to ${CLAUDE_PLANS_PATH}.

    All plans are copied regardless of their content. The destination
    directory is created if it doesn't exist.

    Args:
        plan_path: Path to the source plan file
        workspace_root: Unused, kept for API compatibility

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

    # Get destination directory from environment
    try:
        dest_dir = get_plans_directory()
    except ValueError as e:
        return DistributionResult(
            source_path=plan_path,
            destinations=[],
            success=False,
            message=str(e)
        )

    # Read plan content for filename generation
    content = source.read_text()

    # Generate proper filename from plan content
    new_filename = generate_plan_filename(content)

    try:
        # Create plans directory if it doesn't exist
        dest_dir.mkdir(parents=True, exist_ok=True)

        # Copy plan file to destination with proper naming
        dest_path = dest_dir / new_filename
        shutil.copy2(source, dest_path)

        return DistributionResult(
            source_path=plan_path,
            destinations=[str(dest_path)],
            success=True,
            message=f"Plan distributed to {dest_path}"
        )

    except OSError as e:
        return DistributionResult(
            source_path=plan_path,
            destinations=[],
            success=False,
            message=f"Failed to copy plan: {e}"
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
