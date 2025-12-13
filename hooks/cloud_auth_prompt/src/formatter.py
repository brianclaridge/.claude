"""Format hook output for cloud auth prompt."""

import json
from typing import Any


def format_hook_output(providers: list[dict[str, Any]], event_name: str = "SessionStart") -> str:
    """Format providers into hook JSON output.

    Args:
        providers: List of enabled provider configs
        event_name: Hook event name

    Returns:
        JSON string with hookSpecificOutput
    """
    if not providers:
        # No providers configured, output empty context
        return json.dumps({
            "hookSpecificOutput": {
                "hookEventName": event_name,
                "additionalContext": ""
            }
        })

    # Build context that instructs Claude to invoke cloud-auth-agent
    provider_list = ", ".join(p["display_name"] for p in providers)

    context = f"""Cloud authentication is available for: {provider_list}

To authenticate, invoke the cloud-auth-agent with: "Prompt user to select cloud providers for authentication."

The agent will use AskUserQuestion to present provider options and invoke the appropriate login skills."""

    return json.dumps({
        "hookSpecificOutput": {
            "hookEventName": event_name,
            "additionalContext": context
        }
    })
