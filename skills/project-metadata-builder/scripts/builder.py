#!/usr/bin/env python3
"""
Project metadata builder - main orchestrator.

Usage:
    uv run python scripts/builder.py <project_path> [--session-id <id>]
"""
import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

from loguru import logger

from .collectors import (
    collect_dependencies,
    collect_git_metadata,
    collect_languages,
    collect_mcp_servers,
    collect_runtime,
)
from .config import get_projects_file_path, load_config
from .schema import Activity, ProjectMetadata, Session, Structure
from .utils import expand_path, load_projects_yaml, save_projects_yaml

# Configure logging
LOG_PATH = Path(os.path.expanduser("~/.claude/.data/logs/project-metadata-builder"))
LOG_PATH.mkdir(parents=True, exist_ok=True)

logger.add(
    LOG_PATH / "builder.log",
    rotation="10 MB",
    retention="7 days",
    level="INFO",
)


def detect_project_type(project_path: Path) -> str:
    """Detect project type based on structure."""
    indicators = {
        "monorepo": [
            "packages",
            "apps",
            "libs",
            "workspaces",
            ".claude/skills",
            ".claude/agents",
        ],
        "library": ["setup.py", "setup.cfg", "pyproject.toml", "package.json"],
        "application": ["Dockerfile", "docker-compose.yml", "main.py", "app.py"],
    }

    for proj_type, paths in indicators.items():
        for path in paths:
            if (project_path / path).exists():
                return proj_type

    return "standard"


def detect_key_directories(project_path: Path) -> list[str]:
    """Detect key directories in the project."""
    key_dirs = []
    common_dirs = [
        "src",
        "lib",
        "app",
        "apps",
        "packages",
        "components",
        "services",
        "api",
        "tests",
        "docs",
        "scripts",
        "config",
        ".claude/agents",
        ".claude/skills",
        ".claude/hooks",
        ".claude/directives",
    ]

    for dir_name in common_dirs:
        if (project_path / dir_name).is_dir():
            key_dirs.append(f"{dir_name}/")

    return key_dirs


def detect_entry_points(project_path: Path) -> list[str]:
    """Detect entry point files."""
    entry_files = []
    common_entries = [
        "main.py",
        "app.py",
        "index.py",
        "index.js",
        "index.ts",
        "main.go",
        "main.rs",
        "Makefile",
        "Taskfile.yml",
        "docker-compose.yml",
        "package.json",
        "pyproject.toml",
    ]

    for filename in common_entries:
        if (project_path / filename).is_file():
            entry_files.append(filename)

    # Also check .claude directory
    claude_entries = ["docker-compose.yml", "Taskfile.yml"]
    for filename in claude_entries:
        if (project_path / ".claude" / filename).is_file():
            entry_files.append(f".claude/{filename}")

    return entry_files


def detect_frameworks(project_path: Path) -> list[str]:
    """Detect frameworks from dependencies and files."""
    frameworks: set[str] = set()

    # Check for common framework indicators
    framework_indicators = {
        "react": ["package.json"],
        "nextjs": ["next.config.js", "next.config.mjs", "next.config.ts"],
        "vue": ["vue.config.js", "nuxt.config.js"],
        "django": ["manage.py", "settings.py"],
        "fastapi": ["main.py"],
        "flask": ["app.py"],
        "express": ["package.json"],
        "docker": ["Dockerfile", "docker-compose.yml"],
        "playwright": [".claude/skills/playwright-automation"],
        "structlog": [".claude/hooks/directive_loader"],
    }

    for framework, indicators in framework_indicators.items():
        for indicator in indicators:
            if (project_path / indicator).exists():
                frameworks.add(framework)
                break

    # Check package.json for frameworks
    package_json = project_path / "package.json"
    if package_json.exists():
        try:
            import json

            data = json.loads(package_json.read_text())
            deps = {
                **data.get("dependencies", {}),
                **data.get("devDependencies", {}),
            }
            if "react" in deps:
                frameworks.add("react")
            if "next" in deps:
                frameworks.add("nextjs")
            if "vue" in deps:
                frameworks.add("vue")
            if "express" in deps:
                frameworks.add("express")
            if "playwright" in deps:
                frameworks.add("playwright")
        except (json.JSONDecodeError, IOError, OSError) as e:
            logger.debug(f"Could not parse package.json: {e}")

    return sorted(frameworks)


def build_project_metadata(
    project_path: Path,
    session_id: str | None = None,
) -> ProjectMetadata:
    """Build complete metadata for a project."""
    logger.info(f"Building metadata for: {project_path}")

    # Basic identity
    name = project_path.name
    slug = name.lower().replace(" ", "-")

    # Try to get description from README
    description = ""
    readme = project_path / "README.md"
    if readme.exists():
        try:
            content = readme.read_text()
            # Get first non-header line
            for line in content.split("\n"):
                line = line.strip()
                if line and not line.startswith("#") and not line.startswith(">"):
                    description = line[:200]  # Truncate
                    break
        except (IOError, OSError, UnicodeDecodeError) as e:
            logger.debug(f"Could not read README: {e}")

    # Collect metadata from collectors
    git = collect_git_metadata(project_path)
    languages = collect_languages(project_path)
    dependencies = collect_dependencies(project_path)
    runtime = collect_runtime(project_path)
    runtime.mcp_servers = collect_mcp_servers(project_path)
    frameworks = detect_frameworks(project_path)

    # Build structure
    structure = Structure(
        type=detect_project_type(project_path),
        key_directories=detect_key_directories(project_path),
        entry_points=detect_entry_points(project_path),
    )

    # Build activity
    activity = Activity(
        status="active",
        first_seen=datetime.now(),
        last_updated=datetime.now(),
    )

    # Build session entry if session_id provided
    sessions = []
    if session_id:
        sessions.append(
            Session(
                id=session_id,
                started=datetime.now(),
                commits=0,
                files_changed=0,
            )
        )

    return ProjectMetadata(
        path=str(project_path.absolute()),
        name=name,
        slug=slug,
        description=description,
        git=git,
        languages=languages,
        frameworks=frameworks,
        dependencies=dependencies,
        structure=structure,
        runtime=runtime,
        activity=activity,
        sessions=sessions,
    )


def update_projects_registry(
    metadata: ProjectMetadata,
    config_path: Path,
    session_history_limit: int = 10,
) -> bool:
    """Update the projects registry with new metadata."""
    # Load existing projects
    existing = load_projects_yaml(config_path)

    project_key = metadata.path

    # Check if project already exists
    if project_key in existing.get("projects", {}):
        # Merge with existing
        old_data = existing["projects"][project_key]

        # Preserve first_seen
        if "activity" in old_data and "first_seen" in old_data["activity"]:
            metadata.activity.first_seen = datetime.fromisoformat(
                old_data["activity"]["first_seen"]
            )

        # Merge sessions (keep last N)
        old_sessions = old_data.get("sessions", [])
        all_sessions = metadata.sessions + [
            Session(
                id=s["id"],
                started=datetime.fromisoformat(s["started"]),
                ended=datetime.fromisoformat(s["ended"]) if s.get("ended") else None,
                commits=s.get("commits", 0),
                files_changed=s.get("files_changed", 0),
            )
            for s in old_sessions
        ]
        metadata.sessions = all_sessions[:session_history_limit]

    # Update registry
    existing["projects"][project_key] = metadata.to_dict()

    # Save
    return save_projects_yaml(config_path, existing)


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Build project metadata for Claude Code",
    )
    parser.add_argument(
        "project_path",
        type=str,
        help="Path to the project directory",
    )
    parser.add_argument(
        "--session-id",
        type=str,
        default=None,
        help="Current session ID for history tracking",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )

    args = parser.parse_args()

    if args.debug:
        logger.remove()
        logger.add(sys.stderr, level="DEBUG")

    # Expand path
    project_path = expand_path(args.project_path)
    if not project_path.exists():
        logger.error(f"Project path does not exist: {project_path}")
        return 1

    # Load config
    config = load_config()

    # Build metadata
    metadata = build_project_metadata(project_path, args.session_id)

    # Get projects file path
    projects_file = get_projects_file_path(config)

    # Update registry
    success = update_projects_registry(
        metadata,
        projects_file,
        config.project_metadata.session_history_limit,
    )

    if success:
        logger.info(f"Successfully updated {projects_file}")
        print(f"Project metadata updated: {projects_file}")
        return 0
    else:
        logger.error("Failed to update projects registry")
        return 1


if __name__ == "__main__":
    sys.exit(main())
