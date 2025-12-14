"""Notification message formatting."""

from .updater import UpdateResult


def format_update_notification(result: UpdateResult) -> str:
    """Format the update notification for Claude context injection."""
    commits_list = ""
    if result.commits_pulled:
        commits_list = "\n".join(f"- {commit}" for commit in result.commits_pulled[:10])
        if len(result.commits_pulled) > 10:
            commits_list += f"\n- ... and {len(result.commits_pulled) - 10} more"

    return f"""## .claude Submodule Updated

The `.claude` submodule was automatically updated from upstream.

**Previous commit:** `{result.old_commit[:8]}`
**Current commit:** `{result.new_commit[:8]}`
**Commits pulled:** {result.commits_behind}

**Changes:**
{commits_list}

**Note:** Session hooks and settings may have changed. Consider informing the user that a restart may be beneficial if significant changes were pulled."""
