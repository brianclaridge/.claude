"""Generate validation reports."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .rules import Severity, Violation


def generate_json_report(file_path: Path, violations: list[Violation]) -> dict[str, Any]:
    """Generate JSON report for programmatic consumption."""
    errors = sum(1 for v in violations if v.severity == Severity.ERROR)
    warnings = sum(1 for v in violations if v.severity == Severity.WARNING)
    info = sum(1 for v in violations if v.severity == Severity.INFO)

    return {
        "file": str(file_path),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "violations": [
            {
                "line": v.line,
                "column": v.column,
                "rule": v.rule,
                "severity": v.severity.value,
                "message": v.message,
                "original": v.original,
                "suggested": v.suggested,
            }
            for v in violations
        ],
        "summary": {
            "errors": errors,
            "warnings": warnings,
            "info": info,
            "passed": errors == 0,
        },
    }


def generate_text_report(file_path: Path, violations: list[Violation]) -> str:
    """Generate human-readable text report."""
    lines = [
        "Taskfile Validation Report",
        "=" * 26,
        f"File: {file_path}",
        f"Timestamp: {datetime.now(timezone.utc).isoformat()}",
        "",
    ]

    errors = [v for v in violations if v.severity == Severity.ERROR]
    warnings = [v for v in violations if v.severity == Severity.WARNING]
    info = [v for v in violations if v.severity == Severity.INFO]

    if errors:
        lines.append("ERRORS (must fix):")
        for v in errors:
            lines.append(f"  Line {v.line}: {v.message}")
            if v.suggested:
                lines.append(f"           Fix: {v.suggested}")
        lines.append("")

    if warnings:
        lines.append("WARNINGS (should fix):")
        for v in warnings:
            lines.append(f"  Line {v.line}: {v.message}")
            if v.suggested:
                lines.append(f"           Suggestion: {v.suggested}")
        lines.append("")

    if info:
        lines.append("INFO (optional):")
        for v in info:
            lines.append(f"  Line {v.line}: {v.message}")
            if v.suggested:
                lines.append(f"           Consider: {v.suggested}")
        lines.append("")

    # Summary
    lines.append("-" * 40)
    lines.append(f"Summary: {len(errors)} errors, {len(warnings)} warnings, {len(info)} info")

    if len(errors) > 0:
        lines.append("Status: FAILED")
    elif len(warnings) > 0:
        lines.append("Status: PASSED WITH WARNINGS")
    else:
        lines.append("Status: PASSED")

    return "\n".join(lines)


def print_report(file_path: Path, violations: list[Violation], output_format: str = "text") -> None:
    """Print report to stdout."""
    if output_format == "json":
        report = generate_json_report(file_path, violations)
        print(json.dumps(report, indent=2))
    else:
        report = generate_text_report(file_path, violations)
        print(report)
