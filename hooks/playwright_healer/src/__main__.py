import sys
import json
from typing import Dict, Any

from .cli import parse_args, show_help
from .reader import process_stdin
from .detector import detect_browser_error, is_playwright_tool
from .healer import attempt_recovery
from .logger import setup_logger, log_healing_event, log_error


def process_hook_event(hook_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process a PostToolUse hook event and return response."""
    response = {
        "continue": True,
        "suppressOutput": False
    }

    tool_name = hook_data.get("tool_name", "")
    tool_response = hook_data.get("tool_response", [])
    session_id = hook_data.get("session_id", "unknown")

    if not is_playwright_tool(tool_name):
        return response

    error_info = detect_browser_error(tool_response)

    if error_info["detected"]:
        log_healing_event(
            session_id=session_id,
            event_type="error_detected",
            tool_name=tool_name,
            error_pattern=error_info["pattern"],
            error_message=error_info["message"]
        )

        recovery_result = attempt_recovery(session_id, tool_name, error_info)

        if recovery_result["success"]:
            log_healing_event(
                session_id=session_id,
                event_type="recovery_success",
                tool_name=tool_name,
                recovery_action=recovery_result["action"],
                message=recovery_result["message"]
            )

            response["hookSpecificOutput"] = {
                "hookEventName": "PostToolUse",
                "additionalContext": f"[PLAYWRIGHT HEALER] Browser error detected and recovered: {error_info['pattern']}. Retry the operation."
            }
        else:
            log_healing_event(
                session_id=session_id,
                event_type="recovery_failed",
                tool_name=tool_name,
                error=recovery_result.get("error", "Unknown error")
            )

    return response


def main() -> int:
    try:
        args = parse_args()

        if args.help:
            show_help()
            return 0

        setup_logger()

        for hook_data in process_stdin():
            response = process_hook_event(hook_data)
            print(json.dumps(response))
            sys.stdout.flush()

        return 0

    except KeyboardInterrupt:
        return 0

    except Exception as e:
        log_error(str(e))
        print(json.dumps({"continue": True, "suppressOutput": False}))
        return 0


if __name__ == "__main__":
    sys.exit(main())
