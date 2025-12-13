"""Cloud auth prompt hook entry point.

Reads SessionStart hook events from stdin and outputs context
instructing Claude to invoke cloud-auth-agent for provider selection.
"""

import json
import sys
from typing import Any, Generator

import structlog

from .config_reader import get_enabled_providers
from .formatter import format_hook_output


logger = structlog.get_logger()


def read_hook_event() -> dict[str, Any] | None:
    """Read a single hook event from stdin.

    Returns:
        Parsed JSON event or None if EOF/error
    """
    try:
        line = sys.stdin.readline()
        if not line:
            return None

        line = line.strip()
        if not line:
            return None

        return json.loads(line)

    except json.JSONDecodeError:
        return None
    except Exception:
        return None


def process_stdin() -> Generator[dict[str, Any], None, None]:
    """Process hook events from stdin.

    Yields:
        Hook event dictionaries
    """
    while True:
        hook_data = read_hook_event()
        if hook_data is None:
            break
        yield hook_data


def main() -> int:
    """Main entry point."""
    try:
        for hook_data in process_stdin():
            event_name = hook_data.get("hook_event_name", "SessionStart")
            session_id = hook_data.get("session_id", "unknown")

            logger.debug(
                "processing_hook_event",
                session_id=session_id,
                event_name=event_name
            )

            # Get enabled providers from config
            providers = get_enabled_providers()

            logger.debug(
                "found_providers",
                count=len(providers),
                providers=[p["name"] for p in providers]
            )

            # Format and output hook response
            output = format_hook_output(providers, event_name)
            print(output)
            sys.stdout.flush()

        return 0

    except KeyboardInterrupt:
        return 0

    except Exception as e:
        logger.exception("fatal_error", error=str(e))
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": ""
            }
        }))
        return 0


if __name__ == "__main__":
    sys.exit(main())
