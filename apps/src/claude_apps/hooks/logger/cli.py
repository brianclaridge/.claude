import argparse
import sys
from typing import NoReturn


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Log Claude Code hook events to structured JSON files",
        add_help=False
    )

    parser.add_argument(
        "-h", "--help",
        action="store_true",
        help="Show help message and exit"
    )

    return parser.parse_args()


def show_help() -> NoReturn:
    """Display help text and exit."""
    help_text = """
  # for settings.json setup
  uv run --directory /workspace/.claude/hooks/logger python -m src
"""
    print(help_text)
    sys.exit(0)
