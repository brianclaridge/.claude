import argparse

from .formatter import format_to_hook_json
from .loader import load_rules


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Load markdown directives and output as JSON hook format"
    )

    parser.add_argument(
        "--dir",
        help="Directory containing .md directive files"
    )

    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output with indentation"
    )

    return parser.parse_args()