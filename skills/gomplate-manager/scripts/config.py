"""Parse and validate gomplate.yaml configuration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ruamel.yaml import YAML

yaml = YAML()
yaml.preserve_quotes = True


def parse_config(config_path: Path) -> tuple[dict[str, Any] | None, list[dict]]:
    """Parse gomplate.yaml and return config dict with any parse errors."""
    errors = []

    try:
        with open(config_path) as f:
            config = yaml.load(f)
        return config, errors
    except Exception as e:
        errors.append({
            "file": str(config_path),
            "line": 0,
            "rule": "config-syntax",
            "severity": "error",
            "message": f"Failed to parse YAML: {e}",
        })
        return None, errors


def validate_config(config: dict[str, Any]) -> list[dict]:
    """Validate config structure against gomplate requirements."""
    errors = []

    # Check for required fields
    has_input = "inputFiles" in config or "inputDir" in config or "in" in config
    has_output = "outputFiles" in config or "outputDir" in config or "outputMap" in config

    if not has_input:
        errors.append({
            "file": "gomplate.yaml",
            "line": 0,
            "rule": "config-structure",
            "severity": "error",
            "message": "Missing input specification (inputFiles, inputDir, or in)",
        })

    if not has_output and "in" not in config:
        errors.append({
            "file": "gomplate.yaml",
            "line": 0,
            "rule": "config-structure",
            "severity": "error",
            "message": "Missing output specification (outputFiles, outputDir, or outputMap)",
        })

    # Check inputFiles/outputFiles count match
    if "inputFiles" in config and "outputFiles" in config:
        input_count = len(config["inputFiles"])
        output_count = len(config["outputFiles"])
        if input_count != output_count:
            errors.append({
                "file": "gomplate.yaml",
                "line": 0,
                "rule": "file-count-match",
                "severity": "error",
                "message": f"inputFiles count ({input_count}) != outputFiles count ({output_count})",
            })

    return errors
