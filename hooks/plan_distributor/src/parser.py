"""Parse plan markdown files to extract file paths."""

import re
from pathlib import Path


def extract_file_paths(content: str) -> list[str]:
    """Extract file paths from plan markdown content.

    Looks for:
    1. File Summary tables with paths
    2. Backtick-quoted paths
    3. Paths in CREATE/MODIFY/DELETE rows

    Args:
        content: Plan markdown content

    Returns:
        List of unique file paths found in the plan
    """
    paths: set[str] = set()

    # Pattern 1: Table rows with CREATE/MODIFY/DELETE actions
    # | CREATE | `lib/aws_utils/services/lambda_svc.py` |
    # | MODIFY | `lib/aws_utils/core/schemas.py` |
    table_pattern = r'\|\s*(?:CREATE|MODIFY|DELETE)\s*\|\s*`?([^`|\n]+)`?\s*\|'
    for match in re.finditer(table_pattern, content, re.IGNORECASE):
        path = match.group(1).strip()
        if path and not path.startswith('---'):
            paths.add(path)

    # Pattern 2: Backtick-quoted file paths (common in markdown)
    # `lib/aws_utils/services/sso.py`
    # `/workspace/.claude/hooks/plan_distributor/src/parser.py`
    backtick_pattern = r'`([^`\s]+(?:\.py|\.json|\.yaml|\.yml|\.md|\.toml|\.sh|\.ts|\.js|\.go|\.rs))`'
    for match in re.finditer(backtick_pattern, content):
        path = match.group(1).strip()
        if path:
            paths.add(path)

    # Pattern 3: "Files to create:" or "Files to modify:" sections
    # - /workspace/.claude/lib/aws_utils/services/lambda_svc.py
    list_item_pattern = r'^[-*]\s+(/[^\s]+(?:\.py|\.json|\.yaml|\.yml|\.md|\.toml|\.sh|\.ts|\.js|\.go|\.rs))'
    for match in re.finditer(list_item_pattern, content, re.MULTILINE):
        path = match.group(1).strip()
        if path:
            paths.add(path)

    # Pattern 4: **File**: /path/to/file.py
    file_header_pattern = r'\*\*File\*\*:\s*`?(/[^\s`]+)`?'
    for match in re.finditer(file_header_pattern, content):
        path = match.group(1).strip()
        if path:
            paths.add(path)

    # Pattern 5: **Source**: or **Target**: paths
    source_target_pattern = r'\*\*(?:Source|Target)\*\*:\s*`?(/[^\s`]+)`?'
    for match in re.finditer(source_target_pattern, content):
        path = match.group(1).strip()
        if path:
            paths.add(path)

    return sorted(paths)


def normalize_path(path: str, workspace_root: str = "/workspace") -> str:
    """Normalize a file path to absolute form.

    Args:
        path: File path (may be relative or absolute)
        workspace_root: Root workspace directory

    Returns:
        Absolute path string
    """
    if path.startswith('/'):
        return path

    # Relative paths like lib/aws_utils/... become /workspace/.claude/lib/aws_utils/...
    # or /workspace/lib/aws_utils/... depending on context

    # Check if it looks like a .claude submodule path
    if path.startswith('lib/') or path.startswith('hooks/') or path.startswith('skills/'):
        return f"{workspace_root}/.claude/{path}"

    return f"{workspace_root}/{path}"


def detect_project_roots(paths: list[str], workspace_root: str = "/workspace") -> dict[str, list[str]]:
    """Group file paths by their project root.

    Distribution rules:
    - /workspace/.claude/** -> /workspace/.claude/plans/
    - /workspace/projects/<name>/** -> /workspace/projects/<name>/plans/
    - /workspace/** (root files) -> /workspace/plans/

    Args:
        paths: List of absolute file paths
        workspace_root: Root workspace directory

    Returns:
        Dict mapping project plan directories to their relevant file paths
    """
    projects: dict[str, list[str]] = {}

    claude_path = f"{workspace_root}/.claude"
    projects_path = f"{workspace_root}/projects"

    for path in paths:
        normalized = normalize_path(path, workspace_root)

        # Rule 1: .claude files always go to .claude/plans
        if normalized.startswith(f"{claude_path}/"):
            plan_dir = f"{claude_path}/plans"
            if plan_dir not in projects:
                projects[plan_dir] = []
            projects[plan_dir].append(normalized)
            continue

        # Rule 2: /workspace/projects/<name>/** files
        if normalized.startswith(f"{projects_path}/"):
            # Extract project name: /workspace/projects/foo/bar.py -> foo
            remainder = normalized[len(f"{projects_path}/"):]
            if '/' in remainder:
                project_name = remainder.split('/')[0]
                plan_dir = f"{projects_path}/{project_name}/plans"
                if plan_dir not in projects:
                    projects[plan_dir] = []
                projects[plan_dir].append(normalized)
                continue

        # Rule 3: Root workspace files
        if normalized.startswith(f"{workspace_root}/"):
            plan_dir = f"{workspace_root}/plans"
            if plan_dir not in projects:
                projects[plan_dir] = []
            projects[plan_dir].append(normalized)

    return projects
