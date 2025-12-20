import sys
import json
import traceback
from typing import Dict, Any

from .cli import parse_args, show_help
from .reader import process_stdin
from .writer import write_log_entry
from .paths import get_log_path


def log_hook_event(hook_data: Dict[str, Any]) -> None:
    session_id = hook_data.get("session_id")
    hook_event_name = hook_data.get("hook_event_name")

    if not session_id or not hook_event_name:
        return

    try:
        log_path = get_log_path(hook_event_name, session_id)
        write_log_entry(log_path, hook_data)

    except Exception as e:
        # Log to stderr so failures are visible without breaking hook protocol
        sys.stderr.write(f"[logger hook] Failed to log event: {e}\n")
        sys.stderr.flush()


def output_hook_response() -> None:
    response = {
        "continue": True,
        "suppressOutput": False
    }
    print(json.dumps(response))
    sys.stdout.flush()


def main() -> int:
    try:
        args = parse_args()

        if args.help:
            show_help()
            return 0

        for hook_data in process_stdin():
            log_hook_event(hook_data)

            output_hook_response()

        return 0

    except KeyboardInterrupt:
        return 0

    except Exception as e:
        sys.stderr.write(f"[logger hook] Unexpected error: {e}\n")
        sys.stderr.flush()
        return 0


if __name__ == "__main__":
    sys.exit(main())
