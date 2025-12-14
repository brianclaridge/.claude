"""Template syntax validation."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


def validate_templates(config: dict[str, Any], config_dir: Path) -> list[dict]:
    """Validate all template files for syntax errors."""
    violations = []

    # Get template files from config
    template_files = []
    if "inputFiles" in config:
        template_files = [config_dir / f for f in config["inputFiles"]]
    elif "inputDir" in config:
        input_dir = config_dir / config["inputDir"]
        if input_dir.exists():
            template_files = list(input_dir.glob("**/*"))

    for template_path in template_files:
        if not template_path.exists():
            violations.append({
                "file": str(template_path),
                "line": 0,
                "rule": "template-exists",
                "severity": "error",
                "message": f"Template file not found: {template_path}",
            })
            continue

        if template_path.is_dir():
            continue

        violations.extend(validate_template_file(template_path))

    return violations


def validate_template_file(template_path: Path) -> list[dict]:
    """Validate a single template file."""
    violations = []

    try:
        content = template_path.read_text()
    except Exception as e:
        violations.append({
            "file": str(template_path),
            "line": 0,
            "rule": "template-read",
            "severity": "error",
            "message": f"Failed to read template: {e}",
        })
        return violations

    # Check for mismatched delimiters
    open_count = content.count("{{")
    close_count = content.count("}}")

    if open_count != close_count:
        violations.append({
            "file": str(template_path),
            "line": 1,
            "rule": "template-syntax",
            "severity": "error",
            "message": f"Mismatched template delimiters: {open_count} '{{{{' vs {close_count} '}}}}'",
        })

    # Check for nested templates (invalid)
    for i, line in enumerate(content.splitlines(), start=1):
        if re.search(r"\{\{[^}]*\{\{", line):
            violations.append({
                "file": str(template_path),
                "line": i,
                "rule": "template-syntax",
                "severity": "error",
                "message": "Nested template actions are not allowed",
            })

    return violations
