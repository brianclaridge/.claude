"""Report generation for validation results."""

from __future__ import annotations

import json
from enum import Enum
from pathlib import Path


class ReportFormat(Enum):
    TEXT = "text"
    JSON = "json"


def generate_report(
    config_path: Path,
    violations: list[dict],
    render_results: list[dict],
    format: ReportFormat = ReportFormat.TEXT,
) -> str:
    """Generate validation report in specified format."""
    if format == ReportFormat.JSON:
        return generate_json_report(config_path, violations, render_results)
    return generate_text_report(config_path, violations, render_results)


def generate_json_report(
    config_path: Path,
    violations: list[dict],
    render_results: list[dict],
) -> str:
    """Generate JSON format report."""
    report = {
        "config": str(config_path),
        "violations": violations,
        "render_results": render_results,
        "summary": {
            "errors": sum(1 for v in violations if v.get("severity") == "error"),
            "warnings": sum(1 for v in violations if v.get("severity") == "warning"),
            "info": sum(1 for v in violations if v.get("severity") == "info"),
        },
    }
    return json.dumps(report, indent=2)


def generate_text_report(
    config_path: Path,
    violations: list[dict],
    render_results: list[dict],
) -> str:
    """Generate text format report."""
    lines = [
        "Gomplate Validation Report",
        "==========================",
        f"Config: {config_path}",
        "",
    ]

    # Group violations by severity
    errors = [v for v in violations if v.get("severity") == "error"]
    warnings = [v for v in violations if v.get("severity") == "warning"]
    info = [v for v in violations if v.get("severity") == "info"]

    if errors:
        lines.append("ERRORS (must fix):")
        for v in errors:
            lines.append(format_violation(v))
        lines.append("")

    if warnings:
        lines.append("WARNINGS (should fix):")
        for v in warnings:
            lines.append(format_violation(v))
        lines.append("")

    if info:
        lines.append("INFO (optional):")
        for v in info:
            lines.append(format_violation(v))
        lines.append("")

    # Render results
    if render_results:
        lines.append("Dry-Run Rendering:")
        for result in render_results:
            file_name = Path(result["file"]).name
            if result["success"]:
                lines.append(f"  + {file_name}: OK")
            else:
                lines.append(f"  x {file_name}: FAILED")
                if result.get("error"):
                    lines.append(f"    Error: {result['error']}")
                if result.get("missing_vars"):
                    lines.append(f"    Missing: {', '.join(result['missing_vars'])}")
        lines.append("")

    # Summary
    error_count = len(errors)
    warning_count = len(warnings)
    info_count = len(info)

    lines.append(f"Summary: {error_count} errors, {warning_count} warnings, {info_count} info")

    if error_count > 0:
        lines.append("Status: FAILED")
    elif warning_count > 0:
        lines.append("Status: PASSED (with warnings)")
    else:
        lines.append("Status: PASSED")

    return "\n".join(lines)


def format_violation(violation: dict) -> str:
    """Format a single violation for text output."""
    file_name = Path(violation.get("file", "unknown")).name
    line = violation.get("line", 0)
    message = violation.get("message", "Unknown error")

    result = f"  Line {line} ({file_name}): {message}"

    if "suggested" in violation:
        result += f"\n    Suggestion: {violation['suggested']}"

    return result
