import sys
import json
import time
from .reader import process_stdin
from .loader import load_directives
from .formatter import format_to_hook_json
from .logger import log_directive_event, log_error, log_summary, setup_logger
from .paths import get_directives_path


def main():
    try:
        setup_logger()

        directives_path = get_directives_path()

        for hook_data in process_stdin():
            event_name = hook_data.get("hook_event_name", "Unknown")
            session_id = hook_data.get("session_id", "unknown")

            start_time = time.time()

            directives = load_directives(directives_path)

            load_time_ms = (time.time() - start_time) * 1000

            if not directives:
                print(f"No directives found in {directives_path}", file=sys.stderr)
                log_directive_event(
                    session_id=session_id,
                    event_name=event_name,
                    directive_count=0,
                    directives=[],
                    load_time_ms=load_time_ms,
                    source_directory=directives_path
                )

            if directives:
                log_directive_event(
                    session_id=session_id,
                    event_name=event_name,
                    directive_count=len(directives),
                    directives=directives,
                    load_time_ms=load_time_ms,
                    source_directory=directives_path
                )

            output = format_to_hook_json(directives, event_name, pretty=False)

            log_summary(session_id=session_id, event_name=event_name, output_size=len(output), pretty=False)

            print(output)
            sys.stdout.flush()

        return 0

    except KeyboardInterrupt:
        return 0

    except Exception as e:
        log_error(str(e), session_id="unknown", event_name="Unknown")
        print(f"Fatal error: {e}", file=sys.stderr)
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "Unknown", "additionalContext": ""}}))
        return 0


if __name__ == "__main__":
    sys.exit(main())
