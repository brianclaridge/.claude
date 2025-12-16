import sys
import json
import time
from .reader import process_stdin
from .loader import load_rules, filter_rules_for_reinforcement
from .formatter import format_to_hook_json
from .logger import log_directive_event, log_error, log_summary, setup_logger
from .paths import get_rules_path, get_config


def main():
    try:
        setup_logger()

        rules_path = get_rules_path()
        hook_config = get_config()

        for hook_data in process_stdin():
            event_name = hook_data.get("hook_event_name", "Unknown")
            session_id = hook_data.get("session_id", "unknown")

            start_time = time.time()

            # Load all rules from directory
            all_rules = load_rules(rules_path)

            # Filter rules based on event and reinforcement config
            rules = filter_rules_for_reinforcement(all_rules, hook_config, event_name)

            load_time_ms = (time.time() - start_time) * 1000

            if not rules:
                # No rules to inject (either none found or filtered out)
                if event_name == "UserPromptSubmit":
                    # Silent exit for UserPromptSubmit when no reinforcement configured
                    print(json.dumps({"hookSpecificOutput": {"hookEventName": event_name, "additionalContext": ""}}))
                    sys.stdout.flush()
                    continue
                else:
                    print(f"No rules found in {rules_path}", file=sys.stderr)

                log_directive_event(
                    session_id=session_id,
                    event_name=event_name,
                    directive_count=0,
                    directives=[],
                    load_time_ms=load_time_ms,
                    source_directory=rules_path
                )

            if rules:
                log_directive_event(
                    session_id=session_id,
                    event_name=event_name,
                    directive_count=len(rules),
                    directives=rules,
                    load_time_ms=load_time_ms,
                    source_directory=rules_path
                )

            output = format_to_hook_json(rules, event_name, pretty=False)

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
