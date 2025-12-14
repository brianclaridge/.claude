"""Entry point for taskfile-validator."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import structlog

from .parser import validate_taskfile
from .report import print_report
from .rules import Severity

log = structlog.get_logger()


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate Taskfile.yml against Rule 090 best practices",
        prog="taskfile-validator",
    )
    parser.add_argument(
        "file",
        type=Path,
        nargs="?",
        default=Path("Taskfile.yml"),
        help="Path to Taskfile.yml (default: ./Taskfile.yml)",
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--strict",
        "-s",
        action="store_true",
        help="Treat warnings as errors",
    )

    args = parser.parse_args()

    file_path = args.file.resolve()

    if not file_path.exists():
        log.error("file_not_found", path=str(file_path))
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        return 1

    log.info("validating_taskfile", path=str(file_path))

    violations = validate_taskfile(file_path)

    print_report(file_path, violations, args.format)

    # Determine exit code
    errors = sum(1 for v in violations if v.severity == Severity.ERROR)
    warnings = sum(1 for v in violations if v.severity == Severity.WARNING)

    if errors > 0:
        return 1
    if args.strict and warnings > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
