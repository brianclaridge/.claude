"""Output formatting for JSON and text modes."""

from __future__ import annotations

import json
from typing import Any


def format_output(data: dict[str, Any], fmt: str = "text") -> str:
    """Format output as JSON or human-readable text."""
    if fmt == "json":
        return json.dumps(data, indent=2)
    return format_text(data)


def format_text(data: dict[str, Any]) -> str:
    """Format data as human-readable text."""
    lines = []

    for key, value in data.items():
        if value is None:
            continue

        if isinstance(value, list):
            if value:
                lines.append(f"{key}:")
                for item in value:
                    if isinstance(item, dict):
                        lines.append(f"  - {format_dict_inline(item)}")
                    else:
                        lines.append(f"  - {item}")
        elif isinstance(value, dict):
            lines.append(f"{key}:")
            for k, v in value.items():
                lines.append(f"  {k}: {v}")
        elif isinstance(value, bool):
            lines.append(f"{key}: {'yes' if value else 'no'}")
        else:
            lines.append(f"{key}: {value}")

    return "\n".join(lines)


def format_dict_inline(d: dict[str, Any]) -> str:
    """Format dict as inline key=value."""
    parts = [f"{k}={v}" for k, v in d.items() if v is not None]
    return ", ".join(parts)
