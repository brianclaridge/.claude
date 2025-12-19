#!/usr/bin/env python3
"""Validate rule files for format and consistency.

Checks:
- Rule header format: # RULE: NNN [optional-name]
- No duplicate rule numbers
- CRITICAL marker presence
- Valid markdown structure
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import NamedTuple


class RuleInfo(NamedTuple):
    """Parsed rule information."""

    number: int
    name: str
    has_critical: bool
    path: Path


class ValidationResult(NamedTuple):
    """Validation result for a rule file."""

    path: Path
    errors: list[str]
    warnings: list[str]


RULE_HEADER_PATTERN = re.compile(r"^# RULE:\s*(\d{3})(?:\s+(.+))?$")
CRITICAL_PATTERN = re.compile(r"\*\*CRITICAL\*\*")


def parse_rule_file(path: Path) -> RuleInfo | None:
    """Parse a rule file and extract metadata."""
    try:
        content = path.read_text()
        lines = content.split("\n")

        if not lines:
            return None

        # Check first line for rule header
        match = RULE_HEADER_PATTERN.match(lines[0])
        if not match:
            return None

        number = int(match.group(1))
        name = match.group(2) or ""
        has_critical = bool(CRITICAL_PATTERN.search(content))

        return RuleInfo(number=number, name=name, has_critical=has_critical, path=path)

    except Exception:
        return None


def validate_rule_file(path: Path) -> ValidationResult:
    """Validate a single rule file."""
    errors: list[str] = []
    warnings: list[str] = []

    try:
        content = path.read_text()
        lines = content.split("\n")
    except Exception as e:
        return ValidationResult(path, [f"Could not read file: {e}"], [])

    if not lines:
        errors.append("File is empty")
        return ValidationResult(path, errors, warnings)

    # Check header format
    first_line = lines[0]
    if not first_line.startswith("# RULE:"):
        errors.append(f"Missing rule header. Got: {first_line[:50]}")
    else:
        match = RULE_HEADER_PATTERN.match(first_line)
        if not match:
            errors.append(f"Invalid header format: {first_line}")
        else:
            # Validate number matches filename
            expected_num = path.stem.split("-")[0]
            actual_num = match.group(1)
            if expected_num != actual_num:
                errors.append(
                    f"Rule number mismatch: filename has {expected_num}, "
                    f"header has {actual_num}"
                )

    # Check for CRITICAL marker
    if not CRITICAL_PATTERN.search(content):
        warnings.append("No **CRITICAL** marker found (most rules have one)")

    # Check for empty content after header
    non_empty_lines = [l for l in lines[1:] if l.strip()]
    if len(non_empty_lines) < 2:
        warnings.append("Rule content seems too short")

    return ValidationResult(path, errors, warnings)


def validate_all_rules(rules_dir: Path) -> tuple[list[ValidationResult], list[str]]:
    """Validate all rules in a directory."""
    results: list[ValidationResult] = []
    global_errors: list[str] = []

    if not rules_dir.exists():
        global_errors.append(f"Rules directory not found: {rules_dir}")
        return results, global_errors

    rule_files = sorted(rules_dir.glob("*.md"))
    if not rule_files:
        global_errors.append(f"No rule files found in {rules_dir}")
        return results, global_errors

    # Validate individual files
    for rule_file in rule_files:
        result = validate_rule_file(rule_file)
        results.append(result)

    # Check for duplicate rule numbers
    seen_numbers: dict[int, Path] = {}
    for rule_file in rule_files:
        info = parse_rule_file(rule_file)
        if info:
            if info.number in seen_numbers:
                global_errors.append(
                    f"Duplicate rule number {info.number:03d}: "
                    f"{seen_numbers[info.number].name} and {rule_file.name}"
                )
            else:
                seen_numbers[info.number] = rule_file

    return results, global_errors


def main() -> int:
    """Run rule validation."""
    # Determine rules directory
    if len(sys.argv) > 1:
        rules_dir = Path(sys.argv[1])
    else:
        # Default to .claude/rules relative to script
        script_dir = Path(__file__).parent
        rules_dir = script_dir.parent / "rules"

    print(f"Validating rules in: {rules_dir}\n")

    results, global_errors = validate_all_rules(rules_dir)

    # Report results
    total_errors = len(global_errors)
    total_warnings = 0

    for result in results:
        if result.errors or result.warnings:
            print(f"📄 {result.path.name}")
            for error in result.errors:
                print(f"   ❌ {error}")
                total_errors += 1
            for warning in result.warnings:
                print(f"   ⚠️  {warning}")
                total_warnings += 1
            print()

    for error in global_errors:
        print(f"❌ {error}")

    # Summary
    print(f"\n{'=' * 50}")
    print(f"Rules checked: {len(results)}")
    print(f"Errors: {total_errors}")
    print(f"Warnings: {total_warnings}")

    if total_errors == 0:
        print("\n✅ All rules valid!")
        return 0
    else:
        print("\n❌ Validation failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
