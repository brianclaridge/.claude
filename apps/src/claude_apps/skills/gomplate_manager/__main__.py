"""CLI entry point for gomplate validator."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import structlog

from .config import parse_config, validate_config
from .template import validate_templates
from .rules import run_all_rules
from .render import dry_run_render
from .report import generate_report, ReportFormat

structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(20),
)

logger = structlog.get_logger()


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate gomplate configuration against Rule 095 best practices"
    )
    parser.add_argument(
        "config_path",
        type=Path,
        nargs="?",
        default=Path(".claude/config/gomplate.yaml"),
        help="Path to gomplate.yaml (default: .claude/config/gomplate.yaml)",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Test render templates with current environment",
    )

    args = parser.parse_args()

    if not args.config_path.exists():
        logger.error("config_not_found", path=str(args.config_path))
        print(f"Error: Config file not found: {args.config_path}", file=sys.stderr)
        return 1

    logger.info("validating_config", path=str(args.config_path))

    # Parse and validate config
    config, config_errors = parse_config(args.config_path)
    if config_errors:
        for error in config_errors:
            logger.error("config_error", **error)

    # Validate config structure
    structure_errors = validate_config(config) if config else []

    # Run template validations
    template_violations = []
    if config:
        template_violations = validate_templates(config, args.config_path.parent)

    # Run all rules
    rule_violations = []
    if config:
        rule_violations = run_all_rules(config, args.config_path.parent)

    # Dry run if requested
    render_results = []
    if args.dry_run and config:
        render_results = dry_run_render(config, args.config_path.parent)

    # Generate report
    all_violations = config_errors + structure_errors + template_violations + rule_violations
    report_format = ReportFormat.JSON if args.format == "json" else ReportFormat.TEXT

    report = generate_report(
        config_path=args.config_path,
        violations=all_violations,
        render_results=render_results,
        format=report_format,
    )

    print(report)

    # Determine exit code
    error_count = sum(1 for v in all_violations if v.get("severity") == "error")
    warning_count = sum(1 for v in all_violations if v.get("severity") == "warning")

    if error_count > 0:
        return 1
    if args.strict and warning_count > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
