import json
from typing import List, Dict


def format_to_hook_json(directives: List[Dict[str, str]], event_name: str = "UserPromptSubmit", pretty: bool = False) -> str:
    combined_content = "\n\n".join(
        directive["content"] for directive in directives
        if directive.get("content")
    )

    hook_output = {
        "hookSpecificOutput": {
            "hookEventName": event_name,
            "additionalContext": combined_content
        }
    }

    if pretty:
        return json.dumps(hook_output, indent=2, ensure_ascii=False)
    else:
        return json.dumps(hook_output, ensure_ascii=False)