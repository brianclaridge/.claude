"""Entry point for changelog monitor hook."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import structlog

from .analyzer import AnalysisResult, analyze_versions, format_context_injection
from .fetcher import fetch_changelog, get_last_known_version
from .parser import get_versions_since, parse_changelog

# Configure logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.BoundLogger,
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
    cache_logger_on_first_use=True,
)

log = structlog.get_logger()


def is_enabled() -> bool:
    """Check if changelog monitor is enabled in config."""
    try:
        import yaml

        config_path = Path("/workspace/.claude/config.yml")
        if config_path.exists():
            with config_path.open() as f:
                config = yaml.safe_load(f)
            if config and "changelog_monitor" in config:
                return config["changelog_monitor"].get("enabled", True)
    except Exception:
        pass
    return True  # Enabled by default


def process_event(event: dict[str, Any]) -> dict[str, Any]:
    """Process a hook event."""
    event_name = event.get("hook_event_name", "")

    # Only process SessionStart events
    if event_name != "SessionStart":
        return {"hookSpecificOutput": {"hookEventName": event_name}}

    # Check if enabled
    if not is_enabled():
        log.debug("changelog_monitor_disabled")
        return {"hookSpecificOutput": {"hookEventName": event_name}}

    try:
        # Fetch changelog
        content = fetch_changelog()
        if not content:
            log.warning("changelog_fetch_failed")
            return {"hookSpecificOutput": {"hookEventName": event_name}}

        # Parse changelog
        versions = parse_changelog(content)
        if not versions:
            log.warning("changelog_parse_empty")
            return {"hookSpecificOutput": {"hookEventName": event_name}}

        # Get last known version
        last_version = get_last_known_version()

        # Get new versions
        new_versions = get_versions_since(versions, last_version)

        if not new_versions:
            log.debug("no_new_versions", last_known=last_version)
            return {"hookSpecificOutput": {"hookEventName": event_name}}

        # Analyze for opportunities
        result = analyze_versions(new_versions)

        # Format context injection
        context = format_context_injection(result)

        if context:
            log.info(
                "new_versions_found",
                count=len(new_versions),
                latest=new_versions[0].version if new_versions else None,
            )
            return {
                "hookSpecificOutput": {
                    "hookEventName": event_name,
                    "additionalContext": context,
                }
            }

    except Exception as e:
        log.error("changelog_monitor_error", error=str(e))

    return {"hookSpecificOutput": {"hookEventName": event_name}}


def main() -> int:
    """Main entry point."""
    try:
        # Read event from stdin
        line = sys.stdin.readline()
        if not line:
            return 0

        event = json.loads(line)
        log.debug("processing_event", event_name=event.get("hook_event_name"))

        # Process event
        response = process_event(event)

        # Output response
        print(json.dumps(response))
        sys.stdout.flush()

        return 0

    except json.JSONDecodeError as e:
        log.error("json_decode_error", error=str(e))
        print(json.dumps({"hookSpecificOutput": {}}))
        sys.stdout.flush()
        return 1

    except Exception as e:
        log.error("unexpected_error", error=str(e))
        print(json.dumps({"hookSpecificOutput": {}}))
        sys.stdout.flush()
        return 1


if __name__ == "__main__":
    sys.exit(main())
