"""CLI entry point for git-manager."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import structlog

from .identity import detect_identity
from .message import generate_message
from .auth import check_auth
from .sensitive import scan_sensitive
from .output import format_output

structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(30),  # WARNING+
)


def cmd_identity(args: argparse.Namespace) -> int:
    """Handle identity subcommand."""
    env_path = args.env_path
    result = detect_identity(
        env_path=env_path,
        check_ssh=not args.no_ssh,
        check_gh=not args.no_gh,
    )
    print(format_output(result.to_dict(), args.format))
    return result.exit_code


def cmd_message(args: argparse.Namespace) -> int:
    """Handle message subcommand."""
    result = generate_message(
        repo_path=args.repo_path,
        plans_dir=args.plans_dir,
        claude_plans_dir=args.claude_plans_dir,
    )
    print(format_output(result.to_dict(), args.format))
    return result.exit_code


def cmd_auth_check(args: argparse.Namespace) -> int:
    """Handle auth-check subcommand."""
    result = check_auth(repo_path=args.repo_path)
    print(format_output(result.to_dict(), args.format))
    return result.exit_code


def cmd_sensitive_scan(args: argparse.Namespace) -> int:
    """Handle sensitive-scan subcommand."""
    result = scan_sensitive(repo_path=args.repo_path)
    print(format_output(result.to_dict(), args.format))
    return result.exit_code


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Git workflow automation for Claude Code",
        prog="git-manager",
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # identity subcommand
    p_identity = subparsers.add_parser(
        "identity",
        help="Detect git identity from environment",
    )
    p_identity.add_argument(
        "--env-path",
        type=Path,
        help="Path to .env file",
    )
    p_identity.add_argument(
        "--no-ssh",
        action="store_true",
        help="Skip SSH detection",
    )
    p_identity.add_argument(
        "--no-gh",
        action="store_true",
        help="Skip gh CLI detection",
    )
    p_identity.set_defaults(func=cmd_identity)

    # message subcommand
    p_message = subparsers.add_parser(
        "message",
        help="Generate commit message",
    )
    p_message.add_argument(
        "--repo-path",
        type=Path,
        default=Path.cwd(),
        help="Path to git repository",
    )
    p_message.add_argument(
        "--plans-dir",
        type=Path,
        help="Path to plans/ directory",
    )
    p_message.add_argument(
        "--claude-plans-dir",
        type=Path,
        help="Path to .claude/plans/ directory",
    )
    p_message.set_defaults(func=cmd_message)

    # auth-check subcommand
    p_auth = subparsers.add_parser(
        "auth-check",
        help="Check remote authentication status",
    )
    p_auth.add_argument(
        "--repo-path",
        type=Path,
        default=Path.cwd(),
        help="Path to git repository",
    )
    p_auth.set_defaults(func=cmd_auth_check)

    # sensitive-scan subcommand
    p_sensitive = subparsers.add_parser(
        "sensitive-scan",
        help="Scan for sensitive files in staging",
    )
    p_sensitive.add_argument(
        "--repo-path",
        type=Path,
        default=Path.cwd(),
        help="Path to git repository",
    )
    p_sensitive.set_defaults(func=cmd_sensitive_scan)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
