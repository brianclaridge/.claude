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

    # Build context that suggests slash commands for cloud auth
    provider_commands = []
    if any(p["name"] == "aws" for p in providers):
        provider_commands.append("`/auth-aws` - AWS SSO authentication")
    if any(p["name"] == "gcp" for p in providers):
        provider_commands.append("`/auth-gcp` - GCP authentication")

    commands_list = "\n".join(f"- {cmd}" for cmd in provider_commands)

    context = f"""Cloud authentication available. Use these commands when needed:

{commands_list}"""

    return json.dumps({
        "hookSpecificOutput": {
            "hookEventName": event_name,
            "additionalContext": context
        }
    })
