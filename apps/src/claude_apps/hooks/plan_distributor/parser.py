"""Parse plan markdown files to extract topic and generate filenames."""

import re
from datetime import datetime


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
