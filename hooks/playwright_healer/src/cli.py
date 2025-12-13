import argparse
import sys


def parse_args():
    parser = argparse.ArgumentParser(
        description="Self-healing hook for Playwright MCP browser errors",
        add_help=False
    )

    parser.add_argument(
        "-h", "--help",
        action="store_true",
        help="Show help message and exit"
    )

    return parser.parse_args()


def show_help():
    help_text = """
Playwright Healer Hook - Self-healing for browser lock errors

Usage in settings.json:
  "PostToolUse": [
    {
      "matcher": "mcp__playwright__*",
      "hooks": [
        {
          "type": "command",
          "command": "uv run --directory /workspace/.claude/hooks/playwright_healer python -m src"
        }
      ]
    }
  ]

Configuration:
  Edit config.json to customize error patterns, recovery behavior, and logging.
"""
    print(help_text)
    sys.exit(0)
