"""Entry point for submodule_auto_updater hook."""

import json
import sys
from pathlib import Path

import structlog

from .formatter import format_update_notification
from .state_manager import mark_notified, should_check, should_notify, write_check_state
from .updater import check_and_update

# Configure structlog
LOG_DIR = Path("/workspace/.claude/.data/logs/submodule_auto_updater")
LOG_DIR.mkdir(parents=True, exist_ok=True)

structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(20),
)

log = structlog.get_logger()


def main() -> int:
    """Process hook event and auto-update submodule if needed."""
    try:
        raw_input = sys.stdin.read()
        if not raw_input.strip():
            return 0

        hook_data = json.loads(raw_input)
        event_name = hook_data.get("hook_event_name", "")
        session_id = hook_data.get("session_id", "unknown")

        log.debug("hook_invoked", event_name=event_name, session_id=session_id[:8])

        # Only process UserPromptSubmit events
        if event_name != "UserPromptSubmit":
            output = {
                "hookSpecificOutput": {
                    "hookEventName": event_name,
                    "additionalContext": "",
                }
            }
            print(json.dumps(output))
            return 0

        # Check if we should run the update check
        if not should_check():
            log.debug("skipping_check", reason="interval_not_elapsed")
            output = {
                "hookSpecificOutput": {
                    "hookEventName": event_name,
                    "additionalContext": "",
                }
            }
            print(json.dumps(output))
            return 0

        # Run the check and update
        log.info("running_update_check")
        result = check_and_update()

        # Always update check state (even if no update performed)
        write_check_state(result if result.updated else None)

        # Determine notification
        additional_context = ""
        if result.updated and should_notify(session_id):
            additional_context = format_update_notification(result)
            mark_notified(session_id)
            log.info(
                "notification_injected",
                commits_pulled=result.commits_behind,
            )

        output = {
            "hookSpecificOutput": {
                "hookEventName": event_name,
                "additionalContext": additional_context,
            }
        }
        print(json.dumps(output))
        sys.stdout.flush()
        return 0

    except json.JSONDecodeError as e:
        log.warning("invalid_json_input", error=str(e))
        print(
            json.dumps(
                {
                    "hookSpecificOutput": {
                        "hookEventName": "UserPromptSubmit",
                        "additionalContext": "",
                    }
                }
            )
        )
        return 0

    except Exception as e:
        log.error("hook_failed", error=str(e), exc_info=True)
        print(
            json.dumps(
                {
                    "hookSpecificOutput": {
                        "hookEventName": "UserPromptSubmit",
                        "additionalContext": "",
                    }
                }
            )
        )
        return 0


if __name__ == "__main__":
    sys.exit(main())
