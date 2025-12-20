"""YAML utility functions for safe loading and dumping."""

from pathlib import Path
from typing import Any, Optional, Union

import yaml


def safe_load(source: Union[str, Path, Any]) -> Any:
    """Safely load YAML content from a string, file path, or file object.

    Args:
        source: YAML string, Path to YAML file, or file-like object

    Returns:
        Parsed YAML content, or empty dict if content is empty/None

    Raises:
        FileNotFoundError: If path doesn't exist
        yaml.YAMLError: If YAML is malformed
    """
    if isinstance(source, Path):
        if not source.exists():
            raise FileNotFoundError(f"YAML file not found: {source}")
        with open(source) as f:
            return yaml.safe_load(f) or {}
    elif isinstance(source, str):
        # Check if it's a file path string
        path = Path(source)
        if path.exists() and path.is_file():
            with open(path) as f:
                return yaml.safe_load(f) or {}
        # Otherwise treat as YAML content
        return yaml.safe_load(source) or {}
    else:
        # Assume file-like object
        return yaml.safe_load(source) or {}


def safe_dump(
    data: Any,
    dest: Optional[Union[str, Path]] = None,
    default_flow_style: bool = False,
    allow_unicode: bool = True,
    sort_keys: bool = False,
    indent: int = 2,
) -> Optional[str]:
    """Safely dump data to YAML string or file.

    Args:
        data: Data to serialize to YAML
        dest: Optional file path to write to. If None, returns string.
        default_flow_style: Use flow style for collections
        allow_unicode: Allow unicode characters
        sort_keys: Sort dictionary keys
        indent: Indentation level

    Returns:
        YAML string if dest is None, otherwise None
    """
    kwargs = {
        "default_flow_style": default_flow_style,
        "allow_unicode": allow_unicode,
        "sort_keys": sort_keys,
        "indent": indent,
    }

    if dest is None:
        return yaml.safe_dump(data, **kwargs)

    dest_path = Path(dest)
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    with open(dest_path, "w") as f:
        yaml.safe_dump(data, f, **kwargs)

    return None
