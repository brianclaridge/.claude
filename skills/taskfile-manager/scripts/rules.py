"""Validation rules based on Rule 090 Taskfile best practices."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable


class Severity(Enum):
    """Violation severity levels."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class Violation:
    """A single rule violation."""

    line: int
    column: int
    rule: str
    severity: Severity
    message: str
    original: str
    suggested: str | None = None


@dataclass
class Rule:
    """A validation rule definition."""

    id: str
    name: str
    severity: Severity
    description: str
    check: Callable[[Any, int, str], list[Violation]]


def check_variable_uppercase(content: dict[str, Any], line: int, raw_line: str) -> list[Violation]:
    """Check that variable names are UPPERCASE."""
    violations = []

    if "vars" in content and isinstance(content["vars"], dict):
        for var_name in content["vars"].keys():
            if not var_name.isupper():
                violations.append(
                    Violation(
                        line=line,
                        column=0,
                        rule="variable-uppercase",
                        severity=Severity.ERROR,
                        message=f"Variable '{var_name}' should be UPPERCASE",
                        original=var_name,
                        suggested=var_name.upper(),
                    )
                )

    return violations


def check_template_whitespace(line_num: int, raw_line: str) -> list[Violation]:
    """Check for whitespace in template expressions."""
    violations = []

    # Pattern: {{ .VAR }} or {{. VAR}} or {{ .VAR}}
    pattern = r"\{\{\s+\.|\.\s+\}\}"
    if re.search(pattern, raw_line):
        # Find the offending template
        templates = re.findall(r"\{\{[^}]+\}\}", raw_line)
        for template in templates:
            if re.search(pattern, template):
                fixed = re.sub(r"\{\{\s+\.", "{{.", template)
                fixed = re.sub(r"\.\s+\}\}", ".}}", fixed)
                violations.append(
                    Violation(
                        line=line_num,
                        column=raw_line.find(template),
                        rule="template-whitespace",
                        severity=Severity.ERROR,
                        message=f"Template has whitespace: '{template}'",
                        original=template,
                        suggested=fixed,
                    )
                )

    return violations


def check_task_naming(task_name: str, line: int) -> list[Violation]:
    """Check that task names use kebab-case or namespace:task format."""
    violations = []

    # Valid patterns: kebab-case or namespace:kebab-case
    # Invalid: camelCase, snake_case, PascalCase
    parts = task_name.split(":")
    for part in parts:
        # Check for uppercase or underscore (excluding leading underscore for private)
        if re.search(r"[A-Z]", part) or (re.search(r"_", part) and not part.startswith("_")):
            suggested = part.lower().replace("_", "-")
            violations.append(
                Violation(
                    line=line,
                    column=0,
                    rule="task-kebab-case",
                    severity=Severity.WARNING,
                    message=f"Task '{task_name}' should use kebab-case",
                    original=task_name,
                    suggested=":".join(p.lower().replace("_", "-") for p in parts),
                )
            )
            break

    return violations


def check_task_description(task_name: str, task_config: dict[str, Any], line: int) -> list[Violation]:
    """Check that tasks have desc: field."""
    violations = []

    # Skip internal/private tasks (start with _)
    if task_name.startswith("_"):
        return violations

    if isinstance(task_config, dict) and "desc" not in task_config:
        violations.append(
            Violation(
                line=line,
                column=0,
                rule="task-description",
                severity=Severity.WARNING,
                message=f"Task '{task_name}' is missing 'desc:' field",
                original=task_name,
                suggested=f"desc: Description for {task_name}",
            )
        )

    return violations


def check_platform_specific(task_name: str, task_config: dict[str, Any], line: int) -> list[Violation]:
    """Check for OS-specific commands without platforms: directive."""
    violations = []

    if not isinstance(task_config, dict):
        return violations

    # Unix-only commands
    unix_patterns = [
        r"\brm\s+-rf\b",
        r"\bchmod\b",
        r"\bchown\b",
        r"\bln\s+-s\b",
        r"\bsed\s+",
        r"\bawk\s+",
    ]

    # Windows-only commands
    windows_patterns = [
        r"\bdel\s+",
        r"\brmdir\s+",
        r"\bcopy\s+",
        r"\bmove\s+",
        r"\bicacls\b",
    ]

    cmds = task_config.get("cmds", [])
    has_platforms = "platforms" in task_config

    if not has_platforms and cmds:
        cmd_str = str(cmds)
        for pattern in unix_patterns:
            if re.search(pattern, cmd_str):
                violations.append(
                    Violation(
                        line=line,
                        column=0,
                        rule="platform-directive",
                        severity=Severity.WARNING,
                        message=f"Task '{task_name}' uses Unix-specific commands without 'platforms:' directive",
                        original=task_name,
                        suggested="platforms: [linux, darwin]",
                    )
                )
                break

        for pattern in windows_patterns:
            if re.search(pattern, cmd_str):
                violations.append(
                    Violation(
                        line=line,
                        column=0,
                        rule="platform-directive",
                        severity=Severity.WARNING,
                        message=f"Task '{task_name}' uses Windows-specific commands without 'platforms:' directive",
                        original=task_name,
                        suggested="platforms: [windows]",
                    )
                )
                break

    return violations


def check_silent_mode(task_name: str, task_config: dict[str, Any], line: int) -> list[Violation]:
    """Check if silent: true is used for cleaner output."""
    violations = []

    if isinstance(task_config, dict) and "silent" not in task_config:
        # Only suggest for tasks with commands
        if "cmds" in task_config:
            violations.append(
                Violation(
                    line=line,
                    column=0,
                    rule="silent-mode",
                    severity=Severity.INFO,
                    message=f"Consider adding 'silent: true' to task '{task_name}' for cleaner output",
                    original=task_name,
                    suggested="silent: true",
                )
            )

    return violations


def check_aliases(task_name: str, task_config: dict[str, Any], line: int) -> list[Violation]:
    """Check if common tasks have aliases."""
    violations = []

    common_tasks = ["build", "test", "run", "clean", "install", "deploy", "lint", "format"]

    if task_name in common_tasks:
        if isinstance(task_config, dict) and "aliases" not in task_config:
            suggested_alias = task_name[0]  # First letter as alias
            violations.append(
                Violation(
                    line=line,
                    column=0,
                    rule="task-aliases",
                    severity=Severity.INFO,
                    message=f"Consider adding alias for common task '{task_name}'",
                    original=task_name,
                    suggested=f"aliases: [{suggested_alias}]",
                )
            )

    return violations


# All rules registry
RULES: list[Rule] = [
    Rule(
        id="variable-uppercase",
        name="Variable Naming",
        severity=Severity.ERROR,
        description="Variables must be UPPERCASE",
        check=lambda c, l, r: check_variable_uppercase(c, l, r),
    ),
    Rule(
        id="template-whitespace",
        name="Template Syntax",
        severity=Severity.ERROR,
        description="No whitespace in {{.VAR}} templates",
        check=lambda c, l, r: check_template_whitespace(l, r),
    ),
]
