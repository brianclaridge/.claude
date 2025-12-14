"""Validation rules based on Rule 095 gomplate best practices."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


def run_all_rules(config: dict[str, Any], config_dir: Path) -> list[dict]:
    """Run all validation rules against config and templates."""
    violations = []

    # Get template files
    template_files = []
    if "inputFiles" in config:
        template_files = [config_dir / f for f in config["inputFiles"]]
    elif "inputDir" in config:
        input_dir = config_dir / config["inputDir"]
        if input_dir.exists():
            template_files = [f for f in input_dir.glob("**/*") if f.is_file()]

    # Run rules on each template
    for template_path in template_files:
        if not template_path.exists() or template_path.is_dir():
            continue

        content = template_path.read_text()

        violations.extend(check_getenv_usage(content, str(template_path)))
        violations.extend(check_template_whitespace(content, str(template_path)))

    # Run rules on output paths
    violations.extend(check_output_paths(config))

    return violations


def check_getenv_usage(content: str, file_path: str) -> list[dict]:
    """Check for getenv usage - should use .Env instead per Rule 095."""
    violations = []

    # Pattern for getenv function call
    pattern = r'\{\{\s*getenv\s+"(\w+)"'

    for i, line in enumerate(content.splitlines(), start=1):
        for match in re.finditer(pattern, line):
            var_name = match.group(1)
            violations.append({
                "file": file_path,
                "line": i,
                "rule": "env-access-style",
                "severity": "warning",
                "message": f"Use .Env.{var_name} instead of getenv for fail-fast behavior",
                "original": match.group(0),
                "suggested": f"{{{{ .Env.{var_name} }}}}",
            })

    return violations


def check_template_whitespace(content: str, file_path: str) -> list[dict]:
    """Check for proper whitespace in template delimiters."""
    violations = []

    for i, line in enumerate(content.splitlines(), start=1):
        # Find all template expressions
        templates = re.findall(r"\{\{[^}]+\}\}", line)

        for template in templates:
            # Check for compact style (no spaces)
            # Skip trim markers like {{- or -}}
            inner = template[2:-2]
            if inner and not inner.startswith("-") and not inner.startswith(" "):
                violations.append({
                    "file": file_path,
                    "line": i,
                    "rule": "template-whitespace",
                    "severity": "info",
                    "message": "Use spaces inside template delimiters for readability",
                    "original": template,
                })

    return violations


def check_output_paths(config: dict[str, Any]) -> list[dict]:
    """Check that output paths are absolute."""
    violations = []

    output_files = config.get("outputFiles", [])
    for path in output_files:
        if not path.startswith("/"):
            violations.append({
                "file": "gomplate.yaml",
                "line": 0,
                "rule": "output-path-absolute",
                "severity": "warning",
                "message": f"Output path should be absolute in container: '{path}'",
                "suggested": f"/{path}" if not path.startswith("/") else path,
            })

    return violations
