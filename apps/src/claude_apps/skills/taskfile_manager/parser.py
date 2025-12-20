"""Parse Taskfile.yml with line number tracking."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ruamel.yaml import YAML

from .rules import (
    Severity,
    Violation,
    check_aliases,
    check_platform_specific,
    check_silent_mode,
    check_task_description,
    check_task_naming,
    check_template_whitespace,
    check_variable_uppercase,
)


def parse_taskfile(file_path: Path) -> tuple[dict[str, Any], list[str]]:
    """Parse Taskfile.yml and return content with raw lines."""
    yaml = YAML()
    yaml.preserve_quotes = True

    with file_path.open() as f:
        content = yaml.load(f)

    raw_lines = file_path.read_text().splitlines()

    return content, raw_lines


def find_line_number(raw_lines: list[str], key: str, start_line: int = 0) -> int:
    """Find the line number where a key appears."""
    for i, line in enumerate(raw_lines[start_line:], start=start_line + 1):
        if line.strip().startswith(f"{key}:") or line.strip().startswith(f"  {key}:"):
            return i
    return start_line + 1


def validate_taskfile(file_path: Path) -> list[Violation]:
    """Validate a Taskfile against all rules."""
    violations: list[Violation] = []

    try:
        content, raw_lines = parse_taskfile(file_path)
    except Exception as e:
        return [
            Violation(
                line=1,
                column=0,
                rule="parse-error",
                severity=Severity.ERROR,
                message=f"Failed to parse Taskfile: {e}",
                original=str(file_path),
                suggested=None,
            )
        ]

    if content is None:
        return [
            Violation(
                line=1,
                column=0,
                rule="empty-file",
                severity=Severity.ERROR,
                message="Taskfile is empty",
                original=str(file_path),
                suggested=None,
            )
        ]

    # Check template whitespace in all lines
    for i, line in enumerate(raw_lines, start=1):
        violations.extend(check_template_whitespace(i, line))

    # Check variable naming
    if "vars" in content:
        vars_line = find_line_number(raw_lines, "vars")
        var_violations = check_variable_uppercase(content, vars_line, "")
        for v in var_violations:
            # Find actual line for each variable
            v.line = find_line_number(raw_lines, v.original, vars_line - 1)
        violations.extend(var_violations)

    # Check tasks
    if "tasks" in content and isinstance(content["tasks"], dict):
        tasks_line = find_line_number(raw_lines, "tasks")

        for task_name, task_config in content["tasks"].items():
            task_line = find_line_number(raw_lines, task_name, tasks_line - 1)

            # Task naming
            violations.extend(check_task_naming(task_name, task_line))

            # Task description
            violations.extend(check_task_description(task_name, task_config, task_line))

            # Platform-specific commands
            violations.extend(check_platform_specific(task_name, task_config, task_line))

            # Silent mode
            violations.extend(check_silent_mode(task_name, task_config, task_line))

            # Aliases for common tasks
            violations.extend(check_aliases(task_name, task_config, task_line))

    # Sort by line number
    violations.sort(key=lambda v: v.line)

    return violations
