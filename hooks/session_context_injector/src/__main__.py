"""Entry point for session_context_injector hook."""

import json
import sys

import structlog

from .config import load_session_config
from .prompt_builder import build_agent_prompt

structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(20),  # INFO level
)

log = structlog.get_logger()


def main() -> int:
    """Process SessionStart hook event and inject agent trigger prompt."""
    try:
        # Read hook event from stdin
        raw_input = sys.stdin.read()
        if not raw_input.strip():
            return 0

        hook_data = json.loads(raw_input)
        event_name = hook_data.get("hook_event_name", "")

        # Only process SessionStart events
        if event_name != "SessionStart":
            # Pass through for other events
            output = {"hookSpecificOutput": {"hookEventName": event_name, "additionalContext": ""}}
            print(json.dumps(output))
            return 0

        source = hook_data.get("source", "startup")
        session_id = hook_data.get("session_id", "unknown")

        log.debug("processing_session_start", source=source, session_id=session_id)

        # Load configuration
        config = load_session_config()

        # Check if auto-invoke is enabled
        if not config.get("auto_invoke_agent", True):
            log.debug("auto_invoke_disabled")
            output = {"hookSpecificOutput": {"hookEventName": event_name, "additionalContext": ""}}
            print(json.dumps(output))
            return 0

        # Build agent invocation prompt
        prompt = build_agent_prompt(source, config)

        log.debug("injecting_prompt", source=source, prompt_length=len(prompt))

        # Output hook response with additionalContext
        output = {
            "hookSpecificOutput": {
                "hookEventName": event_name,
                "additionalContext": prompt,
            }
        }

        print(json.dumps(output))
        sys.stdout.flush()

        return 0

    except json.JSONDecodeError as e:
        log.warning("invalid_json_input", error=str(e))
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": ""}}))
        return 0

    except Exception as e:
        log.error("hook_failed", error=str(e))
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": ""}}))
        return 0


if __name__ == "__main__":
    sys.exit(main())
