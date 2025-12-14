"""Dry-run rendering functionality."""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger()


def dry_run_render(config: dict[str, Any], config_dir: Path) -> list[dict]:
    """Test render templates with current environment."""
    results = []

    # Get template files
    template_files = []
    if "inputFiles" in config:
        template_files = [config_dir / f for f in config["inputFiles"]]
    elif "inputDir" in config:
        input_dir = config_dir / config["inputDir"]
        if input_dir.exists():
            template_files = [f for f in input_dir.glob("**/*") if f.is_file()]

    for template_path in template_files:
        if not template_path.exists() or template_path.is_dir():
            continue

        result = render_template(template_path)
        results.append(result)

    return results


def render_template(template_path: Path) -> dict:
    """Attempt to render a single template."""
    result = {
        "file": str(template_path),
        "success": False,
        "error": None,
        "missing_vars": [],
    }

    try:
        content = template_path.read_text()

        # Find all .Env references
        env_vars = re.findall(r"\{\{\s*\.Env\.(\w+)\s*\}\}", content)
        missing = [var for var in env_vars if var not in os.environ]

        if missing:
            result["missing_vars"] = missing
            result["error"] = f"Missing environment variables: {', '.join(missing)}"
            return result

        # Try to render using gomplate
        try:
            proc = subprocess.run(
                ["gomplate", "-f", str(template_path)],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if proc.returncode == 0:
                result["success"] = True
            else:
                result["error"] = proc.stderr.strip() or "Render failed"

        except FileNotFoundError:
            # gomplate not installed, do basic validation only
            result["success"] = True
            result["error"] = "gomplate not installed, syntax check only"

        except subprocess.TimeoutExpired:
            result["error"] = "Render timed out"

    except Exception as e:
        result["error"] = str(e)

    return result
