"""CLI entry point for session-context skill."""

import argparse
import json
import sys
from pathlib import Path

import structlog

from .config import get_git_config, get_plans_config, get_session_behavior, load_config
from .collectors import gather_git_context, gather_recent_plans, detect_pending_work

structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(20),  # INFO level
)

log = structlog.get_logger()


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Gather session context for project-analysis agent"
    )
    parser.add_argument(
        "session_type",
        nargs="?",
        default="startup",
        choices=["startup", "resume", "clear", "compact"],
        help="Session type (default: startup)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )
    parser.add_argument(
        "--repo-path",
        type=Path,
        help="Git repository path (default: cwd)",
    )
    parser.add_argument(
        "--plans-dir",
        type=Path,
        help="Plans directory path",
    )

    args = parser.parse_args()

    try:
        context = gather_context(
            session_type=args.session_type,
            repo_path=args.repo_path,
            plans_dir=args.plans_dir,
        )

        if args.json:
            print(json.dumps(context, indent=2))
        else:
            print_human_readable(context)

        return 0

    except Exception as e:
        log.error("context_gathering_failed", error=str(e))
        return 1


def gather_context(
    session_type: str,
    repo_path: Path | None = None,
    plans_dir: Path | None = None,
) -> dict:
    """Gather all session context."""
    config = load_config()
    behavior = get_session_behavior(config, session_type)
    git_config = get_git_config(config)
    plans_config = get_plans_config(config)

    git_context = gather_git_context(
        repo_path=repo_path,
        commit_limit=git_config.get("commit_history_limit", 5),
    )

    recent_plans = gather_recent_plans(
        limit=plans_config.get("recent_limit", 3),
        plans_dir=plans_dir,
    )

    pending_work = detect_pending_work(
        repo_path=repo_path,
        plans_dir=plans_dir,
    )

    return {
        "session_type": session_type,
        "behavior": behavior,
        "git": git_context,
        "recent_plans": recent_plans,
        "pending_work": pending_work,
        "config": {
            "session_behavior": behavior,
            "git_commit_limit": git_config.get("commit_history_limit", 5),
            "plans_limit": plans_config.get("recent_limit", 3),
        },
    }


def print_human_readable(context: dict) -> None:
    """Print context in human-readable format."""
    print(f"Session Context ({context['session_type']} - {context['behavior']} mode)")
    print("=" * 60)

    # Git section
    git = context.get("git", {})
    print(f"\nGit Branch: {git.get('branch', 'N/A')}")
    if git.get("last_commits"):
        print("Recent Commits:")
        for commit in git["last_commits"][:3]:
            print(f"  [{commit['hash']}] {commit['message']}")

    changes = git.get("uncommitted_changes", {})
    if any(changes.values()):
        print(f"Uncommitted: {changes.get('staged', 0)} staged, "
              f"{changes.get('unstaged', 0)} unstaged, "
              f"{changes.get('untracked', 0)} untracked")

    # Plans section
    plans = context.get("recent_plans", [])
    if plans:
        print(f"\nRecent Plans ({len(plans)}):")
        for plan in plans:
            status = " [incomplete]" if plan.get("has_incomplete_todos") else ""
            print(f"  {plan['date']} - {plan['topic']}{status}")

    # Pending work section
    pending = context.get("pending_work", {})
    if pending.get("has_pending_work"):
        print(f"\nPending Work: {pending.get('summary', 'Yes')}")
    else:
        print("\nNo pending work detected")


if __name__ == "__main__":
    sys.exit(main())
