"""
Dependency collection from project files.
"""
import json
import re
from pathlib import Path

from loguru import logger

from ..schema import Dependencies


def collect_dependencies(project_path: Path) -> Dependencies:
    """Collect dependencies from various project files."""
    deps = Dependencies()

    # Collect Python dependencies
    deps.python = _collect_python_deps(project_path)

    # Collect Node dependencies
    deps.node = _collect_node_deps(project_path)

    logger.info(
        f"Found {len(deps.python)} Python deps, "
        f"{len(deps.node)} Node deps"
    )
    return deps


def _collect_python_deps(project_path: Path) -> list[str]:
    """Collect Python dependencies from pyproject.toml or requirements.txt."""
    deps: list[str] = []

    # Try pyproject.toml first
    pyproject = project_path / "pyproject.toml"
    if pyproject.exists():
        deps.extend(_parse_pyproject_toml(pyproject))

    # Try requirements.txt
    requirements = project_path / "requirements.txt"
    if requirements.exists():
        deps.extend(_parse_requirements_txt(requirements))

    # Also check .claude subdirectory for skills
    claude_dir = project_path / ".claude"
    if claude_dir.exists():
        for skill_dir in (claude_dir / "skills").glob("*/"):
            skill_pyproject = skill_dir / "pyproject.toml"
            if skill_pyproject.exists():
                deps.extend(_parse_pyproject_toml(skill_pyproject))

    # Deduplicate
    return list(dict.fromkeys(deps))


def _parse_pyproject_toml(path: Path) -> list[str]:
    """Parse dependencies from pyproject.toml."""
    deps: list[str] = []
    try:
        content = path.read_text()

        # Simple regex to find dependencies array
        # Look for dependencies = [ ... ]
        match = re.search(
            r'dependencies\s*=\s*\[(.*?)\]',
            content,
            re.DOTALL,
        )
        if match:
            deps_str = match.group(1)
            # Extract quoted strings
            for dep_match in re.finditer(r'"([^"]+)"', deps_str):
                deps.append(dep_match.group(1))

    except Exception as e:
        logger.debug(f"Error parsing {path}: {e}")

    return deps


def _parse_requirements_txt(path: Path) -> list[str]:
    """Parse dependencies from requirements.txt."""
    deps: list[str] = []
    try:
        for line in path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and not line.startswith("-"):
                deps.append(line)
    except Exception as e:
        logger.debug(f"Error parsing {path}: {e}")

    return deps


def _collect_node_deps(project_path: Path) -> list[str]:
    """Collect Node dependencies from package.json."""
    deps: list[str] = []

    package_json = project_path / "package.json"
    if not package_json.exists():
        return deps

    try:
        data = json.loads(package_json.read_text())

        for key in ["dependencies", "devDependencies", "peerDependencies"]:
            if key in data:
                for name, version in data[key].items():
                    deps.append(f"{name}@{version}")

    except Exception as e:
        logger.debug(f"Error parsing {package_json}: {e}")

    return deps
