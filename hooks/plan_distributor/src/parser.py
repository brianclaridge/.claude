"""Parse plan markdown files to extract file paths and metadata."""

import re
from datetime import datetime
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


def extract_plan_topic(content: str) -> str:
    """Extract the topic from plan content for filename generation.

    Looks for:
    1. # Plan: <topic> header
    2. # <topic> (any H1 header)
    3. First sentence as fallback

    Args:
        content: Plan markdown content

    Returns:
        Kebab-case topic string (e.g., "user-authentication")
    """
    # Pattern 1: # Plan: <topic>
    plan_header = re.search(r'^#\s+Plan:\s*(.+)$', content, re.MULTILINE)
    if plan_header:
        topic = plan_header.group(1).strip()
        return _to_kebab_case(topic)

    # Pattern 2: Any H1 header
    h1_header = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    if h1_header:
        topic = h1_header.group(1).strip()
        return _to_kebab_case(topic)

    # Fallback: first 50 chars
    first_line = content.split('\n')[0][:50] if content else "untitled"
    return _to_kebab_case(first_line) or "untitled"


def _to_kebab_case(text: str) -> str:
    """Convert text to kebab-case for filenames.

    Args:
        text: Input text

    Returns:
        Kebab-case string (lowercase, hyphens, no special chars)
    """
    # Remove markdown formatting
    text = re.sub(r'[`*_\[\]()]', '', text)
    # Convert to lowercase
    text = text.lower()
    # Replace spaces and underscores with hyphens
    text = re.sub(r'[\s_]+', '-', text)
    # Remove non-alphanumeric except hyphens
    text = re.sub(r'[^a-z0-9-]', '', text)
    # Collapse multiple hyphens
    text = re.sub(r'-+', '-', text)
    # Trim leading/trailing hyphens
    text = text.strip('-')
    # Limit length
    return text[:50] if text else "untitled"


def generate_plan_filename(content: str) -> str:
    """Generate a properly formatted plan filename.

    Format: YYYYMMDD_HHMMSS_<topic>.md

    Args:
        content: Plan markdown content

    Returns:
        Formatted filename string
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    topic = extract_plan_topic(content)
    return f"{timestamp}_{topic}.md"


def get_plans_directory() -> str:
    """Get the canonical plans directory from environment.

    Returns:
        Path to the plans directory (defaults to /workspace/.claude/plans)
    """
    import os
    return os.environ.get("CLAUDE_PLANS_PATH", "/workspace/.claude/plans")


def detect_project_roots(paths: list[str], workspace_root: str = "/workspace") -> dict[str, list[str]]:
    """Return the single canonical plans directory.

    All plans go to ${CLAUDE_PLANS_PATH} regardless of what files they affect.
    This provides a single source of truth for all plans.

    Args:
        paths: List of file paths from the plan (used for reference only)
        workspace_root: Root workspace directory (unused, kept for compatibility)

    Returns:
        Dict with single entry: plans_dir -> list of paths
    """
    if not paths:
        return {}

    plan_dir = get_plans_directory()

    # Normalize all paths for reference
    normalized_paths = [normalize_path(p, workspace_root) for p in paths]

    return {plan_dir: normalized_paths}
