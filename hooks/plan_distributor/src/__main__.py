"""Entry point for plan_distributor hook.

This hook triggers on PostToolUse for ExitPlanMode and distributes
plan files to appropriate project directories based on the files
being modified in the plan.
"""

import json
import os
import re
import sys
from typing import Any


from .distributor import distribute_plan, get_distribution_summary


def extract_plan_path(tool_response: list[Any]) -> str | None:
    """Extract plan file path from ExitPlanMode tool response.

    The tool_response typically contains text mentioning the plan file path.
    Example: "Your plan has been saved to: /root/.claude/plans/tender-leaping-teapot.md"

    Args:
        tool_response: List of response items from the tool

    Returns:
        Plan file path if found, None otherwise
    """
    # Pattern to match plan file paths
    plan_path_pattern = r'/[^\s]+/plans/[^\s]+\.md'

    for item in tool_response:
        if isinstance(item, dict):
            # Check 'text' field in response items
            text = item.get('text', '')
            if text:
                match = re.search(plan_path_pattern, text)
                if match:
                    return match.group(0)
        elif isinstance(item, str):
            match = re.search(plan_path_pattern, item)
            if match:
                return match.group(0)

    return None


def process_hook_event(hook_data: dict[str, Any]) -> dict[str, Any]:
    """Process a PostToolUse hook event for ExitPlanMode.

    Args:
        hook_data: Hook event data from stdin

    Returns:
        Hook response dict
    """
    response: dict[str, Any] = {
        "continue": True,
        "suppressOutput": False
    }

    tool_name = hook_data.get("tool_name", "")

    # Only process ExitPlanMode events
    if tool_name != "ExitPlanMode":
        return response

    tool_response = hook_data.get("tool_response", [])

    # Extract plan file path from response
    plan_path = extract_plan_path(tool_response)

    if not plan_path:
        # Try to find plan path in other fields
        # Sometimes it might be in a different structure
        return response

    # Get workspace root from environment or use default
    workspace_root = os.environ.get("WORKSPACE_PATH", "/workspace")

    # Distribute the plan
    result = distribute_plan(plan_path, workspace_root)

    # Add distribution summary to hook output
    if result.destinations:
        summary = get_distribution_summary(result)
        response["hookSpecificOutput"] = {
            "hookEventName": "PostToolUse",
            "additionalContext": f"[PLAN DISTRIBUTOR] {result.message}\n{summary}"
        }

    return response


def process_stdin() -> list[dict[str, Any]]:
    """Read and parse JSON from stdin.

    Returns:
        List of parsed JSON objects
    """
    data = sys.stdin.read().strip()
    if not data:
        return []

    try:
        parsed = json.loads(data)
        if isinstance(parsed, list):
            return parsed
        return [parsed]
    except json.JSONDecodeError:
        return []


def main() -> int:
    """Main entry point for the hook."""
    try:
        for hook_data in process_stdin():
            response = process_hook_event(hook_data)
            print(json.dumps(response))
            sys.stdout.flush()

        return 0

    except KeyboardInterrupt:
        return 0

    except Exception as e:
        # Log error but don't fail the hook
        print(json.dumps({
            "continue": True,
            "suppressOutput": False,
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": f"[PLAN DISTRIBUTOR] Error: {e}"
            }
        }))
        return 0


if __name__ == "__main__":
    sys.exit(main())
